"""
Configuration settings for conversation generator.

This module loads configuration from environment variables with CG_ prefix
(Conversation Generator).
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# Azure OpenAI Configuration
# =============================================================================

# Azure OpenAI API Configuration
AZURE_OPENAI_API_KEY = os.getenv("CG_AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("CG_AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("CG_AZURE_OPENAI_API_VERSION", "2024-02-01")

# Deployment names (model deployments in Azure)
CUSTOMER_DEPLOYMENT = os.getenv("CG_CUSTOMER_DEPLOYMENT", "gpt-4o-mini")
CSR_DEPLOYMENT = os.getenv("CG_CSR_DEPLOYMENT", "gpt-4o-mini")

# =============================================================================
# Generation Configuration
# =============================================================================

# Maximum number of turns per conversation
MAX_TURNS = int(os.getenv("CG_MAX_TURNS", "20"))

# LLM temperature (0.0 to 2.0, higher = more creative)
TEMPERATURE = float(os.getenv("CG_TEMPERATURE", "0.7"))

# Maximum tokens per response
MAX_TOKENS = int(os.getenv("CG_MAX_TOKENS", "500"))

# Number of conversations to generate
NUM_CONVERSATIONS = int(os.getenv("CG_NUM_CONVERSATIONS", "10"))

# =============================================================================
# Knowledge Base Configuration
# =============================================================================

# Path to knowledge base directory or file
KNOWLEDGE_BASE_PATH = os.getenv("CG_KNOWLEDGE_BASE_PATH", "knowledge_base/")

# =============================================================================
# Output Configuration
# =============================================================================

# Output directory for generated conversations
OUTPUT_DIR = os.getenv("CG_OUTPUT_DIR", "output/conversations/")

# =============================================================================
# Persona Configuration
# =============================================================================

# Path to persona templates file
PERSONA_TEMPLATES_PATH = os.getenv("CG_PERSONA_TEMPLATES_PATH", "conversation_generator/personas.json")
