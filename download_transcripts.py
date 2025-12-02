#!/usr/bin/env python3
"""
Dynamics 365 Transcript Downloader

This script downloads transcripts of conversations from a Dynamics 365
Customer Service workstream. It uses interactive browser authentication
to connect to the D365 organization.

Usage:
    python download_transcripts.py

Configuration:
    Copy .env.example to .env and fill in your values.
    All settings are configured via environment variables (SA_* prefix).
"""

import sys

from transcript_downloader import config
from transcript_downloader.auth import DynamicsAuthenticator
from transcript_downloader.dataverse_client import DataverseClient
from transcript_downloader.transcript_downloader import TranscriptDownloader


def validate_required_config() -> None:
    """
    Validate that all required configuration values are set.

    Raises:
        ValueError: If required configuration is missing or invalid.
    """
    missing = []

    if not config.ORGANIZATION_URL:
        missing.append("Organization URL (SA_ORGANIZATION_URL env var)")
    if not config.TENANT_ID:
        missing.append("Tenant ID (SA_TENANT_ID env var)")
    if not config.WORKSTREAM_ID:
        missing.append("Workstream ID (SA_WORKSTREAM_ID env var)")
    if not config.MAX_CONVERSATIONS:
        missing.append("Max conversations (SA_MAX_CONVERSATIONS env var, range: 1-1000)")

    if missing:
        raise ValueError(
            "Missing required configuration:\n  - " + "\n  - ".join(missing)
        )
    
    # Validate max_conversations range
    try:
        max_conv = int(config.MAX_CONVERSATIONS)
        if max_conv < 1 or max_conv > 1000:
            raise ValueError(
                f"SA_MAX_CONVERSATIONS must be between 1 and 1000, got {max_conv}"
            )
    except (ValueError, TypeError) as e:
        if "must be between" in str(e):
            raise
        raise ValueError(
            f"SA_MAX_CONVERSATIONS must be a valid integer, got '{config.MAX_CONVERSATIONS}'"
        )


def main() -> int:
    """
    Main entry point for the transcript downloader.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("=" * 60)
    print("Dynamics 365 Transcript Downloader")
    print("=" * 60)
    print()

    try:
        # Validate required configuration
        validate_required_config()

        print(f"Organization URL: {config.ORGANIZATION_URL}")
        print(f"Workstream ID: {config.WORKSTREAM_ID}")
        print(f"Days to fetch: {config.DAYS_TO_FETCH}")
        print(f"Max conversations: {config.MAX_CONVERSATIONS}")
        print(f"Output folder: {config.OUTPUT_FOLDER}")
        print()

        # Step 1: Authenticate
        print("-" * 40)
        print("Step 1: Authentication")
        print("-" * 40)

        authenticator = DynamicsAuthenticator()
        access_token = authenticator.get_access_token()

        # Step 2: Create Dataverse client
        print()
        print("-" * 40)
        print("Step 2: Connecting to Dataverse")
        print("-" * 40)

        client = DataverseClient(access_token=access_token)
        print("Connected successfully.")

        # Step 3: Download transcripts
        print()
        print("-" * 40)
        print("Step 3: Downloading Transcripts")
        print("-" * 40)

        downloader = TranscriptDownloader(
            client=client,
            max_conversations=int(config.MAX_CONVERSATIONS),
        )

        summary = downloader.download_all_transcripts()

        # Print summary
        print()
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Total conversations found: {summary.total_conversations}")
        print(f"Transcripts found: {summary.transcripts_found}")
        print(f"Transcripts downloaded: {summary.transcripts_downloaded}")
        print(f"Errors: {summary.errors}")

        if summary.files:
            print(f"\nFiles saved to: {config.OUTPUT_FOLDER}/")

        return 0

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
