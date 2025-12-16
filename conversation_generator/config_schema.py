"""
Configuration schema for conversation generator.

This module defines the Pydantic model for validating conversation generator
configuration loaded from config.json.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ConversationGeneratorConfig(BaseModel):
    """Configuration schema for conversation generator."""
    
    # Azure AI Projects Configuration (AAD Authentication)
    azure_ai_project_endpoint: str = Field(
        ...,
        description="Azure AI Project endpoint URL for AAD authentication (e.g., https://your-resource.services.ai.azure.com/api/projects/your-project)"
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
    def validate_ai_project_endpoint(cls, v: str) -> str:
        """Validate Azure AI Project endpoint URL."""
        if not v.startswith('https://'):
            raise ValueError('Azure AI Project endpoint must start with https://')
        return v.rstrip('/')
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        extra = 'forbid'
