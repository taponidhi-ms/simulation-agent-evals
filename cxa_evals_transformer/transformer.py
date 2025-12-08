"""
CXA Evals Transformer.

This module transforms conversation generator output into CXA Evals input format.
The transformation converts the conversation format from the conversation_generator
module to the format expected by the CXA Evals framework.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import CXAConversation, CXAMessage


class CXAEvalsTransformer:
    """Transforms conversation generator output to CXA Evals format."""
    
    def __init__(
        self,
        scenario_name: str = "customer_support",  # Deprecated: scenario_name is always "SimulationAgent"
        task: str = "Customer Support",
        groundness_fact: str = ""
    ):
        """
        Initialize the transformer.
        
        Args:
            scenario_name: DEPRECATED - This parameter is ignored. Scenario name is always "SimulationAgent".
            task: Task description for the agent
            groundness_fact: Default groundness fact for conversations
        """
        # Note: scenario_name parameter is deprecated and ignored.
        # All conversations use "SimulationAgent" as the scenario name.
        self.task = task
        self.groundness_fact = groundness_fact
    
    def _transform_message_to_cxa(
        self,
        msg: Dict[str, Any],
        prev_msg: Optional[Dict[str, Any]] = None
    ) -> List[CXAMessage]:
        """
        Transform a single conversation generator message to CXA format.
        
        Each message is converted to a CXA message with role and content only.
        CSR messages become Assistant messages, customer messages become Customer messages.
        System messages are skipped.
        
        Args:
            msg: Message from conversation generator
            prev_msg: Previous message for context (currently unused)
            
        Returns:
            List of CXAMessage objects (typically one message per input)
        """
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "system":
            # Skip system messages
            return []
        
        elif role == "csr":
            # CSR messages become Assistant messages
            return [CXAMessage(
                role="Assistant",
                content=content
            )]
        
        elif role == "customer":
            # Customer messages become Customer messages
            return [CXAMessage(
                role="Customer",
                content=content
            )]
        
        return []
    
    def transform_conversation(self, conversation_data: Dict[str, Any]) -> CXAConversation:
        """
        Transform a single conversation from generator format to CXA format.
        
        Args:
            conversation_data: Conversation in generator format
            
        Returns:
            CXAConversation object
        """
        conv_id = conversation_data.get("conversation_id", "conv_unknown")
        messages = conversation_data.get("messages", [])
        persona = conversation_data.get("persona", "")
        metadata = conversation_data.get("metadata", {})
        
        # Transform messages
        cxa_messages: List[CXAMessage] = []
        
        # Transform conversation messages (skip system messages)
        for i, msg in enumerate(messages):
            prev_msg = messages[i - 1] if i > 0 else None
            transformed = self._transform_message_to_cxa(msg, prev_msg)
            cxa_messages.extend(transformed)
        
        # Create CXA conversation with persona metadata
        return CXAConversation(
            Id=conv_id,
            scenario_name="SimulationAgent",  # Always use "SimulationAgent" as scenario name
            conversation=cxa_messages,
            groundness_fact=self.groundness_fact,
            task=self.task,
            persona_name=persona,
            persona_description=metadata.get("persona_description", ""),
            persona_goal=metadata.get("persona_goal", ""),
            persona_tone=metadata.get("persona_tone", ""),
            persona_complexity=metadata.get("persona_complexity", "")
        )
    
    def transform_directory(
        self,
        input_dir: str,
        output_file: str,
        pattern: str = "*.json"
    ) -> int:
        """
        Transform all conversation files in a directory.
        
        Args:
            input_dir: Directory containing conversation generator output
            output_file: Output file path for transformed conversations
            pattern: File pattern to match (default: "*.json")
            
        Returns:
            Number of conversations transformed
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Find all conversation files (excluding metadata)
        conversation_files = []
        for file_path in input_path.rglob(pattern):
            if file_path.name != "_metadata.json":
                conversation_files.append(file_path)
        
        if not conversation_files:
            raise ValueError(f"No conversation files found in {input_dir}")
        
        # Transform conversations
        cxa_conversations = []
        for file_path in conversation_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    conversation_data = json.load(f)
                
                cxa_conv = self.transform_conversation(conversation_data)
                cxa_conversations.append(cxa_conv)
            except Exception as e:
                print(f"Warning: Failed to transform {file_path}: {e}")
                continue
        
        # Save transformed conversations
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "conversations": [conv.to_dict() for conv in cxa_conversations]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return len(cxa_conversations)
