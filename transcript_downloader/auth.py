"""Authentication module for Dynamics 365 using MSAL."""

import json
import os
import time
from typing import Any

import msal

from . import config

# Token validity buffer in seconds (5 minutes)
# Tokens are considered invalid if they expire within this buffer
TOKEN_EXPIRY_BUFFER_SECONDS = 300

# Default token expiration time in seconds (1 hour)
# Used when MSAL doesn't provide an explicit expiration time
DEFAULT_TOKEN_EXPIRY_SECONDS = 3600


def _is_token_valid(token_data: dict[str, Any]) -> bool:
    """
    Check if a token is still valid (not expired).

    Args:
        token_data: Dictionary containing token data with 'expires_at' timestamp.

    Returns:
        True if token is valid, False otherwise.
    """
    if not token_data:
        return False
    
    expires_at = token_data.get("expires_at", 0)
    # Add buffer to avoid using tokens that are about to expire
    return time.time() < (expires_at - TOKEN_EXPIRY_BUFFER_SECONDS)


def _validate_token_format(token: str) -> bool:
    """
    Basic validation of token format (JWT format check).

    Args:
        token: The access token string.

    Returns:
        True if token appears to be valid format, False otherwise.
    """
    if not token or not isinstance(token, str):
        return False
    
    # JWT tokens have 3 parts separated by dots
    parts = token.split(".")
    return len(parts) == 3 and all(len(part) > 0 for part in parts)


class TokenCache:
    """File-based token cache for persisting authentication tokens."""

    def __init__(self, cache_path: str = config.TOKEN_CACHE_PATH):
        """
        Initialize the token cache.

        Args:
            cache_path: Path to the cache file.
        """
        self.cache_path = os.path.abspath(cache_path)

    def load(self) -> dict[str, Any] | None:
        """
        Load cached token data from file.

        Returns:
            Token data dictionary or None if not found or invalid.
        """
        if not os.path.exists(self.cache_path):
            return None

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validate the structure
            if not isinstance(data, dict) or "access_token" not in data:
                return None
            
            return data
        except (json.JSONDecodeError, OSError):
            return None

    def save(self, token_data: dict[str, Any]) -> None:
        """
        Save token data to cache file.

        Args:
            token_data: Dictionary containing token information.
        """
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=2)
        except OSError as e:
            print(f"Warning: Could not save token cache: {e}")

    def clear(self) -> None:
        """Remove the cache file."""
        if os.path.exists(self.cache_path):
            try:
                os.remove(self.cache_path)
            except OSError:
                pass


class DynamicsAuthenticator:
    """Handles authentication to Dynamics 365 using MSAL interactive browser flow."""

    def __init__(self):
        """
        Initialize the authenticator.

        All settings are loaded from environment variables (SA_* prefix).
        """
        self.tenant_id = config.TENANT_ID
        self.client_id = config.CLIENT_ID
        self.organization_url = config.ORGANIZATION_URL
        self.login_hint = config.LOGIN_HINT
        self.env_access_token = config.ACCESS_TOKEN
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = [f"{self.organization_url}/.default"]
        
        # Initialize token cache
        self._token_cache = TokenCache(config.TOKEN_CACHE_PATH)

        # Create public client application
        self._app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
        )

    def get_access_token(self) -> str:
        """
        Get an access token following the priority order:
        1. If env file has valid token (SA_ACCESS_TOKEN), use that
        2. If token is cached & valid, use that
        3. Use interactive authentication and cache token

        Returns:
            Access token string.

        Raises:
            RuntimeError: If authentication fails.
        """
        # Priority 1: Check for token from environment variable
        if self.env_access_token and _validate_token_format(self.env_access_token):
            print("Using access token from environment variable.")
            return self.env_access_token

        # Priority 2: Check for cached token
        cached_data = self._token_cache.load()
        if cached_data and _is_token_valid(cached_data):
            print("Using cached access token.")
            return cached_data["access_token"]

        # Priority 3a: Try to get token silently from MSAL cache
        accounts = self._app.get_accounts()
        if accounts:
            result = self._app.acquire_token_silent(
                scopes=self.scopes,
                account=accounts[0],
            )
            if result and "access_token" in result:
                print("Token acquired from MSAL cache.")
                self._cache_token_result(result)
                return result["access_token"]

        # Priority 3b: Interactive browser login
        print("Opening browser for authentication...")
        print(f"Please sign in with: {self.login_hint}")

        result = self._app.acquire_token_interactive(
            scopes=self.scopes,
            login_hint=self.login_hint,
        )

        if "access_token" in result:
            print("Authentication successful.")
            self._cache_token_result(result)
            return result["access_token"]

        # Handle errors
        error_description = result.get(
            "error_description", result.get("error", "Unknown error")
        )
        raise RuntimeError(f"Authentication failed: {error_description}")

    def _cache_token_result(self, result: dict[str, Any]) -> None:
        """
        Cache the token result from MSAL.

        Args:
            result: MSAL token acquisition result.
        """
        access_token = result.get("access_token")
        if not access_token:
            return

        # Calculate expiration time
        # MSAL provides 'expires_in' (seconds until expiration)
        expires_in = result.get("expires_in", DEFAULT_TOKEN_EXPIRY_SECONDS)
        expires_at = time.time() + expires_in

        token_data = {
            "access_token": access_token,
            "expires_at": expires_at,
            "expires_in": expires_in,
        }

        self._token_cache.save(token_data)

    def clear_cache(self) -> None:
        """Clear the token cache."""
        self._token_cache.clear()
        print("Token cache cleared.")


def get_authenticated_token() -> str:
    """
    Convenience function to get an authenticated token using default config.

    Returns:
        Access token string.
    """
    authenticator = DynamicsAuthenticator()
    return authenticator.get_access_token()
