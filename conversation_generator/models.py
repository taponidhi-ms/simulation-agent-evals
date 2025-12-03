"""
Data models for conversation generation.

This module defines the data structures used throughout the conversation
generation process, including messages, conversation state, and metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class Role(Enum):
    """Enumeration of conversation participant roles."""
    CUSTOMER = "customer"
    CSR = "csr"
    SYSTEM = "system"


class ConversationStatus(Enum):
    """Enumeration of conversation statuses."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"


@dataclass
class Message:
    """
    Represents a single message in a conversation.
    
    Attributes:
        role: The role of the message sender (customer, csr, or system)
        content: The text content of the message
        timestamp: When the message was created
        metadata: Additional metadata about the message
    """
    role: Role
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ConversationState:
    """
    Tracks the state of an ongoing conversation.
    
    Attributes:
        conversation_id: Unique identifier for the conversation
        messages: List of messages in the conversation
        status: Current status of the conversation
        turn_count: Number of turns in the conversation
        persona: Customer persona used for this conversation
        resolution_reason: Reason for conversation ending (if applicable)
        created_at: When the conversation was created
        ended_at: When the conversation ended (if applicable)
        metadata: Additional metadata about the conversation
    """
    conversation_id: str
    messages: List[Message] = field(default_factory=list)
    status: ConversationStatus = ConversationStatus.ACTIVE
    turn_count: int = 0
    persona: str = ""
    resolution_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        if message.role in [Role.CUSTOMER, Role.CSR]:
            self.turn_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation state to dictionary format."""
        return {
            "conversation_id": self.conversation_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "status": self.status.value,
            "turn_count": self.turn_count,
            "persona": self.persona,
            "resolution_reason": self.resolution_reason,
            "created_at": self.created_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "metadata": self.metadata
        }


@dataclass
class PersonaTemplate:
    """
    Template for customer persona.
    
    Attributes:
        name: Name of the persona
        description: Description of the customer's situation and behavior
        goal: What the customer wants to achieve
        tone: Expected tone (e.g., frustrated, polite, confused)
        complexity: Complexity level (simple, medium, complex)
    """
    name: str
    description: str
    goal: str
    tone: str
    complexity: str = "medium"
    
    def to_prompt(self) -> str:
        """Convert persona to a prompt for the LLM."""
        return f"""You are simulating a customer with the following characteristics:

Persona: {self.name}
Situation: {self.description}
Goal: {self.goal}
Tone: {self.tone}

You are interacting with a customer service representative. Stay in character and 
communicate naturally as this customer would. Be realistic - ask follow-up questions,
express emotions appropriately, and react to the CSR's responses."""


@dataclass
class GenerationConfig:
    """
    Configuration for conversation generation.
    
    Attributes:
        max_turns: Maximum number of turns per conversation
        temperature: LLM temperature for response generation
        max_tokens: Maximum tokens per LLM response
        enable_escalation: Whether to enable escalation scenarios
        escalation_keywords: Keywords that trigger escalation consideration
    """
    max_turns: int = 20
    temperature: float = 0.7
    max_tokens: int = 500
    enable_escalation: bool = True
    escalation_keywords: List[str] = field(default_factory=lambda: [
        "supervisor", "manager", "complaint", "legal", "lawyer", "sue"
    ])
