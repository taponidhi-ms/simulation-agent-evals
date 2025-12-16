"""
LLM-based agents for conversation generation.

This module provides the Customer Agent and CSR Agent classes that use
LLMs to generate realistic conversation responses.
"""

from typing import List, Dict, Any, Optional
import json

try:
    from azure.identity import DefaultAzureCredential
    from azure.ai.projects import AIProjectClient
except ImportError:
    DefaultAzureCredential = None
    AIProjectClient = None

try:
    from openai import AzureOpenAI
except ImportError:
    AzureOpenAI = None

from .models import Message, Role, PersonaTemplate
from .knowledge_base import KnowledgeBase
from . import config
from .logger import get_logger, log_llm_interaction

# Set up logger for this module
logger = get_logger(__name__)


class LLMClient:
    """Wrapper for Azure OpenAI client supporting both AAD and API key authentication."""
    
    def __init__(self, 
                 azure_ai_project_endpoint: Optional[str] = None,
                 azure_openai_api_key: Optional[str] = None,
                 azure_openai_endpoint: Optional[str] = None,
                 api_version: str = "2024-02-01"):
        """
        Initialize Azure OpenAI LLM client with AAD or API key authentication.
        
        Supports two authentication methods:
        1. AAD (Azure Active Directory): Uses DefaultAzureCredential via AIProjectClient
        2. API Key: Uses direct API key authentication
        
        Args:
            azure_ai_project_endpoint: Azure AI Project endpoint URL for AAD auth
                (e.g., https://your-resource.services.ai.azure.com/api/projects/your-project)
            azure_openai_api_key: Azure OpenAI API key for API key auth
            azure_openai_endpoint: Azure OpenAI endpoint URL for API key auth
                (e.g., https://your-resource.openai.azure.com/)
            api_version: Azure OpenAI API version
            
        Raises:
            ImportError: If required packages are not installed
            ValueError: If authentication configuration is invalid
        """
        # Determine authentication method
        has_aad = azure_ai_project_endpoint is not None
        has_api_key = (azure_openai_api_key is not None and 
                       azure_openai_endpoint is not None)
        
        if not has_aad and not has_api_key:
            raise ValueError(
                "Either AAD authentication (azure_ai_project_endpoint) or "
                "API key authentication (azure_openai_api_key + azure_openai_endpoint) must be provided"
            )
        
        if has_aad and has_api_key:
            raise ValueError(
                "Cannot use both AAD and API key authentication. "
                "Please provide only one authentication method"
            )
        
        # Initialize client based on authentication method
        if has_aad:
            self._init_aad_client(azure_ai_project_endpoint)
        else:
            self._init_api_key_client(azure_openai_api_key, azure_openai_endpoint, api_version)
    
    def _init_aad_client(self, azure_ai_project_endpoint: str) -> None:
        """Initialize client with AAD authentication."""
        if DefaultAzureCredential is None or AIProjectClient is None:
            raise ImportError(
                "Azure AI Projects packages are required for AAD authentication. "
                "Install with: pip install azure-ai-projects azure-identity"
            )
        
        logger.info("Initializing Azure OpenAI client with AAD authentication...")
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=azure_ai_project_endpoint,
            credential=credential
        )
        self.client = project_client.get_openai_client()
        logger.info("✓ Azure OpenAI client initialized successfully (AAD authentication)")
    
    def _init_api_key_client(self, api_key: str, endpoint: str, api_version: str) -> None:
        """Initialize client with API key authentication."""
        if AzureOpenAI is None:
            raise ImportError(
                "OpenAI package is required for API key authentication. "
                "Install with: pip install openai"
            )
        
        logger.info("Initializing Azure OpenAI client with API key authentication...")
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        logger.info("✓ Azure OpenAI client initialized successfully (API key authentication)")
    
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
            logger.debug(f"Generating LLM response with model={model}, temperature={temperature}, max_tokens={max_tokens}")
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("LLM returned empty response")
            logger.debug(f"LLM response generated successfully ({len(content)} characters)")
            return content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
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
        
        # Determine turn number
        turn_number = len(conversation_history) + 1
        
        # Log the prompt being sent
        logger.debug(f"Customer agent generating response for turn {turn_number}")
        
        # Generate response
        response = self.llm_client.generate(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # Log the full LLM interaction for transcript viewing
        prompt_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        log_llm_interaction(
            logger=logger,
            agent_type="Customer",
            prompt=prompt_text,
            response=response,
            model=self.model,
            temperature=self.temperature,
            turn_number=turn_number
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
        
        # Determine turn number
        turn_number = len(conversation_history) + 1
        
        # Log the prompt being sent
        logger.debug(f"CSR agent generating response for turn {turn_number}")
        
        # Generate response
        response = self.llm_client.generate(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # Log the full LLM interaction for transcript viewing
        prompt_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        log_llm_interaction(
            logger=logger,
            agent_type="CSR",
            prompt=prompt_text,
            response=response,
            model=self.model,
            temperature=self.temperature,
            turn_number=turn_number
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
