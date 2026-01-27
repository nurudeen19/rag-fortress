"""
Intent Handler for Template Responses

Handles classification and template response generation.
Uses either LLM-based or heuristic (rule-based) classifier.
"""

from typing import Any, AsyncGenerator, Literal, Union, Dict
import asyncio

from app.services.conversation.service import ConversationService
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
    
    async def classify(self, user_query: str) -> Union[Any, None]:
        """
        Classify user query and return raw classifier result.
        
        Returns the raw result object from either LLM or heuristic classifier.
        Response service will handle decision logic based on result.
            
        Returns:
            LLMClassificationResult or UnifiedClassificationResult (from heuristic)
            Returns None on failure (caller should handle fallback)
        """
        if self.classifier_type == "llm":
            # Use LLM classifier - returns LLMClassificationResult
            try:
                result = await self.classifier.classify(user_query)
                
                if not result:
                    logger.warning("LLM classifier returned None")
                    return None
                
                return result
                
            except Exception as e:
                logger.error(f"LLM classifier failed: {e}", exc_info=True)
                return None
        
        else:
            # Use heuristic classifier - returns UnifiedClassificationResult
            try:
                result = self.classifier.classify_heuristic(user_query)                
                
                return result
                    
            except Exception as e:
                logger.error(f"Heuristic classifier failed: {e}", exc_info=True)
                return None
    
    async def generate_template_response_streaming(
        self,
        response_text: str,
        conversation_id: str,
        user_id: int,
        user_query: str,
        meta: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a template or classifier-generated response.
        
        Simulates streaming behavior to maintain consistent UX with RAG responses.
        Streams character-by-character with small delays for natural feel.
            
        Yields:
            Stream chunks with token content
        """
        # Stream character by character for natural feel
        for char in response_text:
            yield {"type": "token", "content": char}
            # Small delay to simulate streaming (adjust as needed)
            await asyncio.sleep(0.01)
        
        # Save response (cache + persist)
        await self.conversation_service.save_assistant_response(
            conversation_id=conversation_id,
            user_id=user_id,
            user_query=user_query,
            response_text=response_text,
            assistant_meta=meta
        )
        
        logger.debug(f"Response streamed: {meta}")
    
    async def generate_template_response(
        self,
        response_text: str,
        conversation_id: str,
        user_id: int,
        user_query: str,
        meta: Dict[str, Any]
    ) -> str:
        """
        Generate complete template or classifier-generated response (non-streaming).
            
        Returns:
            Response text
        """
        # Save response (cache + persist)
        await self.conversation_service.save_assistant_response(
            conversation_id=conversation_id,
            user_id=user_id,
            user_query=user_query,
            response_text=response_text,
            assistant_meta=meta
        )
        
        return response_text
