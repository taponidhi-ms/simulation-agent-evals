# Simulation Agent Evals

This repository contains tools for evaluating the SimulationAgent feature in Dynamics 365 Customer Service.

## Tools

### 1. Transcript Downloader
Downloads conversation transcripts from Dynamics 365 Customer Service workstreams.

**[📖 View Documentation](transcript_downloader/README.md)**

**Quick Start:**
```bash
# Configure
cp .env.example .env
# Edit .env with your Dynamics 365 settings

# Run
python download_transcripts.py
```

---

### 2. Conversation Generator
Generates synthetic conversations between customer and CSR agents using LLMs for testing and evaluation.

**[📖 View Documentation](conversation_generator/README.md)**

**Quick Start:**
```bash
# Configure
cp .env.example .env
# Add your OpenAI API key to .env: CG_OPENAI_API_KEY=sk-...

# Run
python generate_conversations.py

# See example (no API key needed)
python example_usage.py
```

---

## Prerequisites

- **Python 3.9 or higher**
- **For Transcript Downloader**: Access to a Dynamics 365 Customer Service organization
- **For Conversation Generator**: OpenAI API key or Azure OpenAI access

## Installation

1. Clone this repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

All settings are configured via environment variables:
- **Transcript Downloader** uses `SA_` prefix
- **Conversation Generator** uses `CG_` prefix

Configuration can be provided via:
1. **Environment file (`.env`)**: Recommended for local development
2. **Environment variables**: Recommended for CI/CD and production

See `.env.example` for all available options.

## Project Structure

```
.
├── transcript_downloader/      # Transcript downloader module
│   ├── README.md              # Transcript downloader documentation
│   ├── __init__.py
│   ├── auth.py
│   ├── config.py
│   ├── dataverse_client.py
│   ├── models.py
│   ├── transcript_downloader.py
│   └── validators.py
│
├── conversation_generator/     # Conversation generator module
│   ├── README.md              # Conversation generator documentation
│   ├── __init__.py
│   ├── agents.py
│   ├── config.py
│   ├── knowledge_base.py
│   ├── models.py
│   ├── orchestrator.py
│   └── personas.json
│
├── knowledge_base/            # Knowledge base for CSR agent
│   └── faq.json
│
├── download_transcripts.py    # Transcript downloader script
├── generate_conversations.py  # Conversation generator script
├── example_usage.py          # Example usage (no API key needed)
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment configuration
└── README.md               # This file
```

## Documentation

- **[Transcript Downloader Documentation](transcript_downloader/README.md)** - Detailed guide for downloading transcripts from Dynamics 365
- **[Conversation Generator Documentation](conversation_generator/README.md)** - Detailed guide for generating synthetic conversations
- **[Implementation Details](IMPLEMENTATION.md)** - Technical implementation details for the conversation generator

## Usage Examples

### Transcript Downloader
```bash
# Set environment variables
export SA_ORGANIZATION_URL="https://yourorg.crm.dynamics.com"
export SA_TENANT_ID="your-tenant-id"
export SA_WORKSTREAM_ID="your-workstream-id"
export SA_MAX_CONVERSATIONS=100

# Download transcripts
python download_transcripts.py
```

### Conversation Generator
```bash
# Set environment variables
export CG_OPENAI_API_KEY="sk-your-api-key"
export CG_NUM_CONVERSATIONS=10

# Generate conversations
python generate_conversations.py
```

## Output

- **Transcript Downloader**: Saves transcripts to `output/transcripts/{timestamp}/`
- **Conversation Generator**: Saves conversations to `output/conversations/{timestamp}/`

Both tools organize output in timestamped folders for easy tracking and version control.

## Support

For detailed documentation on each tool, see:
- [Transcript Downloader Documentation](transcript_downloader/README.md)
- [Conversation Generator Documentation](conversation_generator/README.md)

For implementation details and architecture:
- [Implementation Documentation](IMPLEMENTATION.md)

## License

This project is part of Microsoft's Dynamics 365 Customer Service development.
