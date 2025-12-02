#!/usr/bin/env python3
"""
Dynamics 365 Transcript Downloader

This script downloads transcripts of conversations from a Dynamics 365
Customer Service workstream. It uses interactive browser authentication
to connect to the D365 organization.

Usage:
    python download_transcripts.py

Configuration:
    Edit transcript_downloader/config.py to modify:
    - Organization URL, ID, and Tenant ID
    - Workstream ID
    - Output folder
    - Number of days to fetch
"""

import argparse
import sys

from transcript_downloader import config
from transcript_downloader.auth import DynamicsAuthenticator
from transcript_downloader.dataverse_client import DataverseClient
from transcript_downloader.transcript_downloader import TranscriptDownloader


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download transcripts from Dynamics 365 Customer Service.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python download_transcripts.py
    python download_transcripts.py --days 14
    python download_transcripts.py --output my_transcripts
    python download_transcripts.py --workstream abc12345-...
        """,
    )

    parser.add_argument(
        "--days",
        type=int,
        default=config.DAYS_TO_FETCH,
        help=f"Number of days to look back for conversations (default: {config.DAYS_TO_FETCH})",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=config.OUTPUT_FOLDER,
        help=f"Output folder for transcript files (default: {config.OUTPUT_FOLDER})",
    )

    parser.add_argument(
        "--workstream",
        type=str,
        default=config.WORKSTREAM_ID,
        help="Workstream ID to fetch conversations from",
    )

    parser.add_argument(
        "--org-url",
        type=str,
        default=config.ORGANIZATION_URL,
        help="Dynamics 365 Organization URL",
    )

    parser.add_argument(
        "--tenant",
        type=str,
        default=config.TENANT_ID,
        help="Azure AD Tenant ID",
    )

    parser.add_argument(
        "--login-hint",
        type=str,
        default=config.LOGIN_HINT,
        help="Email hint for authentication login",
    )

    return parser.parse_args()


def validate_required_config(args: argparse.Namespace) -> None:
    """
    Validate that all required configuration values are set.

    Args:
        args: Parsed command line arguments.

    Raises:
        ValueError: If required configuration is missing.
    """
    missing = []

    if not args.org_url:
        missing.append("Organization URL (--org-url or D365_ORGANIZATION_URL env var)")
    if not args.tenant:
        missing.append("Tenant ID (--tenant or D365_TENANT_ID env var)")
    if not args.workstream:
        missing.append("Workstream ID (--workstream or D365_WORKSTREAM_ID env var)")

    if missing:
        raise ValueError(
            "Missing required configuration:\n  - " + "\n  - ".join(missing)
        )


def main() -> int:
    """
    Main entry point for the transcript downloader.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = parse_arguments()

    print("=" * 60)
    print("Dynamics 365 Transcript Downloader")
    print("=" * 60)
    print()

    try:
        # Validate required configuration
        validate_required_config(args)

        print(f"Organization URL: {args.org_url}")
        print(f"Workstream ID: {args.workstream}")
        print(f"Days to fetch: {args.days}")
        print(f"Output folder: {args.output}")
        print()

        # Step 1: Authenticate
        print("-" * 40)
        print("Step 1: Authentication")
        print("-" * 40)

        authenticator = DynamicsAuthenticator(
            tenant_id=args.tenant,
            organization_url=args.org_url,
            login_hint=args.login_hint,
        )
        access_token = authenticator.get_access_token()

        # Step 2: Create Dataverse client
        print()
        print("-" * 40)
        print("Step 2: Connecting to Dataverse")
        print("-" * 40)

        client = DataverseClient(
            access_token=access_token,
            organization_url=args.org_url,
        )
        print("Connected successfully.")

        # Step 3: Download transcripts
        print()
        print("-" * 40)
        print("Step 3: Downloading Transcripts")
        print("-" * 40)

        downloader = TranscriptDownloader(
            client=client,
            workstream_id=args.workstream,
            output_folder=args.output,
            days_to_fetch=args.days,
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
            print(f"\nFiles saved to: {args.output}/")

        return 0

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
