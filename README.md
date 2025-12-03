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

All settings are configured via environment variables with the `SA_` prefix.
Configuration can be provided in two ways:

1. **Environment file (`.env`)**: Copy `.env.example` to `.env` and fill in your values
2. **Environment variables**: Set variables directly in your shell (overrides `.env` file)

### Quick Start with .env File

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your values
nano .env

# Run the script
python download_transcripts.py
```

### Required Configuration

The following settings are **required** and must be provided:

| Setting | Environment Variable | Description |
|---------|---------------------|-------------|
| Organization URL | `SA_ORGANIZATION_URL` | Your Dynamics 365 organization URL (e.g., `https://yourorg.crm.dynamics.com`) |
| Tenant ID | `SA_TENANT_ID` | Your Azure AD tenant ID (GUID format) |
| Workstream ID | `SA_WORKSTREAM_ID` | The workstream ID to fetch conversations from (GUID format) |
| Max Conversations | `SA_MAX_CONVERSATIONS` | Maximum number of conversations to download (range: 1-1000) |

### Optional Configuration

| Setting | Environment Variable | Default |
|---------|---------------------|---------|-------|
| Access Token | `SA_ACCESS_TOKEN` | (none) - bypasses interactive login |
| Login Hint | `SA_LOGIN_HINT` | (none) |
| Output Folder | `SA_OUTPUT_FOLDER` | `output/latest_transcripts` |
| Days to Fetch | `SA_DAYS_TO_FETCH` | `7` |
| Client ID | `SA_CLIENT_ID` | Power Platform first-party app |
| Max Content Size | `SA_MAX_CONTENT_SIZE` | 52428800 (50MB) |
| Token Cache Path | `SA_TOKEN_CACHE_PATH` | `.token_cache.json` |

### Example Usage

Using environment variables:
```bash
export SA_ORGANIZATION_URL="https://yourorg.crm.dynamics.com"
export SA_TENANT_ID="your-tenant-id-guid"
export SA_WORKSTREAM_ID="your-workstream-id-guid"
export SA_MAX_CONVERSATIONS=100
export SA_LOGIN_HINT="user@yourdomain.com"
python download_transcripts.py
```

## Usage

Run the script after configuring your environment:

```bash
python download_transcripts.py
```

## Authentication

The script supports multiple authentication methods with the following priority order:

1. **Environment Variable Token**: If `SA_ACCESS_TOKEN` is set and valid, it will be used directly
2. **File-based Token Cache**: If a valid cached token exists in `.token_cache.json`, it will be used
3. **Interactive Browser Authentication**: Opens a browser window for login via MSAL

### Token Caching

Tokens are automatically cached to `.token_cache.json` after successful interactive authentication. This allows subsequent runs to skip the browser login. The cache file is automatically excluded from git via `.gitignore`.

To clear the cached token, simply delete the `.token_cache.json` file or set a new `SA_ACCESS_TOKEN` environment variable.

### Direct Token Authentication

For automation scenarios or when you already have a valid access token, you can set the `SA_ACCESS_TOKEN` environment variable:

```bash
export SA_ACCESS_TOKEN="your-access-token-here"
python download_transcripts.py
```

Or add it to your `.env` file:

```
SA_ACCESS_TOKEN=your-access-token-here
```

## Output

Transcripts are saved as JSON files using the conversation ID as the filename:

```
{conversation_id}.json
```

### Output Folder Structure

- **`output/latest_transcripts/`** - Contains transcripts from the most recent run (tracked in git)
- **`output/historical_transcripts/{number}/`** - Archives from previous runs (excluded from git)

### Archiving Behavior

Before each run, any existing transcripts in `output/latest_transcripts/` are automatically archived:

1. The script finds the highest numbered folder in `output/historical_transcripts/`
2. Creates a new folder with the next sequential number
3. Copies all existing transcripts to the new historical folder
4. Clears `output/latest_transcripts/` for the new download

This ensures:
- The latest transcripts are always in `output/latest_transcripts/`
- Historical runs are preserved in numbered archives
- Git only tracks the latest transcripts, not the full history

## Module Structure

```
transcript_downloader/
├── __init__.py              # Package initialization
├── config.py                # Configuration settings
├── auth.py                  # Authentication module (MSAL)
├── dataverse_client.py      # Dataverse Web API client
├── models.py                # Data models (Conversation, Transcript, Annotation, DownloadSummary)
├── transcript_downloader.py # Main transcript download logic
└── validators.py            # Input validation utilities
```

## Data Models

The package uses typed dataclasses for better type safety and IDE support:

- **`Conversation`** - Represents a D365 live work item with id, title, created_on
- **`Transcript`** - Represents a transcript record with id, name, created_on
- **`Annotation`** - Represents an annotation with id, document_body, filename, mimetype
- **`DownloadSummary`** - Summary of download operation with counts and file list

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
