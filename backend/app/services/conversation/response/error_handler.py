"""
Error Response Handler

Handles generation of error responses for various failure scenarios.
Provides consistent error handling for both streaming and non-streaming modes.
"""

from typing import Dict, Any, AsyncGenerator

from app.config.prompt_settings import get_prompt_settings
from app.services.conversation.service import ConversationService
from app.models.message import MessageRole
from app.core import get_logger

logger = get_logger(__name__)


class ErrorResponseHandler:
    """Handles error response generation."""
    
    def __init__(self, conversation_service: ConversationService):
        """
        Initialize error response handler.
        
        Args:
            conversation_service: Conversation service for persistence
        """
        self.conversation_service = conversation_service
        self.prompt_settings = get_prompt_settings()
    
    def get_no_context_response_text(self, error_type: str) -> str:
        """
        Get response text when no context is available.
        
        Args:
            error_type: Type of retrieval error
            
        Returns:
            Response text based on error type
        """
        if error_type == "no_clearance":
            return self.prompt_settings.RETRIEVAL_DEPT_BLOCKED_MESSAGE
        elif error_type == "insufficient_clearance":
            return self.prompt_settings.RETRIEVAL_SECURITY_BLOCKED_MESSAGE
        else:
            # Default for no_context, no_documents, etc.
            return self.prompt_settings.RETRIEVAL_NO_CONTEXT_MESSAGE
    
    async def stream_no_context_response(
        self,
        error_type: str,
        user_query: str,
        conversation_id: str,
        user_id: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a response when no relevant context is found.
        
        Args:
            error_type: Type of retrieval error
            user_query: User's original query
            conversation_id: Conversation ID
            user_id: User ID
            
        Yields:
            Stream chunks with token content
        """
        # Get appropriate message based on error type
        response_text = self.get_no_context_response_text(error_type)
        
        # Stream the message word by word for consistency
        words = response_text.split()
        for word in words:
            yield {"type": "token", "content": word + " "}
        
        # Persist the response
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            token_count=None,
            meta={"source": "no_context", "error_type": error_type}
        )
        
        logger.info(f"Completed no-context response for conversation {conversation_id}")
    
    async def generate_no_context_response(
        self,
        error_type: str,
        user_query: str,
        conversation_id: str,
        user_id: int
    ) -> str:
        """
        Generate complete no-context response (non-streaming).
        
        Args:
            error_type: Type of retrieval error
            user_query: User's original query
            conversation_id: Conversation ID
            user_id: User ID
            
        Returns:
            Response text
        """
        response_text = self.get_no_context_response_text(error_type)
        
        # Persist the response
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            token_count=None,
            meta={"source": "no_context", "error_type": error_type}
        )
        
        return response_text
