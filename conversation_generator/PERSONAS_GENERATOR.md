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
- A `personas.json` file containing the generated personas and embedded metadata
- A `_metadata.json` file with generation metadata (for backward compatibility)

## Prerequisites

1. **Configuration File**: Create `conversation_generator/config.json` from the example:
   ```bash
   cp conversation_generator/config.json.example conversation_generator/config.json
   ```

2. **Azure OpenAI Setup**:
   - Configure `azure_openai_endpoint` in `config.json`
   - Authenticate with Azure: `az login`
   
   See the [main README](README.md) for details on AAD authentication with `DefaultAzureCredential`.

## Command Line Options

| Option | Description |
|--------|-------------|
| `--prompt TEXT` | Natural language prompt describing the simulation scenario |
| `--prompt-file PATH` | Path to a text file containing the prompt |
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
  ],
  "_metadata": {
    "generated_at": "2025-12-09T14:06:11.123456",
    "timestamp": "20251209_140611",
    "prompt": "Original prompt used to generate personas",
    "num_personas": 10
  }
}
```

The `_metadata` field embedded in `personas.json` includes:
- `generated_at`: ISO 8601 timestamp for precise sorting and parsing
- `timestamp`: Compact format matching the directory name for easy reference
- `prompt`: The original natural language prompt used to generate the personas
- `num_personas`: Count of personas in the file

For backward compatibility, a separate `_metadata.json` file is also created with the same metadata.

## How It Works

1. **Prompt Processing**: The natural language prompt is sent to an LLM with instructions to extract customer personas
2. **Structured Generation**: The LLM generates a structured JSON response with persona details
3. **Validation**: The response is validated to ensure it has all required fields
4. **Saving**: Personas are saved to a timestamped directory (`conversation_generator/personas/personas_YYYYMMDD_HHMMSS/`) with metadata
5. **CXA Evals Format**: The personas are also transformed to CXA Evals format for evaluation

## Examples

There are no pre-made example personas. All personas must be generated using the `generate_personas.py` script with your own prompts tailored to your specific use case.

## CXA Evals Integration

The Personas Generator automatically creates files for evaluation with CXA Evals:

1. **`cxa_evals_personas.json`**: Contains the generated personas in CXA Evals single-turn format
   - The `agent_prompt` field contains the full system prompt used by the LLM to generate personas
   - The `agent_response` field contains the generated personas JSON
   - The `persona_prompt` field contains the user's original prompt

2. **`cxa_evals_persona_generator_custom_config.json`**: CXA Evals configuration file with custom rules for evaluating:
   - **persona_diversity**: Checks for diverse personas with varying tones, goals, and complexity levels
   - **persona_completeness**: Ensures all required fields are present
   - **persona_relevance**: Validates personas are relevant to the scenario
   - **persona_distribution**: Verifies the distribution of personas matches what was requested in the prompt (e.g., 50% calm, 50% angry)

3. **`cxa-evals-output/`**: Directory for CXA Evals evaluation results

These files enable automated quality assessment of the generated personas to ensure they meet the requirements specified in the prompt.

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
