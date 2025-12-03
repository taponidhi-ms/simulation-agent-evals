# Conversation Generator Implementation Summary

## Overview
This implementation provides a comprehensive Two-LLM conversation generation framework for creating synthetic conversation datasets to evaluate the SimulationAgent feature in Dynamics 365 Customer Service.

## Architecture

### Two-LLM Framework
1. **Customer Agent**: Simulates customers with specific personas using LLM
2. **CSR Agent**: Simulates customer service representatives with knowledge base access
3. **Orchestrator**: Manages conversation flow, turn-taking, and termination

### Components

#### 1. Data Models (`conversation_generator/models.py`)
- `Message`: Individual conversation messages with role, content, timestamp
- `ConversationState`: Complete conversation state tracking
- `PersonaTemplate`: Customer persona definitions
- `GenerationConfig`: Configuration for generation parameters
- `Role` enum: CUSTOMER, CSR, SYSTEM
- `ConversationStatus` enum: ACTIVE, RESOLVED, ESCALATED, FAILED

#### 2. LLM Agents (`conversation_generator/agents.py`)
- `LLMClient`: Wrapper for Azure OpenAI API
- `CustomerAgent`: Generates customer responses based on persona
- `CSRAgent`: Generates CSR responses using knowledge base

#### 3. Knowledge Base (`conversation_generator/knowledge_base.py`)
- `KnowledgeBase`: JSON-based knowledge storage and retrieval
- Simple search and categorization
- Integration with CSR agent system prompts

#### 4. Orchestrator (`conversation_generator/orchestrator.py`)
- `ConversationOrchestrator`: Manages complete conversation lifecycle
- Termination conditions:
  - Resolution (satisfaction keywords detected)
  - Escalation (CSR transfer to supervisor)
  - Max turns reached
  - Error conditions

#### 5. Configuration (`conversation_generator/config.py`)
- Environment variable based (CG_ prefix)
- Azure OpenAI support
- Customizable generation parameters

## Built-in Content

### Personas (10 diverse customer types)
1. Frustrated Refund Seeker - Medium complexity
2. Confused First-Time User - Simple
3. Urgent Shipping Issue - Medium
4. Technical Support Needed - Complex
5. Price Match Request - Simple
6. Account Access Problem - Medium
7. Product Information Seeker - Simple
8. Warranty Claim - Medium
9. Billing Discrepancy - Complex
10. Highly Satisfied Customer - Simple

### Knowledge Base (16 FAQ items)
Categories covered:
- Returns (3 items): policies, process, defective products
- Shipping (3 items): timelines, tracking, lost packages
- Account (2 items): password reset, locked accounts
- Products (2 items): warranties, stock availability
- Billing (2 items): charges, duplicate charges
- Technical (2 items): troubleshooting, manuals
- Pricing (1 item): price matching
- General (1 item): contact support

## Usage

### Basic Usage
```bash
# Set Azure OpenAI credentials in .env file
CG_AZURE_OPENAI_API_KEY=your-key-here
CG_AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/

# Run generator
python generate_conversations.py
```

### Configuration Options
```bash
CG_AZURE_OPENAI_API_KEY=required                        # Azure OpenAI API key
CG_AZURE_OPENAI_ENDPOINT=required                       # Azure OpenAI endpoint URL
CG_AZURE_OPENAI_API_VERSION=2024-02-01                  # API version
CG_CUSTOMER_DEPLOYMENT=gpt-4o-mini                      # Deployment for customer
CG_CSR_DEPLOYMENT=gpt-4o-mini                           # Deployment for CSR
CG_MAX_TURNS=20                                         # Max conversation turns
CG_TEMPERATURE=0.7                                      # LLM temperature
CG_NUM_CONVERSATIONS=10                                 # Number to generate
```

### Output Format
Conversations are saved as JSON files in timestamped directories:
```
output/conversations/YYYYMMDD_HHMMSS/
├── {uuid-1}.json
├── {uuid-2}.json
└── _metadata.json
```

Each conversation JSON includes:
- conversation_id
- messages array (role, content, timestamp)
- status (resolved/escalated/failed)
- turn_count
- persona used
- resolution_reason
- timestamps
- metadata

## Features

### Conversation Generation
- ✅ Persona-based customer simulation
- ✅ Knowledge-grounded CSR responses
- ✅ Automatic turn-taking
- ✅ Resolution detection (satisfaction keywords)
- ✅ Escalation detection (supervisor transfer)
- ✅ Max turn limiting
- ✅ Error handling and recovery

### API Support
- ✅ Azure OpenAI API
- ✅ Configurable deployments and parameters

### Output
- ✅ Structured JSON format
- ✅ Timestamped output folders
- ✅ Generation metadata
- ✅ Full conversation history

### Quality Assurance
- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Error handling
- ✅ Input validation
- ✅ Code review completed
- ✅ Security scan (CodeQL) - No issues
- ✅ Python best practices (PEP 8)

## Extensibility

### Adding Personas
Edit `conversation_generator/personas.json`:
```json
{
  "personas": [{
    "name": "Persona Name",
    "description": "Situation details",
    "goal": "What customer wants",
    "tone": "Expected emotion/tone",
    "complexity": "simple|medium|complex"
  }]
}
```

### Extending Knowledge Base
Add to `knowledge_base/faq.json`:
```json
{
  "items": [{
    "category": "category_name",
    "question": "Question text",
    "answer": "Answer text",
    "tags": ["tag1", "tag2"]
  }]
}
```

### Advanced RAG Integration
Current implementation uses simple text-based knowledge base. For production:
1. Replace `KnowledgeBase` with vector database (e.g., Pinecone, Weaviate)
2. Add embedding generation for semantic search
3. Implement retrieval-augmented generation in CSR agent
4. Add relevance scoring and filtering

## Testing

### Example Script
`example_usage.py` demonstrates:
- Loading personas and knowledge base
- Creating conversation state
- Message structure
- JSON output format

Run without API key:
```bash
python example_usage.py
```

### Validation
Basic component validation:
```bash
python -c "from conversation_generator import *; print('All imports successful')"
```

## Files Changed/Added

### New Files
- `conversation_generator/__init__.py`
- `conversation_generator/models.py`
- `conversation_generator/config.py`
- `conversation_generator/knowledge_base.py`
- `conversation_generator/agents.py`
- `conversation_generator/orchestrator.py`
- `conversation_generator/personas.json`
- `generate_conversations.py`
- `knowledge_base/faq.json`
- `example_usage.py`
- `IMPLEMENTATION.md` (this file)

### Modified Files
- `requirements.txt` - Added openai>=1.0.0
- `.env.example` - Added CG_* configuration variables
- `README.md` - Added comprehensive generator documentation

## Security Considerations

### Addressed in Implementation
- ✅ No secrets in code
- ✅ Environment-based configuration
- ✅ Input validation (path existence, null checks)
- ✅ Error handling for API failures
- ✅ No code injection vulnerabilities
- ✅ Safe JSON handling

### Best Practices for Usage
- Store API keys in .env file (gitignored)
- Use service accounts for automation
- Implement rate limiting for production use
- Monitor API costs
- Review generated content for quality

## Future Enhancements

### Potential Improvements
1. **Advanced RAG**: Vector database integration for semantic search
2. **Multi-turn Context**: Better context management across turns
3. **Conversation Branching**: Generate multiple paths per scenario
4. **Quality Metrics**: Automatic evaluation of conversation quality
5. **Batch Processing**: Parallel conversation generation
6. **Resume Support**: Continue from partial failures
7. **Custom Evaluators**: Pluggable conversation quality assessment
8. **A/B Testing**: Compare different model configurations

## Dependencies

### Required
- Python 3.9+
- openai >= 1.0.0
- python-dotenv >= 1.0.0

### For Transcript Downloader (separate feature)
- msal >= 1.34.0
- requests >= 2.32.5

## Support

For issues or questions:
1. Check README.md for usage instructions
2. Review example_usage.py for code examples
3. Verify .env configuration matches .env.example
4. Check Azure OpenAI resource status and deployments

## Summary

This implementation provides a production-ready foundation for generating synthetic conversation datasets. The modular architecture allows for easy customization and extension while maintaining code quality and security standards.

Key achievements:
- ✅ Complete Two-LLM conversation framework
- ✅ 10 diverse customer personas
- ✅ Comprehensive knowledge base
- ✅ Flexible configuration
- ✅ Structured JSON output
- ✅ Full documentation
- ✅ Security validated
- ✅ Example code provided
