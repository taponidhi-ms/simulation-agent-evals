# Personas Generator

Generates structured persona lists from natural language prompts using an LLM.

## Overview

The Personas Generator converts natural language descriptions of simulation scenarios into structured JSON persona files. These personas can then be used by the Conversation Generator to create realistic customer service conversations.

## Usage

### Basic Usage

Generate personas from a prompt:

```bash
python generate_personas.py --prompt "Your natural language prompt here"
```

Generate personas from a prompt file:

```bash
python generate_personas.py --prompt-file path/to/prompt.txt
```

### Example

```bash
python generate_personas.py --prompt "Simulate 10 conversations between customers and agent. Agents belong to a company like https://www.1800flowers.com/ which sells flowers to customers. 50% customers should behave as either calm and composed and other 50% should behave as angry or disappointed. They have varying kinds of issues normally faced by customers of 1800flowers type company."
```

This will create:
- A timestamped directory: `conversation_generator/personas/personas_YYYYMMDD_HHMMSS/`
- A `personas.json` file containing the generated personas
- A `_metadata.json` file with generation metadata

## Prerequisites

1. **Configuration File**: Create `conversation_generator/config.json` from the example:
   ```bash
   cp conversation_generator/config.json.example conversation_generator/config.json
   ```

2. **Azure OpenAI Credentials**: Edit `config.json` and add:
   - `azure_openai_api_key`: Your Azure OpenAI API key
   - `azure_openai_endpoint`: Your Azure OpenAI endpoint URL

## Command Line Options

| Option | Description |
|--------|-------------|
| `--prompt TEXT` | Natural language prompt describing the simulation scenario |
| `--prompt-file PATH` | Path to a text file containing the prompt |
| `--output-dir PATH` | Output directory for generated personas (default: `conversation_generator/personas/`) |
| `--temperature FLOAT` | LLM temperature (0.0-2.0, default: 0.7) |
| `--model NAME` | Model deployment name (default: from config) |

## Output Format

The generated `personas.json` file has the following structure:

```json
{
  "personas": [
    {
      "name": "Persona Name",
      "description": "Detailed description of the customer's situation and behavior",
      "goal": "What the customer wants to achieve",
      "tone": "Expected tone/emotion (e.g., frustrated, polite, confused)",
      "complexity": "simple|medium|complex"
    }
  ]
}
```

## How It Works

1. **Prompt Processing**: The natural language prompt is sent to an LLM with instructions to extract customer personas
2. **Structured Generation**: The LLM generates a structured JSON response with persona details
3. **Validation**: The response is validated to ensure it has all required fields
4. **Saving**: Personas are saved to a timestamped directory with metadata

## Examples

Example personas are available in `conversation_generator/personas/examples/`:
- `personas.json` - A set of 10 diverse customer service personas
- `single_persona_for_testing.json` - A single persona for quick testing

You can use these as references when creating custom personas or as templates for the Conversation Generator.

## Integration with Conversation Generator

Once you've generated personas, you can use them with the Conversation Generator:

1. Note the path to your generated `personas.json` file
2. Update `conversation_generator/config.json`:
   ```json
   {
     "persona_templates_path": "conversation_generator/personas/personas_20241209_123456/personas.json"
   }
   ```
3. Run the conversation generator:
   ```bash
   python generate_conversations.py
   ```

## Troubleshooting

### "Configuration file not found"

Create a `config.json` file:
```bash
cd conversation_generator
cp config.json.example config.json
# Edit config.json with your Azure OpenAI credentials
```

### "Azure OpenAI API key is required"

Edit `conversation_generator/config.json` and add your Azure OpenAI credentials.

### Invalid JSON Response

If the LLM returns invalid JSON, try:
- Lowering the temperature (e.g., `--temperature 0.5`)
- Being more specific in your prompt
- Using a different model deployment

## Tips for Writing Good Prompts

1. **Be Specific**: Clearly describe the business domain and types of interactions
2. **Include Diversity**: Specify different customer types, tones, and complexity levels
3. **Mention Quantity**: State how many personas you want to generate
4. **Provide Context**: Include relevant details about the company, products, or services

Example good prompt:
```
Generate 8 customer personas for a streaming service company like Netflix. 
Include a mix of:
- New users confused about features (2 personas)
- Existing users with billing issues (2 personas)  
- Users with technical problems (2 personas)
- Happy users wanting to upgrade (2 personas)

Make half of them calm and patient, and half frustrated or urgent.
```
