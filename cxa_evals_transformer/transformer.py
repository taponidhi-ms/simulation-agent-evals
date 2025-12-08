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

from .models import CXAConversation, CXAMessage, ToolCall


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
        self._tool_call_counter = 0
    
    def _get_next_tool_call_id(self) -> str:
        """Generate next tool call ID."""
        self._tool_call_counter += 1
        return f"call_{self._tool_call_counter:03d}"
    
    def _transform_message_to_cxa(
        self,
        msg: Dict[str, Any],
        prev_msg: Optional[Dict[str, Any]] = None
    ) -> List[CXAMessage]:
        """
        Transform a single conversation generator message to CXA format.
        
        The CXA Evals format uses tool calls to represent agent actions.
        Each CSR message becomes an assistant message with tool_calls.
        Customer messages become user messages.
        
        Args:
            msg: Message from conversation generator
            prev_msg: Previous message for context
            
        Returns:
            List of CXAMessage objects (may be multiple for complex interactions)
        """
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "system":
            # System message at the start
            return [CXAMessage(
                role="system",
                content=f"Instructions: You are a {{{{{self.task}}}}} agent. Follow business knowledge and ground responses in provided sources.",
                tool_calls=[]
            )]
        
        elif role == "csr":
            # CSR messages become assistant messages with tool calls
            # Map the CSR action to appropriate tool call
            tool_name = self._determine_tool_name(content, prev_msg)
            tool_call = ToolCall(
                id=self._get_next_tool_call_id(),
                name=tool_name,
                arguments=json.dumps({"message": content})
            )
            
            return [CXAMessage(
                role="assistant",
                content="",
                tool_calls=[tool_call]
            )]
        
        elif role == "customer":
            # Customer messages become user messages
            # If previous message was a CSR action, add a tool response first
            messages = []
            
            if prev_msg and prev_msg.get("role") == "csr":
                # Add tool response with the previous CSR content
                prev_content = prev_msg.get("content", "")
                tool_call_id = f"call_{self._tool_call_counter:03d}"
                
                messages.append(CXAMessage(
                    role="tool",
                    content=json.dumps({"message": prev_content}),
                    tool_calls=[ToolCall(
                        id=tool_call_id,
                        name="",
                        arguments="",
                        type="tool_call_id"
                    )]
                ))
            
            # Add user message
            messages.append(CXAMessage(
                role="user",
                content=content,
                tool_calls=[]
            ))
            
            return messages
        
        return []
    
    def _determine_tool_name(self, content: str, prev_msg: Optional[Dict[str, Any]]) -> str:
        """
        Determine the appropriate tool name based on message content.
        
        Args:
            content: Message content
            prev_msg: Previous message for context
            
        Returns:
            Tool name string
        """
        content_lower = content.lower()
        
        # Analyze content to determine tool type
        if prev_msg is None:
            # First message from CSR is typically a greeting
            return "_ask_question"
        
        # Check for closing phrases
        closing_phrases = ["thank you", "have a great day", "glad i could help", "you're welcome"]
        if any(phrase in content_lower for phrase in closing_phrases):
            return "_close_conversation"
        
        # Check for knowledge-based responses
        knowledge_indicators = ["here's what", "you need to", "the process is", "according to"]
        if any(indicator in content_lower for indicator in knowledge_indicators):
            return "_fetch_knowledge_article"
        
        # Check for intent identification
        intent_indicators = ["i understand", "let me help", "i see that"]
        if any(indicator in content_lower for indicator in intent_indicators):
            return "_identify_new_intent"
        
        # Default to asking a question
        return "_ask_question"
    
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
        
        # Reset tool call counter for each conversation
        self._tool_call_counter = 0
        
        # Transform messages
        cxa_messages: List[CXAMessage] = []
        
        # Add system message first
        cxa_messages.append(CXAMessage(
            role="system",
            content=f"Instructions: You are a {{{{{self.task}}}}} agent. Follow business knowledge and ground responses in provided sources.",
            tool_calls=[]
        ))
        
        # Transform conversation messages
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
