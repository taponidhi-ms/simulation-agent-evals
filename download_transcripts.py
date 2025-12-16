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
from conversation_generator.logger import get_logger

# Set up logger for this module
logger = get_logger(__name__)


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
    logger.info("=" * 60)
    logger.info("Dynamics 365 Transcript Downloader")
    logger.info("=" * 60)

    try:
        # Validate required configuration
        validate_required_config()

        logger.info(f"Organization URL: {config.ORGANIZATION_URL}")
        logger.info(f"Workstream ID: {config.WORKSTREAM_ID}")
        logger.info(f"Days to fetch: {config.DAYS_TO_FETCH}")
        logger.info(f"Max conversations: {config.MAX_CONVERSATIONS}")

        # Step 1: Authenticate
        logger.info("-" * 40)
        logger.info("Step 1: Authentication")
        logger.info("-" * 40)

        authenticator = DynamicsAuthenticator()
        access_token = authenticator.get_access_token()

        # Step 2: Create Dataverse client
        logger.info("-" * 40)
        logger.info("Step 2: Connecting to Dataverse")
        logger.info("-" * 40)

        client = DataverseClient(access_token=access_token)
        logger.info("Connected successfully.")

        # Step 3: Download transcripts
        logger.info("-" * 40)
        logger.info("Step 3: Downloading Transcripts")
        logger.info("-" * 40)

        downloader = TranscriptDownloader(
            client=client,
            max_conversations=int(config.MAX_CONVERSATIONS),
        )

        summary = downloader.download_all_transcripts()

        # Print summary
        logger.info("=" * 60)
        logger.info("Summary")
        logger.info("=" * 60)
        logger.info(f"Total conversations found: {summary.total_conversations}")
        logger.info(f"Transcripts found: {summary.transcripts_found}")
        logger.info(f"Transcripts downloaded: {summary.transcripts_downloaded}")
        logger.info(f"Errors: {summary.errors}")

        if summary.files:
            logger.info(f"\nFiles saved to: {downloader.output_folder}/")

        return 0

    except KeyboardInterrupt:
        logger.info("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        logger.error(f"\nError: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
