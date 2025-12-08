"""
Configuration settings for CXA Evals transformer.

This module loads configuration from config.json file and validates it using
the CXAEvalsTransformerConfig schema.
"""

import json
from pathlib import Path
from typing import Optional

from .config_schema import CXAEvalsTransformerConfig


def load_config(config_path: Optional[str] = None) -> CXAEvalsTransformerConfig:
    """
    Load and validate configuration from JSON file.
    
    Args:
        config_path: Path to config.json file. If None, uses default location.
        
    Returns:
        Validated CXAEvalsTransformerConfig object
        
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
            f"Please create a config.json file in the cxa_evals_transformer directory."
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
    
    try:
        config = CXAEvalsTransformerConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")
    
    return config


# Load configuration at module import
_config = load_config()

# Export config values as module-level variables
INPUT_DIR = _config.input_dir
OUTPUT_FOLDER_PREFIX = _config.output_folder_prefix
OUTPUT_FILE = _config.output_file
SCENARIO_NAME = _config.scenario_name
TASK = _config.task
GROUNDNESS_FACT = _config.groundness_fact
CXA_EVALS_DIR = _config.cxa_evals_dir
