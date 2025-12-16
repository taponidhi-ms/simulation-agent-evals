#!/usr/bin/env python3
"""
Conversation Generator

This script generates synthetic conversations between a customer agent and
a CSR agent using LLMs. It's designed to create datasets for testing and
evaluating the SimulationAgent feature.

Usage:
    python generate_conversations.py

Configuration:
    Set environment variables with CG_ prefix or use .env file.
    See .env.example for all available options.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List

from conversation_generator import config
from conversation_generator.models import PersonaTemplate, GenerationConfig
from conversation_generator.knowledge_base import KnowledgeBase
from conversation_generator.agents import LLMClient, CustomerAgent, CSRAgent
from conversation_generator.orchestrator import ConversationOrchestrator
from conversation_generator.logger import get_logger


# Import CXA transformer functionality
from conversation_generator.cxa_evals.transformer import CXAEvalsTransformer

# Set up logger for this module
logger = get_logger(__name__)

# Constants
GENERATED_PERSONAS_PREFIX = "personas_"  # Prefix for generated personas folders


def load_personas(persona_file: str) -> List[PersonaTemplate]:
    """
    Load persona templates from JSON file.
    
    Args:
        persona_file: Path to personas JSON file
        
    Returns:
        List of PersonaTemplate objects
    """
    with open(persona_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    personas = []
    for p in data.get('personas', []):
        personas.append(PersonaTemplate(
            name=p['name'],
            description=p['description'],
            goal=p['goal'],
            tone=p['tone'],
            complexity=p.get('complexity', 'medium')
        ))
    
    return personas


def validate_config() -> None:
    """
    Validate required configuration.
    
    Raises:
        ValueError: If required configuration is missing
    """
    if not config.AZURE_OPENAI_ENDPOINT:
        raise ValueError(
            "Azure OpenAI endpoint is required for AAD authentication. "
            "Set azure_openai_endpoint in config.json"
        )


def main() -> int:
    """
    Main entry point for conversation generator.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("=" * 70)
    logger.info("Conversation Generator for SimulationAgent Evaluation")
    logger.info("=" * 70)
    
    try:
        # Validate configuration
        validate_config()
        
        # Display configuration info
        logger.info(f"Azure OpenAI Endpoint: {config.AZURE_OPENAI_ENDPOINT}")
        logger.info("Authentication: Azure Active Directory (AAD)")
        logger.info(f"Customer Deployment: {config.CUSTOMER_DEPLOYMENT}")
        logger.info(f"CSR Deployment: {config.CSR_DEPLOYMENT}")
        logger.info(f"Max Turns: {config.MAX_TURNS}")
        logger.info(f"Temperature: {config.TEMPERATURE}")
        
        # Initialize LLM client
        logger.info("-" * 50)
        logger.info("Step 1: Initializing Azure OpenAI Client")
        logger.info("-" * 50)
        
        llm_client = LLMClient(
            azure_openai_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_version=config.AZURE_OPENAI_API_VERSION
        )
        
        # Load knowledge base
        logger.info("-" * 50)
        logger.info("Step 2: Loading Knowledge Base")
        logger.info("-" * 50)
        
        knowledge_base = KnowledgeBase(config.KNOWLEDGE_BASE_PATH)
        logger.info(f"Loaded {len(knowledge_base.get_all_items())} knowledge items.")
        
        # Load personas
        logger.info("-" * 50)
        logger.info("Step 3: Loading Persona Templates")
        logger.info("-" * 50)
        
        personas = load_personas(config.PERSONA_TEMPLATES_PATH)
        logger.info(f"Loaded {len(personas)} persona templates:")
        for i, p in enumerate(personas, 1):
            logger.info(f"  {i}. {p.name} ({p.complexity})")
        
        # Create generation config
        gen_config = GenerationConfig(
            max_turns=config.MAX_TURNS,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS,
            enable_escalation=True
        )
        
        # Determine output directory
        # If personas are from a generated personas folder (e.g., personas_20251209_140611),
        # save conversations inside that folder as conversations_{timestamp}
        # Otherwise, use the default output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        persona_path = Path(config.PERSONA_TEMPLATES_PATH).resolve()
        
        # Search for a directory in the path hierarchy that starts with GENERATED_PERSONAS_PREFIX
        # This handles both direct parent and nested scenarios
        personas_folder = None
        for parent in persona_path.parents:
            if parent.name.startswith(GENERATED_PERSONAS_PREFIX):
                personas_folder = parent
                break
        
        if personas_folder:
            # Save conversations inside the generated personas folder
            output_dir = personas_folder / f"conversations_{timestamp}"
            logger.debug(f"Using generated personas folder: {personas_folder}")
        else:
            # Use default output directory (old behavior for examples folder)
            output_dir = Path(config.OUTPUT_DIR) / timestamp
            logger.debug("Using default output directory")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("-" * 50)
        logger.info("Step 4: Generating Conversations")
        logger.info("-" * 50)
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Generating 1 conversation per persona ({len(personas)} total)")
        
        # Generate conversations - one per persona
        conversations_generated = 0
        
        for persona in personas:
            logger.info(f"Generating conversation for: {persona.name}")
            
            try:
                # Create agents for this conversation
                customer_agent = CustomerAgent(
                    llm_client=llm_client,
                    persona=persona,
                    model=config.CUSTOMER_DEPLOYMENT,
                    temperature=config.TEMPERATURE,
                    max_tokens=config.MAX_TOKENS
                )
                
                csr_agent = CSRAgent(
                    llm_client=llm_client,
                    knowledge_base=knowledge_base,
                    model=config.CSR_DEPLOYMENT,
                    temperature=config.TEMPERATURE,
                    max_tokens=config.MAX_TOKENS,
                    enable_escalation=True
                )
                
                # Create orchestrator and run conversation
                orchestrator = ConversationOrchestrator(
                    customer_agent=customer_agent,
                    csr_agent=csr_agent,
                    config=gen_config
                )
                
                conversation = orchestrator.run_conversation(persona)
                
                # Save conversation
                filename = f"{conversation.conversation_id}.json"
                filepath = output_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)
                
                conversations_generated += 1
                status_symbol = "✓" if conversation.status.value != "failed" else "✗"
                logger.info(f"  {status_symbol} [{conversations_generated}/{len(personas)}] "
                      f"{conversation.status.value} - {conversation.turn_count} turns "
                      f"({filename})")
            
            except Exception as e:
                logger.error(f"  ✗ Error generating conversation: {e}", exc_info=True)
                continue
        
        # Generate summary
        logger.info("=" * 70)
        logger.info("Summary")
        logger.info("=" * 70)
        logger.info(f"Total conversations generated: {conversations_generated}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Conversations saved to: {output_dir}/")
        
        # Save generation metadata
        metadata = {
            "timestamp": timestamp,
            "total_conversations": conversations_generated,
            "configuration": {
                "max_turns": config.MAX_TURNS,
                "temperature": config.TEMPERATURE,
                "customer_deployment": config.CUSTOMER_DEPLOYMENT,
                "csr_deployment": config.CSR_DEPLOYMENT
            },
            "personas_used": [p.name for p in personas]
        }
        
        metadata_file = output_dir / "_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to: {metadata_file}")
        print()
        
        # Step 5: Transform to CXA Evals format
        logger.info("=" * 70)
        logger.info("Step 5: Transforming to CXA Evals Format")
        logger.info("=" * 70)
        
        # Create CXA transformer
        transformer = CXAEvalsTransformer(
            task="Customer Support",
            groundness_fact="Knowledge base contains FAQ for customer support."
        )
        
        # Transform conversations
        cxa_output_file = output_dir / "cxa_evals_multi_turn_conversations.json"
        num_transformed = transformer.transform_directory(
            input_dir=str(output_dir),
            output_file=str(cxa_output_file)
        )
        
        logger.info(f"✓ Transformed {num_transformed} conversations to CXA Evals format")
        logger.info(f"✓ CXA output saved to: {cxa_output_file}")
        
        # Step 6: Create CXA Evals config file
        logger.info("-" * 50)
        logger.info("Creating CXA Evals Config File")
        logger.info("-" * 50)
        
        # Load template config
        template_config_path = Path(__file__).parent / "conversation_generator" / "cxa_evals" / "cxa_evals_conversation_generator_custom_config.json"
        
        if template_config_path.exists():
            with open(template_config_path, 'r', encoding='utf-8') as f:
                cxa_config = json.load(f)
            
            # Update paths in the config
            # Use relative path from the config file location to the output file
            cxa_config_output_dir = output_dir / "cxa-evals-output"
            cxa_config_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Make paths relative to the output directory
            relative_source_path = cxa_output_file.name
            relative_output_path = "./cxa-evals-output/"
            
            cxa_config["source"]["source_folder_path"] = relative_source_path
            cxa_config["sink"]["output_folder_path"] = relative_output_path
            
            # Save the updated config
            cxa_config_file = output_dir / "cxa_evals_conversation_generator_custom_config.json"
            with open(cxa_config_file, 'w', encoding='utf-8') as f:
                json.dump(cxa_config, f, indent=2)
            
            logger.info(f"✓ CXA Evals config saved to: {cxa_config_file}")
            logger.info(f"  - source_folder_path: {relative_source_path}")
            logger.info(f"  - output_folder_path: {relative_output_path}")
        else:
            logger.warning(f"⚠ Warning: Template config not found at {template_config_path}")
            logger.warning("  CXA Evals config file was not created.")
        
        logger.info("=" * 70)
        logger.info("Complete!")
        logger.info("=" * 70)
        logger.info(f"All files saved to: {output_dir}/")
        logger.info(f"  - Conversations: {conversations_generated} JSON files")
        logger.info(f"  - CXA Evals data: cxa_evals_multi_turn_conversations.json")
        logger.info(f"  - CXA Evals config: cxa_evals_conversation_generator_custom_config.json")
        logger.info(f"  - Output directory: cxa-evals-output/")
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        logger.error(f"\nError: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
