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

## Prerequisites

- Python 3.9 or higher
- Azure OpenAI access

## Installation

From the repository root:

```bash
pip install -r requirements.txt
```

## Configuration

All settings are configured via a `config.json` file in the `conversation_generator` directory.

### Quick Start

```bash
# Navigate to conversation_generator directory
cd conversation_generator

# Copy the example config file
cp config.json.example config.json

# Edit config.json with your Azure OpenAI credentials
# "azure_openai_api_key": "your-key-here"
# "azure_openai_endpoint": "https://your-resource.cognitiveservices.azure.com"

# Run the generator (from repository root)
cd ..
python generate_conversations.py
```

## Required Configuration

The following fields are required in `config.json`:

| Field | Description |
|-------|-------------|
| `azure_openai_api_key` | Your Azure OpenAI API key (subscription key from https://ai.azure.com/) |
| `azure_openai_endpoint` | Your Azure OpenAI endpoint URL (e.g., https://your-resource.cognitiveservices.azure.com/) |

## Optional Configuration

| Field | Default | Description |
|-------|---------|-------------|
| `azure_openai_api_version` | `2024-02-01` | Azure OpenAI API version |
| `customer_deployment` | `gpt-4o-mini` | Deployment name for customer agent |
| `csr_deployment` | `gpt-4o-mini` | Deployment name for CSR agent |
| `max_turns` | `20` | Maximum conversation turns |
| `temperature` | `0.7` | LLM temperature (0.0-2.0) |
| `max_tokens` | `500` | Maximum tokens per response |
| `num_conversations` | `10` | Number of conversations to generate |
| `knowledge_base_path` | `conversation_generator/knowledge_base/` | Path to knowledge base files |
| `output_dir` | `conversation_generator/output/` | Output directory for conversations |
| `persona_templates_path` | `conversation_generator/personas.json` | Path to persona templates file |

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

The CSR agent uses a knowledge base to answer questions. The default knowledge base (`data/knowledge_base/faq.json`) includes:
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

Add items to `data/knowledge_base/faq.json`:

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

Set these environment variables in your `.env` file:

```bash
CG_AZURE_OPENAI_API_KEY=your-azure-api-key
CG_AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
CG_AZURE_OPENAI_API_VERSION=2024-02-01
CG_CUSTOMER_DEPLOYMENT=gpt-4o-mini
CG_CSR_DEPLOYMENT=gpt-4o-mini
```

**Note:** The deployment names (`CG_CUSTOMER_DEPLOYMENT` and `CG_CSR_DEPLOYMENT`) must match the deployment names you created in your Azure OpenAI resource.

## Example

See `example_usage.py` in the repository root for a demonstration of the framework components without requiring an API key.

```bash
python example_usage.py
```

## Troubleshooting

### Azure OpenAI API Errors

- Verify your API key is correct and active
- Check your Azure OpenAI resource is properly deployed
- Ensure the deployment names match your Azure OpenAI deployments
- Verify the endpoint URL is correct (should end with `.cognitiveservices.azure.com/`)

### No Conversations Generated

- Check that persona templates loaded correctly
- Verify knowledge base is accessible
- Review error messages in console output

### Poor Quality Conversations

- Adjust temperature (lower = more consistent, higher = more creative)
- Modify persona descriptions to be more specific
- Enhance knowledge base with more detailed information
- Increase max_tokens if responses are being cut off
