"""
Intent Handler for Template Responses

Handles classification and routing of simple intents that don't require RAG pipeline.
Uses either LLM-based or heuristic (rule-based) classifier.
"""

from typing import Dict, Any, AsyncGenerator, Literal
import asyncio

from app.config.response_templates import get_template_response
from app.services.conversation.service import ConversationService
from app.models.message import MessageRole
from app.core import get_logger

logger = get_logger(__name__)

ClassifierType = Literal["llm", "heuristic"]


class IntentHandler:
    """Handles intent classification and template responses."""
    
    def __init__(
        self,
        classifier_type: ClassifierType,
        conversation_service: ConversationService,
        classifier
    ):
        """
        Initialize intent handler with a single classifier.
        
        Args:
            classifier_type: Type of classifier ("llm" or "heuristic")
            conversation_service: Conversation service for persistence
            classifier: Either LLMIntentClassifier or IntentClassifier instance
        """
        self.classifier_type = classifier_type
        self.conversation_service = conversation_service
        self.classifier = classifier
        
        logger.info(f"IntentHandler initialized with {classifier_type} classifier")
    
    async def should_use_template(self, user_query: str) -> Dict[str, Any]:
        """
        Determine if query should use template/direct response.
        
        Args:
            user_query: User's query
            
        Returns:
            Dict with:
                - requires_rag: bool (whether RAG pipeline is needed)
                - response: str (generated response if requires_rag=False)
                - confidence: float
                - source: str (classifier type used)
        """
        if self.classifier_type == "llm":
            # Use LLM classifier
            try:
                result = await self.classifier.classify(user_query)

                logger.debug(f"LLM classifier result: {result} for query: {user_query}")
                
                if not result:
                    logger.warning("LLM classifier returned None, defaulting to RAG")
                    return {
                        "requires_rag": True,
                        "response": "",
                        "confidence": 0.0,
                        "source": "llm_fallback"
                    }
                
                logger.info(
                    f"LLM classifier: requires_rag={result.requires_rag}, "
                    f"confidence={result.confidence:.2f}"
                )
                
                return {
                    "requires_rag": result.requires_rag,
                    "response": result.response,
                    "confidence": result.confidence,
                    "source": "llm"
                }
                
            except Exception as e:
                logger.error(f"LLM classifier failed: {e}", exc_info=True)
                return {
                    "requires_rag": True,
                    "response": "",
                    "confidence": 0.0,
                    "source": "llm_error"
                }
        
        else:
            # Use heuristic classifier
            try:
                result = self.classifier.classify(user_query)
                
                # Check if high confidence template match
                if self.classifier.should_use_template(result):
                    logger.debug(
                        f"Heuristic classifier: {result.intent.value} "
                        f"(confidence={result.confidence:.2f})"
                    )
                    
                    return {
                        "requires_rag": False,
                        "response": get_template_response(result.intent),
                        "confidence": result.confidence,
                        "source": "heuristic",
                        "intent": result.intent
                    }
                else:
                    logger.debug(
                        f"Heuristic classifier: needs RAG "
                        f"(confidence={result.confidence:.2f})"
                    )
                    return {
                        "requires_rag": True,
                        "response": "",
                        "confidence": result.confidence,
                        "source": "heuristic"
                    }
                    
            except Exception as e:
                logger.error(f"Heuristic classifier failed: {e}", exc_info=True)
                return {
                    "requires_rag": True,
                    "response": "",
                    "confidence": 0.0,
                    "source": "heuristic_error"
                }
    
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
