#!/usr/bin/env python3
"""
Generate Personas

Entry point script for generating personas from natural language prompts.

Usage:
    python generate_personas.py --prompt "Your prompt here"
    python generate_personas.py --prompt-file path/to/prompt.txt
"""

import sys
from conversation_generator.personas_generator import main

if __name__ == "__main__":
    sys.exit(main())
