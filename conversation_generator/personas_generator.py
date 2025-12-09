#!/usr/bin/env python3
"""
Personas Generator

This script converts natural language prompts into structured persona lists
using an LLM. The generated personas are saved to a timestamped directory.

Usage:
    python -m conversation_generator.personas_generator --prompt "Your prompt here"
    python -m conversation_generator.personas_generator --prompt-file path/to/prompt.txt
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from .agents import LLMClient


def get_config_values():
    """
    Get configuration values, importing only when needed.
    
    Returns:
        Tuple of (AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, CUSTOMER_DEPLOYMENT)
    """
    from . import config
    return (
        config.AZURE_OPENAI_API_KEY,
        config.AZURE_OPENAI_ENDPOINT,
        config.AZURE_OPENAI_API_VERSION,
        config.CUSTOMER_DEPLOYMENT
    )


SYSTEM_PROMPT = """You are an expert at creating customer personas for customer service simulation scenarios.

Given a natural language description of a simulation scenario, extract and generate a structured list of customer personas.

Each persona should include:
- name: A descriptive name for the persona (e.g., "Frustrated Refund Seeker")
- description: A detailed description of the customer's situation and behavior
- goal: What the customer wants to achieve
- tone: The expected tone/emotion of the customer (e.g., "frustrated but trying to remain civil")
- complexity: The complexity level of the interaction (simple, medium, or complex)

IMPORTANT: You must respond ONLY with valid JSON in exactly this format:
{
  "personas": [
    {
      "name": "Persona Name",
      "description": "Detailed description",
      "goal": "What they want to achieve",
      "tone": "Their emotional tone",
      "complexity": "simple|medium|complex"
    }
  ]
}

Do NOT include any other text, explanations, or markdown formatting. Only output the JSON object."""


def extract_personas_from_prompt(
    llm_client: LLMClient,
    prompt: str,
    model: str,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Extract personas from a natural language prompt using LLM.
    
    Args:
        llm_client: LLM client for generation
        prompt: Natural language prompt describing the simulation scenario
        model: Model deployment name to use
        temperature: Sampling temperature
        
    Returns:
        Dictionary containing the personas list
        
    Raises:
        RuntimeError: If LLM generation fails or returns invalid JSON
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = llm_client.generate(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=4000  # Allow for longer responses with multiple personas
        )
        
        # Try to parse the response as JSON
        try:
            personas_data = json.loads(response)
        except json.JSONDecodeError:
            # If response contains markdown code blocks, try to extract JSON
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                if json_end == -1:
                    raise ValueError("Markdown code block not properly closed")
                json_str = response[json_start:json_end].strip()
                personas_data = json.loads(json_str)
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                if json_end == -1:
                    raise ValueError("Markdown code block not properly closed")
                json_str = response[json_start:json_end].strip()
                personas_data = json.loads(json_str)
            else:
                raise ValueError(f"LLM response is not valid JSON: {response}")
        
        # Validate the structure
        if "personas" not in personas_data:
            raise ValueError("Response missing 'personas' key")
        
        if not isinstance(personas_data["personas"], list):
            raise ValueError("'personas' must be a list")
        
        # Validate each persona has required fields
        required_fields = ["name", "description", "goal", "tone", "complexity"]
        for i, persona in enumerate(personas_data["personas"]):
            for field in required_fields:
                if field not in persona:
                    raise ValueError(f"Persona {i} missing required field: {field}")
        
        return personas_data
        
    except Exception as e:
        raise RuntimeError(f"Failed to extract personas from prompt: {e}")


def save_personas(
    personas_data: Dict[str, Any],
    output_dir: Path,
    prompt: str
) -> Path:
    """
    Save personas to a timestamped directory.
    
    Args:
        personas_data: Dictionary containing the personas list
        output_dir: Base output directory (conversation_generator/personas/)
        prompt: Original prompt used to generate the personas
        
    Returns:
        Path to the saved personas.json file
    """
    # Create timestamped directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    personas_dir = output_dir / f"personas_{timestamp}"
    personas_dir.mkdir(parents=True, exist_ok=True)
    
    # Save personas.json
    personas_file = personas_dir / "personas.json"
    with open(personas_file, 'w', encoding='utf-8') as f:
        json.dump(personas_data, f, indent=2, ensure_ascii=False)
    
    # Save metadata including the original prompt
    metadata = {
        "generated_at": datetime.now().isoformat(),  # ISO format timestamp
        "timestamp": timestamp,  # Human-readable timestamp for directory name
        "prompt": prompt,
        "num_personas": len(personas_data.get("personas", []))
    }
    
    metadata_file = personas_dir / "_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return personas_file


def main():
    """Main entry point for personas generator."""
    parser = argparse.ArgumentParser(
        description="Generate personas from natural language prompts using LLM"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--prompt",
        type=str,
        help="Natural language prompt describing the simulation scenario"
    )
    group.add_argument(
        "--prompt-file",
        type=str,
        help="Path to a text file containing the prompt"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="conversation_generator/personas/",
        help="Output directory for generated personas (default: conversation_generator/personas/)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="LLM temperature (0.0-2.0, default: 0.7)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model deployment name (default: from config)"
    )
    
    args = parser.parse_args()
    
    # Get configuration values
    try:
        api_key, endpoint, api_version, default_deployment = get_config_values()
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        print("Please create a config.json file in the conversation_generator directory.", file=sys.stderr)
        return 1
    
    # Get the prompt
    if args.prompt:
        prompt = args.prompt
    else:
        with open(args.prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
    
    # Validate configuration
    if not api_key:
        print("Error: Azure OpenAI API key is required.", file=sys.stderr)
        print("Set it in conversation_generator/config.json", file=sys.stderr)
        return 1
    
    if not endpoint:
        print("Error: Azure OpenAI endpoint is required.", file=sys.stderr)
        print("Set it in conversation_generator/config.json", file=sys.stderr)
        return 1
    
    model = args.model or default_deployment
    
    print("=" * 70)
    print("Personas Generator")
    print("=" * 70)
    print()
    print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print(f"Model: {model}")
    print(f"Temperature: {args.temperature}")
    print(f"Output Directory: {args.output_dir}")
    print()
    
    try:
        # Initialize LLM client
        print("Initializing Azure OpenAI client...")
        llm_client = LLMClient(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        print("✓ Client initialized")
        print()
        
        # Extract personas from prompt
        print("Generating personas from prompt...")
        personas_data = extract_personas_from_prompt(
            llm_client=llm_client,
            prompt=prompt,
            model=model,
            temperature=args.temperature
        )
        
        num_personas = len(personas_data.get("personas", []))
        print(f"✓ Generated {num_personas} personas")
        print()
        
        # Display generated personas
        print("Generated Personas:")
        print("-" * 70)
        for i, persona in enumerate(personas_data["personas"], 1):
            print(f"{i}. {persona['name']}")
            print(f"   Goal: {persona['goal']}")
            print(f"   Tone: {persona['tone']}")
            print(f"   Complexity: {persona['complexity']}")
            print()
        
        # Save personas
        output_dir = Path(args.output_dir)
        personas_file = save_personas(personas_data, output_dir, prompt)
        
        print("=" * 70)
        print("Success!")
        print("=" * 70)
        print(f"Personas saved to: {personas_file}")
        print(f"Metadata saved to: {personas_file.parent / '_metadata.json'}")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 70)
        print("Error!")
        print("=" * 70)
        print(f"{e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
