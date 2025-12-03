"""
LLM-based agents for conversation generation.

This module provides the Customer Agent and CSR Agent classes that use
LLMs to generate realistic conversation responses.
"""

from typing import List, Dict, Any, Optional
import json

try:
    from openai import OpenAI, AzureOpenAI
except ImportError:
    OpenAI = None
    AzureOpenAI = None

from .models import Message, Role, PersonaTemplate
from .knowledge_base import KnowledgeBase
from . import config


class LLMClient:
    """Wrapper for OpenAI/Azure OpenAI client."""
    
    def __init__(self, api_key: str, api_base: str, api_type: str = "openai", 
                 api_version: str = "2024-02-01"):
        """
        Initialize LLM client.
        
        Args:
            api_key: API key for OpenAI or Azure OpenAI
            api_base: Base URL for API
            api_type: Type of API ("openai" or "azure")
            api_version: API version (for Azure)
        """
        if OpenAI is None:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )
        
        self.api_type = api_type
        if api_type == "azure":
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=api_base
            )
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url=api_base if api_base != "https://api.openai.com/v1" else None
            )
    
    def generate(self, messages: List[Dict[str, str]], model: str,
                 temperature: float = 0.7, max_tokens: int = 500) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dictionaries with "role" and "content"
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("LLM returned empty response")
            return content
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}")


class CustomerAgent:
    """
    Customer agent that simulates a customer using an LLM.
    
    The agent maintains a persona and generates customer responses
    based on the conversation history.
    """
    
    def __init__(self, llm_client: LLMClient, persona: PersonaTemplate,
                 model: str, temperature: float = 0.7, max_tokens: int = 500):
        """
        Initialize customer agent.
        
        Args:
            llm_client: LLM client for generation
            persona: Customer persona template
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
        """
        self.llm_client = llm_client
        self.persona = persona
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def generate_response(self, conversation_history: List[Message]) -> str:
        """
        Generate customer response based on conversation history.
        
        Args:
            conversation_history: List of previous messages
            
        Returns:
            Generated customer message
        """
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self.persona.to_prompt()}
        ]
        
        # Add conversation history
        for msg in conversation_history:
            if msg.role == Role.CUSTOMER:
                messages.append({"role": "assistant", "content": msg.content})
            elif msg.role == Role.CSR:
                messages.append({"role": "user", "content": f"CSR: {msg.content}"})
        
        # Generate response
        response = self.llm_client.generate(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.strip()


class CSRAgent:
    """
    Customer Service Representative agent using an LLM.
    
    The agent has access to a knowledge base and generates appropriate
    responses to customer queries. It can also escalate conversations
    when necessary.
    """
    
    def __init__(self, llm_client: LLMClient, knowledge_base: KnowledgeBase,
                 model: str, temperature: float = 0.7, max_tokens: int = 500,
                 enable_escalation: bool = True):
        """
        Initialize CSR agent.
        
        Args:
            llm_client: LLM client for generation
            knowledge_base: Knowledge base for answering queries
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
            enable_escalation: Whether to enable escalation scenarios
        """
        self.llm_client = llm_client
        self.knowledge_base = knowledge_base
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_escalation = enable_escalation
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for CSR agent."""
        kb_context = self.knowledge_base.to_prompt_context(max_items=15)
        
        prompt = f"""You are a helpful and professional customer service representative.

Your role is to:
1. Assist customers with their inquiries using the knowledge base provided
2. Be polite, empathetic, and solution-oriented
3. If you cannot help with a request or it's outside your scope, politely end the conversation with "I'll transfer you to a supervisor for further assistance."

{kb_context}

Guidelines:
- Keep responses concise and helpful
- Use information from the knowledge base when available
- Be empathetic to customer concerns
- If the customer's issue cannot be resolved with available knowledge, escalate
- Do not make up information not in the knowledge base"""

        return prompt
    
    def generate_response(self, conversation_history: List[Message]) -> str:
        """
        Generate CSR response based on conversation history.
        
        Args:
            conversation_history: List of previous messages
            
        Returns:
            Generated CSR message
        """
        # Build messages for LLM
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        
        # Add conversation history
        for msg in conversation_history:
            if msg.role == Role.CUSTOMER:
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == Role.CSR:
                messages.append({"role": "assistant", "content": msg.content})
        
        # Generate response
        response = self.llm_client.generate(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.strip()
    
    def should_escalate(self, response: str) -> bool:
        """
        Check if the response indicates escalation.
        
        Args:
            response: CSR response text
            
        Returns:
            True if response indicates escalation
        """
        if not self.enable_escalation:
            return False
        
        escalation_phrases = [
            "transfer you to a supervisor",
            "transfer to supervisor",
            "escalate to",
            "speak with a supervisor",
            "speak to a manager",
            "transfer you to a manager"
        ]
        
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in escalation_phrases)
