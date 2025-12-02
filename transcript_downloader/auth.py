"""Authentication module for Dynamics 365 using MSAL."""

import msal

from . import config


class DynamicsAuthenticator:
    """Handles authentication to Dynamics 365 using MSAL interactive browser flow."""

    def __init__(
        self,
        tenant_id: str = config.TENANT_ID,
        client_id: str = config.CLIENT_ID,
        organization_url: str = config.ORGANIZATION_URL,
        login_hint: str = config.LOGIN_HINT,
    ):
        """
        Initialize the authenticator.

        Args:
            tenant_id: Azure AD tenant ID.
            client_id: Azure AD application client ID.
            organization_url: Dynamics 365 organization URL.
            login_hint: Optional email hint for login.
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.organization_url = organization_url
        self.login_hint = login_hint
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scopes = [f"{organization_url}/.default"]

        # Create public client application
        self._app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
        )

    def get_access_token(self) -> str:
        """
        Get an access token using interactive browser flow.

        First attempts to get a token silently from the cache.
        If that fails, initiates an interactive browser login.

        Returns:
            Access token string.

        Raises:
            RuntimeError: If authentication fails.
        """
        # Try to get token silently from cache
        accounts = self._app.get_accounts()
        if accounts:
            result = self._app.acquire_token_silent(
                scopes=self.scopes,
                account=accounts[0],
            )
            if result and "access_token" in result:
                print("Token acquired from cache.")
                return result["access_token"]

        # Interactive browser login
        print("Opening browser for authentication...")
        print(f"Please sign in with: {self.login_hint}")

        result = self._app.acquire_token_interactive(
            scopes=self.scopes,
            login_hint=self.login_hint,
        )

        if "access_token" in result:
            print("Authentication successful.")
            return result["access_token"]

        # Handle errors
        error_description = result.get(
            "error_description", result.get("error", "Unknown error")
        )
        raise RuntimeError(f"Authentication failed: {error_description}")


def get_authenticated_token() -> str:
    """
    Convenience function to get an authenticated token using default config.

    Returns:
        Access token string.
    """
    authenticator = DynamicsAuthenticator()
    return authenticator.get_access_token()
