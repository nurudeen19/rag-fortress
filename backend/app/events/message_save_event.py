"""
Message Save Event Handler

Handles asynchronous message persistence to database to reduce latency
in the main response pipeline. Messages are saved to cache synchronously
and persisted to DB in the background.
"""

from typing import Dict, Any

from app.events.base import BaseEventHandler
from app.core import get_logger
from app.core.database import get_session
from app.models.message import MessageRole
from app.services.conversation.service import ConversationService

logger = get_logger(__name__)


class MessageSaveEvent(BaseEventHandler):
    """
    Message save event handler.
    
    Handles background persistence of conversation messages to database.
    Cache updates happen synchronously in the main flow.
    
    Event data fields:
    - conversation_id: str (required)
    - user_id: int (required)
    - role: str (required) - "user" or "assistant"
    - content: str (required) - message content (will be encrypted)
    - token_count: Optional[int] - estimated token count
    - meta: Optional[Dict] - message metadata (e.g., sources, intent)
    
    Usage:
        from app.core.events import get_event_bus
        
        bus = get_event_bus()
        await bus.emit("save_message", {
            "conversation_id": "conv-123",
            "user_id": 456,
            "role": "assistant",
            "content": "Response text here",
            "meta": {"sources": [...]}
        })
    """
    
    @property
    def event_type(self) -> str:
        return "save_message"
    
    async def handle(self, event_data: Dict[str, Any]) -> None:
        """Process message save event using existing ConversationService."""
        try:
            # Validate required fields
            conversation_id = event_data["conversation_id"]
            user_id = event_data["user_id"]
            role_str = event_data["role"]
            content = event_data["content"]
            
            # Optional fields
            token_count = event_data.get("token_count")
            meta = event_data.get("meta")
            
            # Parse role
            try:
                role = MessageRole[role_str.upper()]
            except KeyError:
                logger.error(f"Invalid role: {role_str}")
                return
            
            # Get database session and use ConversationService
            async for session in get_session():
                try:
                    conversation_service = ConversationService(session)
                    
                    # Use existing add_message method
                    result = await conversation_service.add_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role=role,
                        content=content,
                        token_count=token_count,
                        meta=meta
                    )
                    
                    if result["success"]:
                        logger.info(
                            f"Background save: {role.value} message to conversation {conversation_id}"
                        )
                    else:
                        logger.warning(
                            f"Failed to save {role.value} message: {result.get('error')}"
                        )
                    
                except Exception as e:
                    logger.error(f"Error saving message: {e}", exc_info=True)
                finally:
                    # Session cleanup handled by async generator
                    break
        
        except KeyError as e:
            logger.error(f"Missing required field in save_message event: {e}")
        except Exception as e:
            logger.error(f"Failed to process save_message event: {e}", exc_info=True)
