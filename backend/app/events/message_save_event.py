"""
Message Save Event Handler

Handles asynchronous message persistence to database to reduce latency
in the main response pipeline. Messages are saved to cache synchronously
and persisted to DB in the background.
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid

from app.events.base import BaseEventHandler
from app.core import get_logger
from app.core.database import get_async_session
from app.models.message import Message, MessageRole
from app.models.conversation import Conversation
from sqlalchemy import select

logger = get_logger(__name__)


class MessageSaveEvent(BaseEventHandler):
    """
    Message save event handler.
    
    Handles background persistence of conversation messages to database. Cache updates happen synchronously in the main flow.
    
    Event data fields:
    - conversation_id: str (required)
    - user_id: int (required)
    - role: str (required) - "user" or "assistant"
    - content: str (required) - message content (will be encrypted)
    - token_count: Optional[int] - estimated token count
    - meta: Optional[Dict] - message metadata (e.g., sources, intent)
    - user_query: Optional[str] - paired user query (for assistant messages)
    
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
        """Process message save event."""
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
            
            # Get database session
            async for session in get_async_session():
                try:
                    await self._save_message_to_db(
                        session=session,
                        conversation_id=conversation_id,
                        user_id=user_id,
                        role=role,
                        content=content,
                        token_count=token_count,
                        meta=meta
                    )
                    break  # Successfully saved
                except Exception as e:
                    logger.error(f"Database session error: {e}", exc_info=True)
                    await session.rollback()
        
        except KeyError as e:
            logger.error(f"Missing required field in save_message event: {e}")
        except Exception as e:
            logger.error(f"Failed to process save_message event: {e}", exc_info=True)
    
    async def _save_message_to_db(
        self,
        session: AsyncSession,
        conversation_id: str,
        user_id: int,
        role: MessageRole,
        content: str,
        token_count: int | None,
        meta: Dict[str, Any] | None
    ) -> None:
        """
        Save message to database with conversation metadata update.
        
        Performs atomic transaction:
        1. Create message record
        2. Update conversation denormalized fields
        """
        try:
            # Verify conversation exists and belongs to user
            stmt = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                logger.warning(
                    f"Conversation {conversation_id} not found for user {user_id}, "
                    f"skipping message save"
                )
                return
            
            # Create message
            message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                token_count=token_count,
                meta=meta,
            )
            session.add(message)
            
            # Update conversation denormalized fields
            conversation.message_count += 1
            conversation.last_message_at = datetime.now(timezone.utc)
            
            await session.flush()
            await session.commit()
            
            logger.info(
                f"Background save: {role.value} message to conversation {conversation_id} "
                f"(msg_count={conversation.message_count})"
            )
        
        except Exception as e:
            await session.rollback()
            logger.error(
                f"Failed to save {role.value} message to DB: {e}",
                exc_info=True
            )
            raise
