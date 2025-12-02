# Dynamics 365 Transcript Downloader

This tool downloads conversation transcripts from Dynamics 365 Customer Service workstreams.

## Prerequisites

- Python 3.9 or higher
- Access to a Dynamics 365 Customer Service organization
- An account with permissions to read conversations and transcripts

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The default configuration is set in `transcript_downloader/config.py`. You can modify:

- `ORGANIZATION_URL`: Your Dynamics 365 organization URL
- `ORGANIZATION_ID`: Your organization ID
- `TENANT_ID`: Your Azure AD tenant ID
- `WORKSTREAM_ID`: The workstream ID to fetch conversations from
- `OUTPUT_FOLDER`: Where to save the transcript files
- `DAYS_TO_FETCH`: Number of days to look back for conversations

## Usage

### Basic Usage

Run the script with default configuration:

```bash
python download_transcripts.py
```

### Command Line Options

```bash
python download_transcripts.py --help
```

Available options:
- `--days`: Number of days to look back (default: 7)
- `--output`: Output folder for transcript files (default: transcripts_output)
- `--workstream`: Workstream ID to fetch conversations from
- `--org-url`: Dynamics 365 Organization URL
- `--tenant`: Azure AD Tenant ID

### Examples

Download transcripts from the last 14 days:
```bash
python download_transcripts.py --days 14
```

Save transcripts to a custom folder:
```bash
python download_transcripts.py --output my_transcripts
```

Use a different workstream:
```bash
python download_transcripts.py --workstream <workstream-guid>
```

## Authentication

The script uses interactive browser authentication via MSAL (Microsoft Authentication Library). When you run the script:

1. A browser window will open
2. Sign in with your Microsoft account (the configured login hint will be pre-filled)
3. Grant the necessary permissions
4. The script will receive an access token and begin downloading transcripts

### Token Caching

MSAL caches tokens automatically. On subsequent runs, if a valid token exists in the cache, you may not need to authenticate again.

## Output

Transcripts are saved as JSON files in the output folder. Each file is named using the pattern:

```
transcript_{timestamp}_{conversation_id}_{title}.json
```

## Module Structure

```
transcript_downloader/
├── __init__.py          # Package initialization
├── config.py            # Configuration settings
├── auth.py              # Authentication module (MSAL)
├── dataverse_client.py  # Dataverse Web API client
└── transcript_downloader.py  # Main transcript download logic
```

## How It Works

1. **Authentication**: Uses MSAL to authenticate with Azure AD and get an access token for Dynamics 365
2. **Fetch Conversations**: Queries the `msdyn_ocliveworkitem` table for conversations in the specified workstream
3. **Fetch Transcripts**: For each conversation, queries the `msdyn_transcript` table
4. **Fetch Annotations**: Retrieves the `annotation` record containing the transcript content
5. **Decode & Save**: Decodes the base64-encoded document body and saves it as a formatted JSON file

## Troubleshooting

### Authentication Errors

- Ensure you have the correct tenant ID
- Verify your account has access to the Dynamics 365 organization
- Check that the organization URL is correct

### No Transcripts Found

- Verify the workstream ID is correct
- Ensure there are conversations with transcripts in the specified time range
- Check that transcripts exist in the system for the conversations

### Permission Errors

- Your account needs read access to:
  - `msdyn_ocliveworkitem` (Conversations)
  - `msdyn_transcript` (Transcripts)
  - `annotation` (Notes/Attachments)
