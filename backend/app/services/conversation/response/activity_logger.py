"""
Activity Logger for Response Generation

Centralizes activity logging for conversation response generation events.
All logging is done via EventBus for non-blocking, async processing.
"""

from typing import Optional, Dict, Any
from app.core import get_logger
from app.core.events import get_event_bus

logger = get_logger(__name__)


class ConversationActivityLogger:
    """Handles activity logging for conversation responses."""
    
    @staticmethod
    async def log_retrieval_error(
        user_id: int,
        error_type: str,
        user_query: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log retrieval errors from the retriever service.
        """
        try:
            bus = get_event_bus()
            
            # Map error_type to incident_type and severity
            error_mapping = {
                "insufficient_clearance": ("insufficient_clearance", "warning"),
                "no_clearance": ("no_clearance", "warning"),
                "no_documents": ("retrieval_no_context", "info"),
                "no_relevant_documents": ("retrieval_no_context", "info"),
                "low_quality_results": ("retrieval_no_context", "info"),
                "reranker_no_quality": ("retrieval_no_context", "info"),
            }
            incident_type, severity = error_mapping.get(error_type, ("retrieval_error", "warning"))
            
            payload = {
                "user_id": user_id,
                "error_type": error_type,
                "incident_type": incident_type,
                "severity": severity,
                "description": f"Retrieval failed: {error_type}",
                "user_query": user_query[:500],
            }
            
            if details:
                payload["details"] = details
            
            await bus.emit("activity_log", payload)
        except Exception as e:
            logger.error(f"Failed to emit activity log event: {e}")
