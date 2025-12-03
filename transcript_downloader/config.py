"""Configuration settings for Dynamics 365 transcript downloader."""

import os

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This allows users to configure the tool via .env file in addition to env vars
load_dotenv()


def _get_env(name: str, default: str) -> str:
    """Get an environment variable with a default value."""
    return os.environ.get(name, default)


# Dynamics 365 Organization Settings (from environment variables)
# Set these environment variables before running:
#   SA_ORGANIZATION_URL - e.g., "https://yourorg.crm.dynamics.com"
#   SA_TENANT_ID - Your Azure AD tenant ID
#   SA_WORKSTREAM_ID - The workstream ID to fetch conversations from
ORGANIZATION_URL = _get_env("SA_ORGANIZATION_URL", "")
TENANT_ID = _get_env("SA_TENANT_ID", "")

# Workstream Settings (from environment variable)
WORKSTREAM_ID = _get_env("SA_WORKSTREAM_ID", "")

# Authentication Settings
# Using the well-known Power Platform / Dynamics 365 first-party app client ID
# This enables interactive browser login without requiring app registration
CLIENT_ID = _get_env("SA_CLIENT_ID", "51f81489-12ee-4a9e-aaae-a2591f45987d")

# User login hint (from environment variable)
LOGIN_HINT = _get_env("SA_LOGIN_HINT", "")

# API Settings
API_VERSION = "v9.2"

# Output Settings
OUTPUT_FOLDER = _get_env("SA_OUTPUT_FOLDER", "output/latest_transcripts")

# Time Range Settings (in days)
DAYS_TO_FETCH = int(_get_env("SA_DAYS_TO_FETCH", "7"))

# Maximum number of conversations to download in a single run (required, must be 1-1000)
MAX_CONVERSATIONS = _get_env("SA_MAX_CONVERSATIONS", "")

# Batch size for pagination
PAGE_SIZE = 50

# Maximum base64 content size (in bytes) - 50MB default
MAX_CONTENT_SIZE = int(_get_env("SA_MAX_CONTENT_SIZE", str(50 * 1024 * 1024)))

# Access token for direct authentication (bypasses interactive login if set and valid)
ACCESS_TOKEN = _get_env("SA_ACCESS_TOKEN", "")

# Token cache file path (for persisting authentication across runs)
TOKEN_CACHE_PATH = _get_env("SA_TOKEN_CACHE_PATH", ".token_cache.json")
