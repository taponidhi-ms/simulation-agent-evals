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

All organization-specific settings must be provided via environment variables or command-line arguments. No values are hardcoded.

### Required Configuration

The following settings are **required** and must be provided:

| Setting | Environment Variable | CLI Argument | Description |
|---------|---------------------|--------------|-------------|
| Organization URL | `D365_ORGANIZATION_URL` | `--org-url` | Your Dynamics 365 organization URL (e.g., `https://yourorg.crm.dynamics.com`) |
| Tenant ID | `D365_TENANT_ID` | `--tenant` | Your Azure AD tenant ID (GUID format) |
| Workstream ID | `D365_WORKSTREAM_ID` | `--workstream` | The workstream ID to fetch conversations from (GUID format) |

### Optional Configuration

| Setting | Environment Variable | CLI Argument | Default |
|---------|---------------------|--------------|---------|
| Login Hint | `D365_LOGIN_HINT` | `--login-hint` | (none) |
| Output Folder | `D365_OUTPUT_FOLDER` | `--output` | `transcripts_output` |
| Days to Fetch | `D365_DAYS_TO_FETCH` | `--days` | `7` |
| Client ID | `D365_CLIENT_ID` | - | Power Platform first-party app |
| Max Content Size | `D365_MAX_CONTENT_SIZE` | - | 52428800 (50MB) |

### Example Usage

Using environment variables:
```bash
export D365_ORGANIZATION_URL="https://yourorg.crm.dynamics.com"
export D365_TENANT_ID="your-tenant-id-guid"
export D365_WORKSTREAM_ID="your-workstream-id-guid"
export D365_LOGIN_HINT="user@yourdomain.com"
python download_transcripts.py
```

Using command-line arguments:
```bash
python download_transcripts.py \
    --org-url "https://yourorg.crm.dynamics.com" \
    --tenant "your-tenant-id-guid" \
    --workstream "your-workstream-id-guid" \
    --login-hint "user@yourdomain.com"
```

## Usage

### Command Line Options

```bash
python download_transcripts.py --help
```

Available options:
- `--org-url`: Dynamics 365 Organization URL (required)
- `--tenant`: Azure AD Tenant ID (required)
- `--workstream`: Workstream ID to fetch conversations from (required)
- `--login-hint`: Email hint for authentication login
- `--days`: Number of days to look back (default: 7)
- `--output`: Output folder for transcript files (default: transcripts_output)

### Examples

Download transcripts from the last 14 days:
```bash
python download_transcripts.py --days 14
```

Save transcripts to a custom folder:
```bash
python download_transcripts.py --output my_transcripts
```

## Authentication

The script uses interactive browser authentication via MSAL (Microsoft Authentication Library). When you run the script:

1. A browser window will open
2. Sign in with your Microsoft account (the configured login hint will be pre-filled if provided)
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
├── __init__.py              # Package initialization
├── config.py                # Configuration settings
├── auth.py                  # Authentication module (MSAL)
├── dataverse_client.py      # Dataverse Web API client
├── transcript_downloader.py # Main transcript download logic
└── validators.py            # Input validation utilities
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
