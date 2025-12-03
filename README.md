# Simulation Agent Evals

This repository contains tools for evaluating the SimulationAgent feature in Dynamics 365 Customer Service.

## Tools

1. **Transcript Downloader** - Downloads conversation transcripts from Dynamics 365 Customer Service workstreams
2. **Conversation Generator** - Generates synthetic conversations between customer and CSR agents using LLMs

## Prerequisites

- Python 3.9 or higher
- For Transcript Downloader: Access to a Dynamics 365 Customer Service organization
- For Conversation Generator: OpenAI API key or Azure OpenAI access

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

All settings are configured via environment variables.
- Transcript Downloader uses `SA_` prefix
- Conversation Generator uses `CG_` prefix

Configuration can be provided in two ways:

1. **Environment file (`.env`)**: Copy `.env.example` to `.env` and fill in your values
2. **Environment variables**: Set variables directly in your shell (overrides `.env` file)

### Quick Start with .env File

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your values
nano .env
```

---

# Transcript Downloader

Downloads conversation transcripts from Dynamics 365 Customer Service workstreams.

## Usage

```bash
python download_transcripts.py
```

## Required Configuration

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

By default, transcripts are organized by timestamp in:

```
output/transcripts/{timestamp}/
```

Where `{timestamp}` is in the format `YYYYMMDD_HHMMSS` (e.g., `20231215_143022`).

Each run creates a new timestamped folder, preserving the history of all downloads automatically.

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

---

# Conversation Generator

Generates synthetic conversations between a customer agent and a CSR (Customer Service Representative) agent using LLMs. This tool creates realistic conversation datasets for testing and evaluating the SimulationAgent feature.

## Overview

The conversation generator uses a **Two-LLM Framework**:
- **Customer Agent**: Simulates a customer with a specific persona (e.g., frustrated, confused, urgent)
- **CSR Agent**: Simulates a customer service representative with access to a knowledge base
- **Orchestrator**: Manages turn-taking, tracks conversation state, and handles termination

## Usage

```bash
python generate_conversations.py
```

## Required Configuration

| Setting | Environment Variable | Description |
|---------|---------------------|-------------|
| OpenAI API Key | `CG_OPENAI_API_KEY` | Your OpenAI API key (from https://platform.openai.com) |

## Optional Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| API Base | `CG_OPENAI_API_BASE` | `https://api.openai.com/v1` | API endpoint (use Azure endpoint for Azure OpenAI) |
| API Type | `CG_OPENAI_API_TYPE` | `openai` | API type: `openai` or `azure` |
| Customer Model | `CG_CUSTOMER_MODEL` | `gpt-4` | Model for customer agent |
| CSR Model | `CG_CSR_MODEL` | `gpt-4` | Model for CSR agent |
| Max Turns | `CG_MAX_TURNS` | `20` | Maximum conversation turns |
| Temperature | `CG_TEMPERATURE` | `0.7` | LLM temperature (0.0-2.0) |
| Max Tokens | `CG_MAX_TOKENS` | `500` | Maximum tokens per response |
| Num Conversations | `CG_NUM_CONVERSATIONS` | `10` | Number of conversations to generate |
| Knowledge Base Path | `CG_KNOWLEDGE_BASE_PATH` | `knowledge_base/` | Path to knowledge base files |
| Output Directory | `CG_OUTPUT_DIR` | `output/conversations/` | Output directory for conversations |

## How It Works

1. **Initialize Agents**: Creates customer and CSR agents with LLM clients
2. **Load Knowledge**: Loads knowledge base (FAQs, policies) for CSR agent
3. **Load Personas**: Loads customer persona templates (frustrated, confused, etc.)
4. **Generate Conversations**: For each persona:
   - Customer starts with an initial message based on persona
   - CSR responds using knowledge base
   - Turns continue until resolved, escalated, or max turns reached
5. **Save Results**: Conversations saved as JSON files with metadata

## Components

### Personas

Built-in personas include:
- Frustrated Refund Seeker
- Confused First-Time User
- Urgent Shipping Issue
- Technical Support Needed
- Price Match Request
- Account Access Problem
- Product Information Seeker
- Warranty Claim
- Billing Discrepancy
- Highly Satisfied Customer

Personas are defined in `conversation_generator/personas.json` and can be customized.

### Knowledge Base

The CSR agent uses a knowledge base to answer questions. The default knowledge base (`knowledge_base/faq.json`) includes:
- Return and refund policies
- Shipping and tracking information
- Account management
- Product warranties
- Billing and payment
- Technical support

You can customize or extend the knowledge base by editing the JSON file or adding new files to the `knowledge_base/` directory.

### Conversation Termination

Conversations end when:
- **Resolved**: Customer expresses satisfaction (detected via keywords like "thank you", "perfect")
- **Escalated**: CSR transfers to supervisor (detected in CSR response)
- **Max Turns**: Conversation reaches maximum turn limit
- **Error**: An error occurs during generation

## Output Format

Each conversation is saved as a JSON file with this structure:

```json
{
  "conversation_id": "uuid",
  "messages": [
    {
      "role": "customer",
      "content": "message text",
      "timestamp": "ISO-8601 timestamp",
      "metadata": {}
    }
  ],
  "status": "resolved|escalated|failed",
  "turn_count": 10,
  "persona": "Frustrated Refund Seeker",
  "resolution_reason": "Issue resolved",
  "created_at": "ISO-8601 timestamp",
  "ended_at": "ISO-8601 timestamp",
  "metadata": {
    "persona_description": "...",
    "persona_goal": "...",
    "persona_tone": "...",
    "persona_complexity": "medium"
  }
}
```

### Output Folder Structure

Conversations are organized by timestamp:

```
output/conversations/YYYYMMDD_HHMMSS/
├── {conversation-id-1}.json
├── {conversation-id-2}.json
├── ...
└── _metadata.json
```

The `_metadata.json` file contains generation settings and summary information.

## Module Structure

```
conversation_generator/
├── __init__.py           # Package initialization
├── models.py             # Data models (Message, ConversationState, PersonaTemplate)
├── config.py             # Configuration settings
├── knowledge_base.py     # Knowledge base handler
├── agents.py             # Customer and CSR agent implementations
├── orchestrator.py       # Conversation orchestrator
└── personas.json         # Persona templates
```

## Customization

### Adding Custom Personas

Edit `conversation_generator/personas.json`:

```json
{
  "personas": [
    {
      "name": "Your Persona Name",
      "description": "Detailed situation description",
      "goal": "What the customer wants to achieve",
      "tone": "Expected tone/emotion",
      "complexity": "simple|medium|complex"
    }
  ]
}
```

### Extending Knowledge Base

Add items to `knowledge_base/faq.json`:

```json
{
  "items": [
    {
      "category": "category_name",
      "question": "Question or topic",
      "answer": "Answer or information",
      "tags": ["tag1", "tag2"]
    }
  ]
}
```

### Using Azure OpenAI

Set these environment variables:

```bash
export CG_OPENAI_API_TYPE=azure
export CG_OPENAI_API_BASE=https://YOUR-RESOURCE.openai.azure.com
export CG_OPENAI_API_VERSION=2024-02-01
export CG_OPENAI_API_KEY=your-azure-api-key
export CG_CUSTOMER_MODEL=your-deployment-name
export CG_CSR_MODEL=your-deployment-name
```

## Troubleshooting

### OpenAI API Errors

- Verify your API key is correct and active
- Check your API quota and rate limits
- Ensure the model names are valid for your API type

### No Conversations Generated

- Check that persona templates loaded correctly
- Verify knowledge base is accessible
- Review error messages in console output

### Poor Quality Conversations

- Adjust temperature (lower = more consistent, higher = more creative)
- Modify persona descriptions to be more specific
- Enhance knowledge base with more detailed information
- Increase max_tokens if responses are being cut off
