# Knowledge Base

This directory contains FAQ files used by the CSR agent during conversation generation.

## Available FAQ Files

### faq.json
Generic customer support FAQ covering common topics:
- Returns and refunds
- Shipping and tracking
- Account management
- Product information
- Technical support
- Billing and payments

### blooms-faq.json
Flower delivery company FAQ (similar to 1800flowers):
- Delivery options and timing
- Flower freshness and care
- Occasions and customization
- Subscriptions and corporate orders
- International delivery
- Sympathy and special arrangements

**Note:** All pricing, policies, and specific details in these FAQ files are **example/test data only** and should be updated to reflect actual business policies when used in production scenarios.

## Using FAQ Files

To use a specific FAQ file, configure the `knowledge_base_path` in your `config.json`:

```json
{
  "knowledge_base_path": "conversation_generator/knowledge_base/blooms-faq.json"
}
```

Or to use the entire directory (loads all FAQ files):

```json
{
  "knowledge_base_path": "conversation_generator/knowledge_base/"
}
```

## Adding New FAQ Files

To add a new FAQ file:

1. Create a JSON file with the naming pattern `{company}-faq.json`
2. Follow the structure:
```json
{
  "items": [
    {
      "category": "category_name",
      "question": "Sample question?",
      "answer": "Detailed answer with specific information.",
      "tags": ["tag1", "tag2", "tag3"]
    }
  ]
}
```

3. Include realistic but clearly example data for testing purposes
4. Cover the most common customer scenarios for that business domain
