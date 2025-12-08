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
    output_folder_prefix: str = Field(
        default="cxa_evals_output_",
        description="Prefix for timestamped output folders (e.g., 'cxa_evals_output_' creates 'cxa_evals_output_20241208_120000/')"
    )
    output_file: str = Field(
        default="sa_multi_turn_conversations.json",
        description="Output filename for transformed CXA Evals conversations (will be created in timestamped directory)"
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
