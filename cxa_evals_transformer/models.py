"""
Data models for CXA Evals transformer.

This module defines the data structures for transforming conversation generator
output into CXA Evals input format.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ToolCall:
    """Represents a tool call in CXA Evals format."""
    id: str
    name: str
    arguments: str
    type: Optional[str] = None  # For tool response type field
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments
        }
        if self.type:
            result["type"] = self.type
        return result


@dataclass
class CXAMessage:
    """Represents a message in CXA Evals format."""
    role: str  # "system", "assistant", "user", or "tool"
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "role": self.role,
            "content": self.content
        }
        if self.tool_calls:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        return result


@dataclass
class CXAConversation:
    """Represents a conversation in CXA Evals format."""
    Id: str
    scenario_name: str
    conversation: List[CXAMessage]
    groundness_fact: str = ""
    task: str = "Customer Support"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "Id": self.Id,
            "scenario_name": self.scenario_name,
            "conversation": [msg.to_dict() for msg in self.conversation],
            "groundness_fact": self.groundness_fact,
            "task": self.task
        }
