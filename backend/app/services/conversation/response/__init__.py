"""
Response service components package.

This package contains modular components for conversation response generation:
- activity_logger: Handles activity logging for conversation events
- intent_handler: Manages intent classification and template responses
- error_handler: Handles error response generation
- retrieval_coordinator: Coordinates multi-query retrieval with partial context tracking
- pipeline: Orchestrates the response generation flow
"""

from app.services.conversation.response.activity_logger import ConversationActivityLogger
from app.services.conversation.response.intent_handler import IntentHandler
from app.services.conversation.response.error_handler import ErrorResponseHandler
from app.services.conversation.response.retrieval_coordinator import RetrievalCoordinator
from app.services.conversation.response.pipeline import ResponsePipeline

__all__ = [
    "ConversationActivityLogger",
    "IntentHandler",
    "ErrorResponseHandler",
    "RetrievalCoordinator",
    "ResponsePipeline"
]
