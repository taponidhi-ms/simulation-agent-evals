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
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from .agents import LLMClient
from .logger import get_logger, log_llm_interaction


# Set up logger for this module
logger = get_logger(__name__)

# Constants
MAX_PERSONAS_RESPONSE_TOKENS = 4000  # Allow for longer responses with multiple personas


def get_config_values():
    """
    Get configuration values, importing only when needed.
    
    Returns:
        tuple[str, str, str, str]: A tuple containing (api_key, endpoint, api_version, deployment)
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

LIMIT: If the user's prompt requests more than 50 personas, return an empty list: {"personas": []}

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
        logger.info("Generating personas from prompt...")
        logger.debug(f"Prompt length: {len(prompt)} characters")
        
        response = llm_client.generate(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=MAX_PERSONAS_RESPONSE_TOKENS
        )
        
        # Log the LLM interaction for transcript viewing
        prompt_text = f"SYSTEM: {SYSTEM_PROMPT}\n\nUSER: {prompt}"
        log_llm_interaction(
            logger=logger,
            agent_type="PersonaGenerator",
            prompt=prompt_text,
            response=response,
            model=model,
            temperature=temperature
        )
        
        # Try to parse the response as JSON
        try:
            personas_data = json.loads(response)
            logger.debug("Successfully parsed LLM response as JSON")
        except json.JSONDecodeError:
            logger.debug("Initial JSON parsing failed, attempting to extract from markdown")
            # If response contains markdown code blocks, try to extract JSON
            personas_data = None
            
            # Try to find and extract JSON from markdown code blocks
            for prefix in ["```json", "```"]:
                if prefix in response:
                    offset = len(prefix)
                    json_start = response.find(prefix) + offset
                    json_end = response.find("```", json_start)
                    if json_end == -1:
                        raise ValueError("Markdown code block not properly closed")
                    json_str = response[json_start:json_end].strip()
                    try:
                        personas_data = json.loads(json_str)
                        logger.debug(f"Successfully extracted JSON from {prefix} block")
                        break
                    except json.JSONDecodeError:
                        continue
            
            if personas_data is None:
                logger.error(f"LLM response is not valid JSON: {response}")
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
        
        logger.info(f"Successfully extracted {len(personas_data['personas'])} personas")
        return personas_data
        
    except Exception as e:
        logger.error(f"Failed to extract personas from prompt: {e}")
        raise RuntimeError(f"Failed to extract personas from prompt: {e}")


def save_personas(
    personas_data: Dict[str, Any],
    prompt: str
) -> Path:
    """
    Save personas to a timestamped directory.
    
    Args:
        personas_data: Dictionary containing the personas list
        prompt: Original prompt used to generate the personas
        
    Returns:
        Path to the saved personas.json file
        
    Raises:
        ValueError: If personas_data is missing required structure
    """
    # Validate input structure
    if "personas" not in personas_data:
        raise ValueError("personas_data must contain 'personas' key")
    
    if not isinstance(personas_data["personas"], list):
        raise ValueError("'personas' must be a list")
    
    # Create timestamped directory (always in conversation_generator/personas/)
    output_dir = Path(__file__).parent / "personas"
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    personas_dir = output_dir / f"personas_{timestamp}"
    personas_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving personas to: {personas_dir}")
    
    # Prepare metadata including the original prompt
    # We include both timestamp formats:
    # - generated_at: ISO 8601 format for precise sorting and parsing
    # - timestamp: Compact format matching the directory name for easy reference
    metadata = {
        "generated_at": now.isoformat(),
        "timestamp": timestamp,
        "prompt": prompt,
        "num_personas": len(personas_data.get("personas", []))
    }
    
    # Save personas.json with embedded metadata
    personas_with_metadata = {
        "personas": personas_data.get("personas", []),
        "_metadata": metadata
    }
    personas_file = personas_dir / "personas.json"
    with open(personas_file, 'w', encoding='utf-8') as f:
        json.dump(personas_with_metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Personas saved to: {personas_file}")
    
    # Also save separate _metadata.json for backward compatibility
    metadata_file = personas_dir / "_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.debug(f"Metadata saved to: {metadata_file}")
    
    return personas_file


def transform_personas_to_cxa(personas_data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    """
    Transform personas to CXA Evals format for evaluation.
    
    Args:
        personas_data: Dictionary containing personas list
        prompt: The original prompt used to generate personas
        
    Returns:
        Dictionary in CXA Evals format for single-turn evaluation
    """
    conversations = []
    
    # Create a single-turn conversation entry for persona generation evaluation
    # This follows the CXA Evals single-turn format with agent_prompt and agent_response
    # The system_prompt contains the LLM instructions, and agent_prompt uses template variables
    # that will be substituted by the CXA Evals framework
    conversation_entry = {
        "Id": "persona_generation_eval",
        "system_prompt": SYSTEM_PROMPT,
        "agent_prompt": "{system_prompt} Now generate personas with given prompt: {persona_prompt}",
        "agent_response": json.dumps(personas_data),
        "scenario_name": "PersonaGenerator",
        "persona_prompt": prompt,
        "num_personas_generated": len(personas_data.get("personas", []))
    }
    
    conversations.append(conversation_entry)
    
    return {
        "conversations": conversations
    }


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
        logger.debug("Using prompt from command line argument")
    else:
        try:
            with open(args.prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
            logger.debug(f"Loaded prompt from file: {args.prompt_file}")
        except FileNotFoundError:
            logger.error(f"Error: Prompt file not found: {args.prompt_file}")
            return 1
        except Exception as e:
            logger.error(f"Error reading prompt file: {e}")
            return 1
    
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
        logger.info("Generating personas from prompt...")
        personas_data = extract_personas_from_prompt(
            llm_client=llm_client,
            prompt=prompt,
            model=model,
            temperature=args.temperature
        )
        
        num_personas = len(personas_data.get("personas", []))
        logger.info(f"✓ Generated {num_personas} personas")
        
        # Display generated personas
        logger.info("Generated Personas:")
        logger.info("-" * 70)
        for i, persona in enumerate(personas_data["personas"], 1):
            logger.info(f"{i}. {persona['name']}")
            logger.info(f"   Goal: {persona['goal']}")
            logger.info(f"   Tone: {persona['tone']}")
            logger.info(f"   Complexity: {persona['complexity']}")
        
        # Save personas
        personas_file = save_personas(personas_data, prompt)
        
        logger.info("=" * 70)
        logger.info("Transforming Personas to CXA Evals Format")
        logger.info("=" * 70)
        
        # Transform personas to CXA evals format
        cxa_personas = transform_personas_to_cxa(personas_data, prompt)
        cxa_personas_file = personas_file.parent / "cxa_evals_personas.json"
        
        with open(cxa_personas_file, 'w', encoding='utf-8') as f:
            json.dump(cxa_personas, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ CXA Evals personas saved to: {cxa_personas_file}")
        
        # Create CXA Evals config for persona evaluation
        logger.info("Creating CXA Evals Config for Persona Evaluation")
        logger.info("-" * 70)
        
        template_config_path = Path(__file__).parent / "cxa_evals" / "cxa_evals_persona_generator_custom_config.json"
        
        if template_config_path.exists():
            with open(template_config_path, 'r', encoding='utf-8') as f:
                cxa_config = json.load(f)
            
            # Update paths in the config
            cxa_config_output_dir = personas_file.parent / "cxa-evals-output"
            cxa_config_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Make paths relative to the personas directory
            relative_source_path = cxa_personas_file.name
            relative_output_path = "./cxa-evals-output/"
            
            cxa_config["source"]["source_folder_path"] = relative_source_path
            cxa_config["sink"]["output_folder_path"] = relative_output_path
            
            # Save the updated config
            cxa_config_file = personas_file.parent / "cxa_evals_persona_generator_custom_config.json"
            with open(cxa_config_file, 'w', encoding='utf-8') as f:
                json.dump(cxa_config, f, indent=2)
            
            logger.info(f"✓ CXA Evals config saved to: {cxa_config_file}")
            logger.info(f"  - source_folder_path: {relative_source_path}")
            logger.info(f"  - output_folder_path: {relative_output_path}")
        else:
            logger.warning(f"⚠ Warning: Template config not found at {template_config_path}")
            logger.warning("  CXA Evals config file was not created.")
        
        logger.info("=" * 70)
        logger.info("Success!")
        logger.info("=" * 70)
        logger.info(f"Personas saved to: {personas_file}")
        logger.info(f"Metadata saved to: {personas_file.parent / '_metadata.json'}")
        logger.info(f"CXA Evals personas: {cxa_personas_file}")
        logger.info(f"CXA Evals config: {cxa_config_file}")
        
        return 0
        
    except Exception as e:
        logger.error("=" * 70)
        logger.error("Error!")
        logger.error("=" * 70)
        logger.error(f"{e}", exc_info=True)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
