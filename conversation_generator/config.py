"""
Configuration settings for conversation generator.

This module loads configuration from config.json file and validates it using
the ConversationGeneratorConfig schema.
"""

import json
import os
from pathlib import Path
from typing import Optional

from .config_schema import ConversationGeneratorConfig


def load_config(config_path: Optional[str] = None) -> ConversationGeneratorConfig:
    """
    Load and validate configuration from JSON file.
    
    Args:
        config_path: Path to config.json file. If None, uses default location.
        
    Returns:
        Validated ConversationGeneratorConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid or missing required fields
    """
    if config_path is None:
        # Default to config.json in the same directory as this file
        config_dir = Path(__file__).parent
        config_path = config_dir / "config.json"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please create a config.json file in the conversation_generator directory."
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
    
    try:
        config = ConversationGeneratorConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")
    
    return config


# Load configuration at module import
_config = load_config()

# Export config values as module-level variables for backward compatibility
AZURE_OPENAI_ENDPOINT = _config.azure_openai_endpoint
AZURE_OPENAI_API_VERSION = _config.azure_openai_api_version
CUSTOMER_DEPLOYMENT = _config.customer_deployment
CSR_DEPLOYMENT = _config.csr_deployment
MAX_TURNS = _config.max_turns
TEMPERATURE = _config.temperature
MAX_TOKENS = _config.max_tokens
KNOWLEDGE_BASE_PATH = _config.knowledge_base_path
OUTPUT_DIR = _config.output_dir
PERSONA_TEMPLATES_PATH = _config.persona_templates_path

