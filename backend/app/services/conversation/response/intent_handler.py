"""
Intent Handler for Template Responses

Handles classification and routing of simple intents that don't require RAG pipeline.
Uses template responses for pleasantries, greetings, and simple queries.
"""

from typing import Dict, Any, AsyncGenerator, Optional
import asyncio

from app.utils.intent_classifier import IntentClassifier, IntentType, IntentResult
from app.config.response_templates import get_template_response
from app.services.conversation.service import ConversationService
from app.models.message import MessageRole
from app.core import get_logger

logger = get_logger(__name__)


class IntentHandler:
    """Handles intent classification and template responses."""
    
    def __init__(
        self,
        intent_classifier: Optional[IntentClassifier],
        conversation_service: ConversationService
    ):
        """
        Initialize intent handler.
        
        Args:
            intent_classifier: Intent classifier instance (or None if disabled)
            conversation_service: Conversation service for persistence
        """
        self.intent_classifier = intent_classifier
        self.conversation_service = conversation_service
    
    def should_use_template(self, user_query: str) -> Optional[IntentResult]:
        """
        Determine if query should use template response.
        
        Args:
            user_query: User's query
            
        Returns:
            IntentResult if template should be used, None otherwise
        """
        if not self.intent_classifier:
            return None
        
        intent_result = self.intent_classifier.classify(user_query)
        
        if self.intent_classifier.should_use_template(intent_result):
            return intent_result
        
        return None
    
    async def generate_template_response_streaming(
        self,
        intent: IntentType,
        conversation_id: str,
        user_id: int,
        user_query: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a template response for simple intents.
        
        Simulates streaming behavior to maintain consistent UX with RAG responses.
        Streams character-by-character with small delays for natural feel.
        
        Args:
            intent: Intent type
            conversation_id: Conversation ID
            user_id: User ID
            user_query: User's original query
            
        Yields:
            Stream chunks with token content
        """
        # Get template response
        template_response = get_template_response(intent)
        
        # Stream character by character for natural feel
        for char in template_response:
            yield {"type": "token", "content": char}
            # Small delay to simulate streaming (adjust as needed)
            await asyncio.sleep(0.01)
        
        # Cache and persist the template response
        await self.conversation_service.cache_conversation_exchange(
            conversation_id,
            user_query,
            template_response,
            user_id=user_id,
            persist_to_db=False,
            assistant_meta={"intent": intent.value, "template_response": True}
        )
        
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=template_response,
            token_count=None,
            meta={"intent": intent.value, "template_response": True}
        )
        
        logger.info(f"Template response streamed for intent: {intent.value}")
    
    async def generate_template_response(
        self,
        intent: IntentType,
        conversation_id: str,
        user_id: int,
        user_query: str
    ) -> str:
        """
        Generate complete template response (non-streaming).
        
        Args:
            intent: Intent type
            conversation_id: Conversation ID
            user_id: User ID
            user_query: User's original query
            
        Returns:
            Template response text
        """
        template_response = get_template_response(intent)
        
        # Cache and persist the template response
        await self.conversation_service.cache_conversation_exchange(
            conversation_id,
            user_query,
            template_response,
            user_id=user_id,
            persist_to_db=False,
            assistant_meta={"intent": intent.value}
        )
        
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=template_response,
            token_count=None,
            meta={"intent": intent.value}
        )
        
        return template_response
