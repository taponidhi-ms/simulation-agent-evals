# Migration Guide

## Azure OpenAI Authentication Update

### Overview
The conversation generator has been updated to use direct Azure OpenAI model access instead of Azure AI Projects. This change removes the requirement for agent creation permissions.

### What Changed?

**Before:** The code used `AIProjectClient` which required Azure AI Projects permissions and may have attempted to create or access agents.

**After:** The code now uses `AzureOpenAI` directly with AAD authentication, providing direct model access without agent-related permissions.

### Required Actions

#### 1. Update Configuration File

You need to update your `conversation_generator/config.json` file:

**Old Configuration:**
```json
{
  "azure_ai_project_endpoint": "https://your-resource.services.ai.azure.com/api/projects/your-project",
  "azure_openai_api_version": "2024-02-01",
  "customer_deployment": "gpt-4o-mini",
  "csr_deployment": "gpt-4o-mini",
  ...
}
```

**New Configuration:**
```json
{
  "azure_openai_endpoint": "https://your-resource.openai.azure.com/",
  "azure_openai_api_version": "2024-02-01",
  "customer_deployment": "gpt-4o-mini",
  "csr_deployment": "gpt-4o-mini",
  ...
}
```

**Key Changes:**
- Replace `azure_ai_project_endpoint` with `azure_openai_endpoint`
- Change the endpoint URL from AI Project format to Azure OpenAI format:
  - **Old:** `https://your-resource.services.ai.azure.com/api/projects/your-project`
  - **New:** `https://your-resource.openai.azure.com/`

#### 2. Update Dependencies

The `azure-ai-projects` package is no longer required. If you previously installed it separately, you can remove it:

```bash
pip uninstall azure-ai-projects
```

Required packages (already in `requirements.txt`):
```
openai>=2.12.0
azure-identity>=1.25.1
```

Reinstall dependencies:
```bash
pip install -r requirements.txt
```

### Authentication

Authentication remains the same - uses `DefaultAzureCredential` from `azure-identity`. For local development:

```bash
az login
```

### Benefits

1. **No agent permissions required** - Works with standard Azure OpenAI role assignments
2. **Simpler setup** - Direct access to model deployments
3. **Fewer dependencies** - Removed dependency on Azure AI Projects SDK

### Troubleshooting

#### Error: "Configuration validation failed"
Make sure you've updated your `config.json` to use `azure_openai_endpoint` instead of `azure_ai_project_endpoint`.

#### Error: "Missing required packages"
Run `pip install -r requirements.txt` to install the updated dependencies.

#### Error: "Authentication failed"
Ensure you've authenticated with Azure:
```bash
az login
```

And that your Azure account has the appropriate permissions for the Azure OpenAI resource:
- `Cognitive Services OpenAI User` or
- `Cognitive Services OpenAI Contributor`

### Questions?

If you encounter issues during migration, please open an issue on GitHub with:
- Your configuration file (remove sensitive values)
- The complete error message
- The output of `pip list | grep -E "azure|openai"`
