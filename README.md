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

All organization-specific settings can be provided via:
1. **Environment file (`.env`)**: Copy `.env.example` to `.env` and fill in your values
2. **Environment variables**: Set variables directly in your shell
3. **Command-line arguments**: Pass values as CLI arguments

Configuration is loaded with `.env` file values available as environment variables, and CLI arguments take precedence over environment variables.

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

| Setting | Environment Variable | CLI Argument | Description |
|---------|---------------------|--------------|-------------|
| Organization URL | `D365_ORGANIZATION_URL` | `--org-url` | Your Dynamics 365 organization URL (e.g., `https://yourorg.crm.dynamics.com`) |
| Tenant ID | `D365_TENANT_ID` | `--tenant` | Your Azure AD tenant ID (GUID format) |
| Workstream ID | `D365_WORKSTREAM_ID` | `--workstream` | The workstream ID to fetch conversations from (GUID format) |

### Optional Configuration

| Setting | Environment Variable | CLI Argument | Default |
|---------|---------------------|--------------|---------|
| Access Token | `D365_ACCESS_TOKEN` | - | (none) - bypasses interactive login |
| Login Hint | `D365_LOGIN_HINT` | `--login-hint` | (none) |
| Output Folder | `D365_OUTPUT_FOLDER` | `--output` | `transcripts_output` |
| Days to Fetch | `D365_DAYS_TO_FETCH` | `--days` | `7` |
| Client ID | `D365_CLIENT_ID` | - | Power Platform first-party app |
| Max Content Size | `D365_MAX_CONTENT_SIZE` | - | 52428800 (50MB) |
| Token Cache Path | `D365_TOKEN_CACHE_PATH` | - | `.token_cache.json` |

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

The script supports multiple authentication methods with the following priority order:

1. **Environment Variable Token**: If `D365_ACCESS_TOKEN` is set and valid, it will be used directly
2. **File-based Token Cache**: If a valid cached token exists in `.token_cache.json`, it will be used
3. **Interactive Browser Authentication**: Opens a browser window for login via MSAL

### Token Caching

Tokens are automatically cached to `.token_cache.json` after successful interactive authentication. This allows subsequent runs to skip the browser login. The cache file is automatically excluded from git via `.gitignore`.

To clear the cached token, simply delete the `.token_cache.json` file or set a new `D365_ACCESS_TOKEN` environment variable.

### Direct Token Authentication

For automation scenarios or when you already have a valid access token, you can set the `D365_ACCESS_TOKEN` environment variable:

```bash
export D365_ACCESS_TOKEN="your-access-token-here"
python download_transcripts.py
```

Or add it to your `.env` file:

```
D365_ACCESS_TOKEN=your-access-token-here
```

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
