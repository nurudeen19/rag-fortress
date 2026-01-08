"""
Intent Handler for Template Responses

Handles classification and routing of simple intents that don't require RAG pipeline.
Uses template responses for pleasantries, greetings, and simple queries.

Supports hybrid classification:
- Uses heuristic (rule-based) classifier first for fast pattern matching
- Falls back to LLM-based classifier when heuristic confidence is low
"""

from typing import Dict, Any, AsyncGenerator, Optional
import asyncio

from app.utils.intent_classifier import IntentClassifier
from app.config.response_templates import get_template_response
from app.services.conversation.service import ConversationService
from app.models.message import MessageRole
from app.core import get_logger

logger = get_logger(__name__)


class IntentHandler:
    """Handles intent classification and template responses with hybrid approach."""
    
    def __init__(
        self,
        intent_classifier: Optional[IntentClassifier],
        conversation_service: ConversationService,
        llm_classifier=None
    ):
        """
        Initialize intent handler.
        
        Args:
            intent_classifier: Heuristic intent classifier instance (or None if disabled)
            conversation_service: Conversation service for persistence
            llm_classifier: LLM-based classifier for fallback (or None if disabled)
        """
        self.intent_classifier = intent_classifier
        self.conversation_service = conversation_service
        self.llm_classifier = llm_classifier
        
        logger.info(
            f"IntentHandler initialized "
            f"(heuristic={'enabled' if intent_classifier else 'disabled'}, "
            f"llm={'enabled' if llm_classifier else 'disabled'})"
        )
    
    async def should_use_template(
        self,
        user_query: str,
        user_clearance_level: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Determine if query should use template/direct response using hybrid classification.
        
        Strategy:
        1. Try LLM classifier first if enabled (generates its own responses)
        2. Fall back to heuristic classifier for pattern matching
        3. Return result with response or intent if template should be used, None otherwise
        
        Args:
            user_query: User's query
            user_clearance_level: User's security clearance level
            
        Returns:
            Dict with 'response' (str) or 'intent' (IntentType), or None if RAG needed
        """
        # Try LLM classifier first if enabled
        if self.llm_classifier:
            try:
                llm_result = await self.llm_classifier.classify(user_query)
                
                if llm_result and not llm_result.requires_rag:
                    # LLM says no RAG needed - use its generated response
                    logger.info(
                        f"LLM classifier: requires_rag=false "
                        f"(confidence={llm_result.confidence:.2f})"
                    )
                    
                    return {
                        "response": llm_result.response,
                        "confidence": llm_result.confidence,
                        "source": "llm_classifier"
                    }
                elif llm_result and llm_result.requires_rag:
                    # LLM says RAG is needed
                    logger.debug(
                        f"LLM classifier: requires_rag=true "
                        f"(confidence={llm_result.confidence:.2f})"
                    )
                    return None  # Proceed to RAG pipeline
                    
            except Exception as e:
                logger.warning(
                    f"LLM classifier failed: {e}. Falling back to heuristic classifier.",
                    exc_info=False
                )
                # Continue to heuristic classifier fallback
        
        # Fall back to heuristic classifier
        if self.intent_classifier:
            try:
                heuristic_result = self.intent_classifier.classify(user_query)
                
                # If high confidence from heuristic, use template
                if self.intent_classifier.should_use_template(heuristic_result):
                    logger.debug(
                        f"Heuristic classifier: {heuristic_result.intent.value} "
                        f"(confidence={heuristic_result.confidence:.2f})"
                    )
                    
                    return {
                        "intent": heuristic_result.intent,
                        "confidence": heuristic_result.confidence,
                        "source": "heuristic"
                    }
                else:
                    # Heuristic says RAG is needed
                    logger.debug(
                        f"Heuristic classifier: needs RAG "
                        f"(confidence={heuristic_result.confidence:.2f})"
                    )
                    return None  # Proceed to RAG pipeline
                    
            except Exception as e:
                logger.error(
                    f"Heuristic classifier failed: {e}",
                    exc_info=True
                )
        
        # No classifiers available or both failed - default to RAG pipeline
        return None
    
    async def generate_template_response_streaming(
        self,
        response_or_intent: Any,
        conversation_id: str,
        user_id: int,
        user_query: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a template or LLM-generated response for simple intents.
        
        Simulates streaming behavior to maintain consistent UX with RAG responses.
        Streams character-by-character with small delays for natural feel.
        
        Args:
            response_or_intent: Either str (LLM response) or IntentType (for template)
            conversation_id: Conversation ID
            user_id: User ID
            user_query: User's original query
            
        Yields:
            Stream chunks with token content
        """
        # Determine if we have direct response or need template
        if isinstance(response_or_intent, str):
            # Direct response from LLM classifier
            response_text = response_or_intent
            meta = {"llm_classifier": True}
        else:
            # Intent type - use template
            intent = response_or_intent
            response_text = get_template_response(intent)
            meta = {"intent": intent.value, "template_response": True}
        
        # Stream character by character for natural feel
        for char in response_text:
            yield {"type": "token", "content": char}
            # Small delay to simulate streaming (adjust as needed)
            await asyncio.sleep(0.01)
        
        # Cache and persist the response
        await self.conversation_service.cache_conversation_exchange(
            conversation_id,
            user_query,
            response_text,
            user_id=user_id,
            persist_to_db=False,
            assistant_meta=meta
        )
        
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            token_count=None,
            meta=meta
        )
        
        logger.info(f"Response streamed: {meta}")
    
    async def generate_template_response(
        self,
        response_or_intent: Any,
        conversation_id: str,
        user_id: int,
        user_query: str
    ) -> str:
        """
        Generate complete template or LLM-generated response (non-streaming).
        
        Args:
            response_or_intent: Either str (LLM response) or IntentType (for template)
            conversation_id: Conversation ID
            user_id: User ID
            user_query: User's original query
            
        Returns:
            Response text
        """
        # Determine if we have direct response or need template
        if isinstance(response_or_intent, str):
            # Direct response from LLM classifier
            response_text = response_or_intent
            meta = {"llm_classifier": True}
        else:
            # Intent type - use template
            intent = response_or_intent
            response_text = get_template_response(intent)
            meta = {"intent": intent.value, "template_response": True}
        
        # Cache and persist the response
        await self.conversation_service.cache_conversation_exchange(
            conversation_id,
            user_query,
            response_text,
            user_id=user_id,
            persist_to_db=False,
            assistant_meta=meta
        )
        
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            token_count=None,
            meta=meta
        )
        
        return response_text
