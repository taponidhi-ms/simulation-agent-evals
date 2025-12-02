"""Configuration settings for Dynamics 365 transcript downloader."""

import os


def _get_required_env(name: str, description: str) -> str:
    """Get a required environment variable or raise an error with helpful message."""
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {name}\n"
            f"Description: {description}\n"
            f"Please set this variable before running the script."
        )
    return value


def _get_env(name: str, default: str) -> str:
    """Get an environment variable with a default value."""
    return os.environ.get(name, default)


# Dynamics 365 Organization Settings (from environment variables)
# Set these environment variables before running:
#   D365_ORGANIZATION_URL - e.g., "https://yourorg.crm.dynamics.com"
#   D365_TENANT_ID - Your Azure AD tenant ID
#   D365_WORKSTREAM_ID - The workstream ID to fetch conversations from
ORGANIZATION_URL = _get_env("D365_ORGANIZATION_URL", "")
ORGANIZATION_ID = _get_env("D365_ORGANIZATION_ID", "")
TENANT_ID = _get_env("D365_TENANT_ID", "")

# Workstream Settings (from environment variable)
WORKSTREAM_ID = _get_env("D365_WORKSTREAM_ID", "")

# Authentication Settings
# Using the well-known Power Platform / Dynamics 365 first-party app client ID
# This enables interactive browser login without requiring app registration
CLIENT_ID = _get_env("D365_CLIENT_ID", "51f81489-12ee-4a9e-aaae-a2591f45987d")

# User login hint (from environment variable)
LOGIN_HINT = _get_env("D365_LOGIN_HINT", "")

# API Settings
API_VERSION = "v9.2"

# Output Settings
OUTPUT_FOLDER = _get_env("D365_OUTPUT_FOLDER", "transcripts_output")

# Time Range Settings (in days)
DAYS_TO_FETCH = int(_get_env("D365_DAYS_TO_FETCH", "7"))

# Batch size for pagination
PAGE_SIZE = 50

# Maximum base64 content size (in bytes) - 50MB default
MAX_CONTENT_SIZE = int(_get_env("D365_MAX_CONTENT_SIZE", str(50 * 1024 * 1024)))
