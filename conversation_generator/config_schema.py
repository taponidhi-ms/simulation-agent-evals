"""
Configuration schema for conversation generator.

This module defines the Pydantic model for validating conversation generator
configuration loaded from config.json.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional


class ConversationGeneratorConfig(BaseModel):
    """Configuration schema for conversation generator."""
    
    # Azure OpenAI Configuration (API Key mode - legacy)
    azure_openai_api_key: Optional[str] = Field(
        default=None, 
        description="Azure OpenAI API key (optional if using AAD authentication)"
    )
    azure_openai_endpoint: Optional[str] = Field(
        default=None,
        description="Azure OpenAI endpoint URL (optional if using AAD authentication)"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-01",
        description="Azure OpenAI API version"
    )
    
    # Azure AI Projects Configuration (AAD mode - recommended)
    azure_ai_project_endpoint: Optional[str] = Field(
        default=None,
        description="Azure AI Project endpoint URL for AAD authentication (e.g., https://your-resource.services.ai.azure.com/api/projects/your-project)"
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
    
    @model_validator(mode='after')
    def validate_authentication_mode(self) -> 'ConversationGeneratorConfig':
        """Validate that either API key or AAD authentication is configured."""
        has_api_key = bool(self.azure_openai_api_key and self.azure_openai_endpoint)
        has_aad = bool(self.azure_ai_project_endpoint)
        
        if not has_api_key and not has_aad:
            raise ValueError(
                'Either API key authentication (azure_openai_api_key + azure_openai_endpoint) '
                'or AAD authentication (azure_ai_project_endpoint) must be configured'
            )
        
        return self
    
    @field_validator('azure_openai_endpoint')
    @classmethod
    def validate_endpoint(cls, v: Optional[str]) -> Optional[str]:
        """Validate Azure OpenAI endpoint URL."""
        if v and not v.startswith('https://'):
            raise ValueError('Azure OpenAI endpoint must start with https://')
        return v.rstrip('/') if v else v
    
    @field_validator('azure_ai_project_endpoint')
    @classmethod
    def validate_ai_project_endpoint(cls, v: Optional[str]) -> Optional[str]:
        """Validate Azure AI Project endpoint URL."""
        if v and not v.startswith('https://'):
            raise ValueError('Azure AI Project endpoint must start with https://')
        return v
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        extra = 'forbid'
