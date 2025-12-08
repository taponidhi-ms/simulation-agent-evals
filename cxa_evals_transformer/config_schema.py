"""
Configuration schema for CXA Evals transformer.

This module defines the Pydantic model for validating CXA Evals transformer
configuration loaded from config.json.
"""

from pydantic import BaseModel, Field
from typing import Optional


class CXAEvalsTransformerConfig(BaseModel):
    """Configuration schema for CXA Evals transformer."""
    
    # Input/Output paths
    input_dir: str = Field(
        ...,
        description="Directory containing conversation generator output files"
    )
    output_file: str = Field(
        ...,
        description="Output file path for transformed CXA Evals conversations"
    )
    
    # Transformation settings
    scenario_name: str = Field(
        default="customer_support",
        description="Default scenario name for conversations"
    )
    task: str = Field(
        default="Customer Support",
        description="Task description for the agent"
    )
    groundness_fact: str = Field(
        default="",
        description="Default groundness fact for conversations"
    )
    
    # CXA Evals directory
    cxa_evals_dir: str = Field(
        default="cxa_evals_transformer/cxa-evals/",
        description="Directory for CXA Evals related files"
    )
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        extra = 'forbid'
