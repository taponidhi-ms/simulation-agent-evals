"""
Conversation Orchestrator.

This module manages the conversation flow between customer and CSR agents,
handling turn-taking, termination conditions, and conversation state.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from .models import (
    Message, Role, ConversationState, ConversationStatus,
    PersonaTemplate, GenerationConfig
)
from .agents import CustomerAgent, CSRAgent
from .logger import get_logger

# Set up logger for this module
logger = get_logger(__name__)


class ConversationOrchestrator:
    """
    Orchestrates conversations between customer and CSR agents.
    
    Manages the flow of conversation, enforces turn limits, and handles
    termination conditions.
    """
    
    def __init__(self, customer_agent: CustomerAgent, csr_agent: CSRAgent,
                 config: GenerationConfig):
        """
        Initialize conversation orchestrator.
        
        Args:
            customer_agent: The customer agent
            csr_agent: The CSR agent
            config: Configuration for conversation generation
        """
        self.customer_agent = customer_agent
        self.csr_agent = csr_agent
        self.config = config
    
    def run_conversation(self, persona: PersonaTemplate) -> ConversationState:
        """
        Run a complete conversation between customer and CSR.
        
        Args:
            persona: Customer persona to use
            
        Returns:
            Final conversation state with all messages
        """
        # Initialize conversation state
        conversation_id = str(uuid.uuid4())
        state = ConversationState(
            conversation_id=conversation_id,
            persona=persona.name,
            metadata={
                "persona_description": persona.description,
                "persona_goal": persona.goal,
                "persona_tone": persona.tone,
                "persona_complexity": persona.complexity
            }
        )
        
        logger.info(f"Starting conversation {conversation_id} with persona: {persona.name}")
        logger.debug(f"Persona details - Goal: {persona.goal}, Tone: {persona.tone}, Complexity: {persona.complexity}")
        
        # Customer starts the conversation
        try:
            logger.debug("Customer initiating conversation...")
            customer_message = self._generate_customer_message(state)
            state.add_message(customer_message)
            logger.info(f"Turn {state.turn_count}: Customer message added")
            
            # Conversation loop
            while state.status == ConversationStatus.ACTIVE:
                # Check termination conditions
                if self._should_terminate(state):
                    logger.debug(f"Termination condition met at turn {state.turn_count}")
                    break
                
                # CSR responds
                logger.debug("CSR generating response...")
                csr_message = self._generate_csr_message(state)
                state.add_message(csr_message)
                logger.info(f"Turn {state.turn_count}: CSR message added")
                
                # Check if CSR escalated
                if self.csr_agent.should_escalate(csr_message.content):
                    state.status = ConversationStatus.ESCALATED
                    state.resolution_reason = "Escalated to supervisor"
                    logger.info(f"Conversation escalated at turn {state.turn_count}")
                    break
                
                # Check termination conditions again
                if self._should_terminate(state):
                    logger.debug(f"Termination condition met at turn {state.turn_count}")
                    break
                
                # Customer responds
                logger.debug("Customer generating response...")
                customer_message = self._generate_customer_message(state)
                state.add_message(customer_message)
                logger.info(f"Turn {state.turn_count}: Customer message added")
                
                # Check if customer is satisfied (simple heuristic)
                if self._is_conversation_resolved(state):
                    state.status = ConversationStatus.RESOLVED
                    state.resolution_reason = "Issue resolved"
                    logger.info(f"Conversation resolved at turn {state.turn_count}")
                    break
            
            # Set end time
            state.ended_at = datetime.now(timezone.utc)
            
            # If still active after loop, mark as resolved
            if state.status == ConversationStatus.ACTIVE:
                state.status = ConversationStatus.RESOLVED
                state.resolution_reason = "Max turns reached"
                logger.info(f"Conversation ended - max turns reached ({state.turn_count} turns)")
            
            logger.info(f"Conversation {conversation_id} completed with status: {state.status.value}")
            
        except Exception as e:
            state.status = ConversationStatus.FAILED
            state.resolution_reason = f"Error: {str(e)}"
            state.ended_at = datetime.now(timezone.utc)
            logger.error(f"Conversation {conversation_id} failed: {e}", exc_info=True)
        
        return state
    
    def _generate_customer_message(self, state: ConversationState) -> Message:
        """
        Generate a customer message.
        
        Args:
            state: Current conversation state
            
        Returns:
            Generated customer message
        """
        response = self.customer_agent.generate_response(state.messages)
        # Turn number is current count + 1 since this will be the next turn
        turn_number = state.turn_count + 1
        return Message(
            role=Role.CUSTOMER,
            content=response,
            metadata={"turn": turn_number}
        )
    
    def _generate_csr_message(self, state: ConversationState) -> Message:
        """
        Generate a CSR message.
        
        Args:
            state: Current conversation state
            
        Returns:
            Generated CSR message
        """
        response = self.csr_agent.generate_response(state.messages)
        # Turn number is current count + 1 since this will be the next turn
        turn_number = state.turn_count + 1
        return Message(
            role=Role.CSR,
            content=response,
            metadata={"turn": turn_number}
        )
    
    def _should_terminate(self, state: ConversationState) -> bool:
        """
        Check if conversation should terminate.
        
        Args:
            state: Current conversation state
            
        Returns:
            True if conversation should end
        """
        # Max turns reached
        if state.turn_count >= self.config.max_turns:
            return True
        
        # Already ended
        if state.status != ConversationStatus.ACTIVE:
            return True
        
        return False
    
    def _is_conversation_resolved(self, state: ConversationState) -> bool:
        """
        Simple heuristic to detect if conversation is resolved.
        
        Args:
            state: Current conversation state
            
        Returns:
            True if conversation appears resolved
        """
        if len(state.messages) < 4:
            return False
        
        # Check last customer message for satisfaction indicators
        last_customer_msgs = [msg for msg in state.messages[-3:] 
                             if msg.role == Role.CUSTOMER]
        
        if not last_customer_msgs:
            return False
        
        last_customer_msg = last_customer_msgs[-1].content.lower()
        
        satisfaction_keywords = [
            "thank you", "thanks", "perfect", "great", "appreciate",
            "that helps", "that works", "sounds good", "okay", "ok"
        ]
        
        # If customer expresses satisfaction, consider resolved
        if any(keyword in last_customer_msg for keyword in satisfaction_keywords):
            # But not if they're still asking questions
            if "?" not in last_customer_msg:
                return True
        
        return False
