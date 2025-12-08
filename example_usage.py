#!/usr/bin/env python3
"""
Example: Conversation Generator Usage

This example demonstrates how to use the conversation generator components
without requiring an actual Azure OpenAI API key. It shows the structure and
data flow of the system.
"""

from conversation_generator.models import (
    Message, Role, PersonaTemplate, ConversationState, 
    GenerationConfig, ConversationStatus
)
from conversation_generator.knowledge_base import KnowledgeBase
import json
from datetime import datetime, timezone


def main():
    print("=" * 70)
    print("Conversation Generator - Example Usage")
    print("=" * 70)
    print()
    
    # 1. Load and display personas
    print("-" * 50)
    print("1. Loading Persona Templates")
    print("-" * 50)
    
    with open('conversation_generator/personas.json', 'r') as f:
        personas_data = json.load(f)
    
    print(f"Loaded {len(personas_data['personas'])} personas:")
    for i, p in enumerate(personas_data['personas'][:3], 1):
        print(f"\n  {i}. {p['name']}")
        print(f"     Goal: {p['goal']}")
        print(f"     Tone: {p['tone']}")
        print(f"     Complexity: {p['complexity']}")
    print(f"\n  ... and {len(personas_data['personas']) - 3} more")
    
    # 2. Load and display knowledge base
    print()
    print("-" * 50)
    print("2. Loading Knowledge Base")
    print("-" * 50)
    
    kb = KnowledgeBase('data/knowledge_base/faq.json')
    items = kb.get_all_items()
    print(f"Loaded {len(items)} knowledge items:")
    
    # Group by category
    categories = {}
    for item in items:
        cat = item.get('category', 'General')
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in categories.items():
        print(f"  - {cat.title()}: {count} items")
    
    print("\nSample knowledge item:")
    sample = items[0]
    print(f"  Category: {sample['category']}")
    print(f"  Question: {sample['question']}")
    print(f"  Answer: {sample['answer'][:100]}...")
    
    # 3. Create a sample conversation state
    print()
    print("-" * 50)
    print("3. Sample Conversation Structure")
    print("-" * 50)
    
    # Create a persona
    persona = PersonaTemplate(
        name="Frustrated Refund Seeker",
        description="Customer who wants a refund for a defective product",
        goal="Get a full refund",
        tone="frustrated but civil",
        complexity="medium"
    )
    
    # Create conversation state
    conversation = ConversationState(
        conversation_id="example-conversation-001",
        persona=persona.name
    )
    
    # Add sample messages
    conversation.add_message(Message(
        role=Role.CUSTOMER,
        content="Hi, I bought a product last week and it's already broken. I want a refund.",
        timestamp=datetime.now(timezone.utc)
    ))
    
    conversation.add_message(Message(
        role=Role.CSR,
        content="I'm sorry to hear about the defective product. We offer full refunds for defective items. Could you provide your order number?",
        timestamp=datetime.now(timezone.utc)
    ))
    
    conversation.add_message(Message(
        role=Role.CUSTOMER,
        content="My order number is ORD-12345. How long will the refund take?",
        timestamp=datetime.now(timezone.utc)
    ))
    
    conversation.add_message(Message(
        role=Role.CSR,
        content="Thank you. Refunds are processed within 5-7 business days after we receive the returned item. I'll email you a prepaid return label shortly.",
        timestamp=datetime.now(timezone.utc)
    ))
    
    conversation.add_message(Message(
        role=Role.CUSTOMER,
        content="That works, thanks for your help!",
        timestamp=datetime.now(timezone.utc)
    ))
    
    conversation.status = ConversationStatus.RESOLVED
    conversation.resolution_reason = "Issue resolved"
    conversation.ended_at = datetime.now(timezone.utc)
    
    # Display conversation
    print(f"\nConversation ID: {conversation.conversation_id}")
    print(f"Persona: {conversation.persona}")
    print(f"Status: {conversation.status.value}")
    print(f"Turn Count: {conversation.turn_count}")
    print(f"Resolution: {conversation.resolution_reason}")
    print(f"\nMessages:")
    
    for i, msg in enumerate(conversation.messages, 1):
        role_label = msg.role.value.upper()
        print(f"\n  [{i}] {role_label}:")
        print(f"      {msg.content}")
    
    # 4. Show JSON output structure
    print()
    print("-" * 50)
    print("4. JSON Output Structure")
    print("-" * 50)
    
    conversation_dict = conversation.to_dict()
    print("\nSample output (truncated):")
    print(json.dumps({
        "conversation_id": conversation_dict["conversation_id"],
        "status": conversation_dict["status"],
        "turn_count": conversation_dict["turn_count"],
        "persona": conversation_dict["persona"],
        "messages": [
            {
                "role": msg["role"],
                "content": msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            }
            for msg in conversation_dict["messages"][:2]
        ],
        "...": "additional fields"
    }, indent=2))
    
    # 5. Show configuration
    print()
    print("-" * 50)
    print("5. Generation Configuration")
    print("-" * 50)
    
    config = GenerationConfig(
        max_turns=20,
        temperature=0.7,
        max_tokens=500,
        enable_escalation=True
    )
    
    print(f"\nDefault settings:")
    print(f"  Max Turns: {config.max_turns}")
    print(f"  Temperature: {config.temperature}")
    print(f"  Max Tokens: {config.max_tokens}")
    print(f"  Enable Escalation: {config.enable_escalation}")
    print(f"  Escalation Keywords: {', '.join(config.escalation_keywords[:3])}...")
    
    print()
    print("=" * 70)
    print("Example Complete")
    print("=" * 70)
    print()
    print("To generate actual conversations with LLMs:")
    print("1. Set CG_AZURE_OPENAI_API_KEY and CG_AZURE_OPENAI_ENDPOINT in your .env file")
    print("2. Run: python generate_conversations.py")
    print()


if __name__ == "__main__":
    main()
