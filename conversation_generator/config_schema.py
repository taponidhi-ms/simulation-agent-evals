"""
Configuration schema for conversation generator.

This module defines the Pydantic model for validating conversation generator
configuration loaded from config.json.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional


class ConversationGeneratorConfig(BaseModel):
    """Configuration schema for conversation generator."""
    
    # Azure AI Projects Configuration (AAD Authentication)
    azure_ai_project_endpoint: Optional[str] = Field(
        default=None,
        description="Azure AI Project endpoint URL for AAD authentication (e.g., https://your-resource.services.ai.azure.com/api/projects/your-project)"
    )
    
    # Azure OpenAI Configuration (API Key Authentication)
    azure_openai_api_key: Optional[str] = Field(
        default=None,
        description="Azure OpenAI API key for API key-based authentication"
    )
    azure_openai_endpoint: Optional[str] = Field(
        default=None,
        description="Azure OpenAI endpoint URL for API key authentication (e.g., https://your-resource.openai.azure.com/)"
    )
    
    # API Version (kept for compatibility with OpenAI client)
    azure_openai_api_version: str = Field(
        default="2024-02-01",
        description="Azure OpenAI API version"
    )
    
    # Deployment names
    customer_deployment: str = Field(
        default="gpt-4o-mini",
        description="Deployment name for customer agent"
    )
    csr_deployment: str = Field(
        default="gpt-4o-mini",
        description="Deployment name for CSR agent"
    )
    
    # Generation Configuration
    max_turns: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of turns per conversation"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0.0 to 2.0, higher = more creative)"
    )
    max_tokens: int = Field(
        default=500,
        ge=1,
        le=4000,
        description="Maximum tokens per response"
    )
    
    # Paths
    knowledge_base_path: str = Field(
        default="conversation_generator/knowledge_base/",
        description="Path to knowledge base directory or file"
    )
    output_dir: str = Field(
        default="conversation_generator/output/",
        description="Output directory for generated conversations"
    )
    persona_templates_path: str = Field(
        default="conversation_generator/personas/personas.json",
        description="Path to persona templates file (generated using generate_personas.py)"
    )
    
    @field_validator('azure_ai_project_endpoint')
    @classmethod
    def validate_ai_project_endpoint(cls, v: Optional[str]) -> Optional[str]:
        """Validate Azure AI Project endpoint URL."""
        if v is not None:
            if not v.startswith('https://'):
                raise ValueError('Azure AI Project endpoint must start with https://')
            return v.rstrip('/')
        return v
    
    @field_validator('azure_openai_endpoint')
    @classmethod
    def validate_openai_endpoint(cls, v: Optional[str]) -> Optional[str]:
        """Validate Azure OpenAI endpoint URL."""
        if v is not None:
            if not v.startswith('https://'):
                raise ValueError('Azure OpenAI endpoint must start with https://')
            return v.rstrip('/')
        return v
    
    @model_validator(mode='after')
    def validate_authentication_config(self) -> 'ConversationGeneratorConfig':
        """Validate that exactly one authentication method is configured."""
        has_aad = self.azure_ai_project_endpoint is not None
        has_api_key = (self.azure_openai_api_key is not None and 
                       self.azure_openai_endpoint is not None)
        
        if not has_aad and not has_api_key:
            raise ValueError(
                'Either AAD authentication (azure_ai_project_endpoint) or '
                'API key authentication (azure_openai_api_key + azure_openai_endpoint) must be configured'
            )
        
        if has_aad and has_api_key:
            raise ValueError(
                'Cannot use both AAD and API key authentication. '
                'Please configure only one authentication method'
            )
        
        return self
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        extra = 'forbid'
