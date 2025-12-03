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
    if not config.OPENAI_API_KEY:
        raise ValueError(
            "OpenAI API key is required. Set CG_OPENAI_API_KEY environment variable."
        )


def main() -> int:
    """
    Main entry point for conversation generator.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("=" * 70)
    print("Conversation Generator for SimulationAgent Evaluation")
    print("=" * 70)
    print()
    
    try:
        # Validate configuration
        validate_config()
        
        print(f"API Type: {config.OPENAI_API_TYPE}")
        print(f"Customer Model: {config.CUSTOMER_MODEL}")
        print(f"CSR Model: {config.CSR_MODEL}")
        print(f"Max Turns: {config.MAX_TURNS}")
        print(f"Temperature: {config.TEMPERATURE}")
        print(f"Conversations to Generate: {config.NUM_CONVERSATIONS}")
        print()
        
        # Initialize LLM client
        print("-" * 50)
        print("Step 1: Initializing LLM Client")
        print("-" * 50)
        
        llm_client = LLMClient(
            api_key=config.OPENAI_API_KEY,
            api_base=config.OPENAI_API_BASE,
            api_type=config.OPENAI_API_TYPE,
            api_version=config.OPENAI_API_VERSION
        )
        print("LLM client initialized successfully.")
        print()
        
        # Load knowledge base
        print("-" * 50)
        print("Step 2: Loading Knowledge Base")
        print("-" * 50)
        
        knowledge_base = KnowledgeBase(config.KNOWLEDGE_BASE_PATH)
        print(f"Loaded {len(knowledge_base.get_all_items())} knowledge items.")
        print()
        
        # Load personas
        print("-" * 50)
        print("Step 3: Loading Persona Templates")
        print("-" * 50)
        
        personas = load_personas(config.PERSONA_TEMPLATES_PATH)
        print(f"Loaded {len(personas)} persona templates:")
        for i, p in enumerate(personas, 1):
            print(f"  {i}. {p.name} ({p.complexity})")
        print()
        
        # Create generation config
        gen_config = GenerationConfig(
            max_turns=config.MAX_TURNS,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS,
            enable_escalation=True
        )
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(config.OUTPUT_DIR) / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("-" * 50)
        print("Step 4: Generating Conversations")
        print("-" * 50)
        print(f"Output directory: {output_dir}")
        print()
        
        # Generate conversations
        conversations_generated = 0
        conversations_per_persona = max(1, config.NUM_CONVERSATIONS // len(personas))
        
        for persona in personas:
            print(f"Generating conversations for: {persona.name}")
            
            for i in range(conversations_per_persona):
                if conversations_generated >= config.NUM_CONVERSATIONS:
                    break
                
                try:
                    # Create agents for this conversation
                    customer_agent = CustomerAgent(
                        llm_client=llm_client,
                        persona=persona,
                        model=config.CUSTOMER_MODEL,
                        temperature=config.TEMPERATURE,
                        max_tokens=config.MAX_TOKENS
                    )
                    
                    csr_agent = CSRAgent(
                        llm_client=llm_client,
                        knowledge_base=knowledge_base,
                        model=config.CSR_MODEL,
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
                    print(f"  {status_symbol} [{conversations_generated}/{config.NUM_CONVERSATIONS}] "
                          f"{conversation.status.value} - {conversation.turn_count} turns "
                          f"({filename})")
                
                except Exception as e:
                    print(f"  ✗ Error generating conversation: {e}")
                    continue
        
        # Generate summary
        print()
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Total conversations generated: {conversations_generated}")
        print(f"Output directory: {output_dir}")
        print()
        print(f"Conversations saved to: {output_dir}/")
        
        # Save generation metadata
        metadata = {
            "timestamp": timestamp,
            "total_conversations": conversations_generated,
            "configuration": {
                "max_turns": config.MAX_TURNS,
                "temperature": config.TEMPERATURE,
                "customer_model": config.CUSTOMER_MODEL,
                "csr_model": config.CSR_MODEL
            },
            "personas_used": [p.name for p in personas]
        }
        
        metadata_file = output_dir / "_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Metadata saved to: {metadata_file}")
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
