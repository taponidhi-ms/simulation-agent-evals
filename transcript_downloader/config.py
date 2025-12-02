"""Configuration settings for Dynamics 365 transcript downloader."""

import os

# Dynamics 365 Organization Settings (from environment variables)
ORGANIZATION_URL = os.environ.get(
    "D365_ORGANIZATION_URL", "https://aurorabapenv89059.crm10.dynamics.com"
)
ORGANIZATION_ID = os.environ.get(
    "D365_ORGANIZATION_ID", "407ce31e-0a98-f011-bbc9-6045bd09e9c3"
)
TENANT_ID = os.environ.get("D365_TENANT_ID", "8f08bcba-e79b-4aec-ba55-e46e7343c5f5")

# Workstream Settings (from environment variable)
WORKSTREAM_ID = os.environ.get(
    "D365_WORKSTREAM_ID", "bf8ebd2e-9043-fdeb-311f-d2fa48afc455"
)

# Authentication Settings
# Using the well-known Power Platform / Dynamics 365 first-party app client ID
# This enables interactive browser login without requiring app registration
CLIENT_ID = os.environ.get("D365_CLIENT_ID", "51f81489-12ee-4a9e-aaae-a2591f45987d")

# User login hint (from environment variable)
LOGIN_HINT = os.environ.get(
    "D365_LOGIN_HINT", "Auroraserviceaccount1@ccaasdev.onmicrosoft.com"
)

# API Settings
API_VERSION = "v9.2"

# Output Settings
OUTPUT_FOLDER = os.environ.get("D365_OUTPUT_FOLDER", "transcripts_output")

# Time Range Settings (in days)
DAYS_TO_FETCH = int(os.environ.get("D365_DAYS_TO_FETCH", "7"))

# Batch size for pagination
PAGE_SIZE = 50

# Maximum base64 content size (in bytes) - 50MB default
MAX_CONTENT_SIZE = int(os.environ.get("D365_MAX_CONTENT_SIZE", str(50 * 1024 * 1024)))
