"""Service layer for Conversation and Message CRUD operations."""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta
import uuid
import json

from app.core.cache import get_cache

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.core import get_logger
from app.services.query_validator_service import get_query_validator
from app.services import activity_logger_service

logger = get_logger(__name__)


class ConversationService:
    """Provides CRUD operations for conversations and messages."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache = get_cache()

    # ==================== Helper Methods ====================

    def _serialize_conversation(self, conversation: Conversation) -> Dict[str, Any]:
        """Convert Conversation model to dict."""
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "message_count": conversation.message_count,
            "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            "is_deleted": conversation.is_deleted,
        }

    def _serialize_message(self, message: Message) -> Dict[str, Any]:
        """Convert Message model to dict."""
        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role.value,
            "content": message.content,
            "token_count": message.token_count,
            "meta": message.meta,
            "created_at": message.created_at.isoformat() if message.created_at else None,
            "updated_at": message.updated_at.isoformat() if message.updated_at else None,
        }

    # ==================== Conversation Operations ====================

    async def create_conversation(
        self,
        user_id: int,
        title: str = "New Conversation",
    ) -> Dict[str, Any]:
        """Create a new conversation for a user."""
        try:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                message_count=0,
                last_message_at=datetime.now(timezone.utc),
            )
            self.session.add(conversation)
            await self.session.flush()
            await self.session.commit()
            logger.info(f"Created conversation {conversation.id} for user {user_id}")
            
            return {
                "success": True,
                "conversation": self._serialize_conversation(conversation)
            }
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "conversation": None
            }

    async def get_conversation(
        self, 
        conversation_id: str, 
        user_id: int
    ) -> Optional[Conversation]:
        """Get a conversation by ID, ensuring it belongs to the user (returns model)."""
        stmt = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_conversation_dict(
        self, 
        conversation_id: str, 
        user_id: int
    ) -> Dict[str, Any]:
        """Get a conversation by ID as dict with success/error handling."""
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return {
                    "success": False,
                    "error": "Conversation not found",
                    "conversation": None
                }
            
            return {
                "success": True,
                "conversation": self._serialize_conversation(conversation)
            }
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "conversation": None
            }

    async def list_user_conversations(
        self,
        user_id: int,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List all conversations for a user with pagination."""
        try:
            stmt = select(Conversation).where(Conversation.user_id == user_id)
            
            if not include_deleted:
                stmt = stmt.where(Conversation.is_deleted == False)
            
            # Order by most recent activity
            stmt = stmt.order_by(Conversation.last_message_at.desc())
            
            # Count total (without pagination)
            count_stmt = select(Conversation).where(Conversation.user_id == user_id)
            if not include_deleted:
                count_stmt = count_stmt.where(Conversation.is_deleted == False)
            
            count_result = await self.session.execute(count_stmt)
            total = len(count_result.scalars().all())
            
            # Apply pagination
            stmt = stmt.limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            conversations = result.scalars().all()
            
            logger.info(f"Retrieved {len(conversations)} conversations for user {user_id}")
            
            return {
                "success": True,
                "total": total,
                "limit": limit,
                "offset": offset,
                "conversations": [self._serialize_conversation(c) for c in conversations]
            }
        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "conversations": [],
                "total": 0
            }

    async def update_conversation(
        self,
        conversation_id: str,
        user_id: int,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update conversation metadata."""
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return {
                    "success": False,
                    "error": "Conversation not found",
                    "conversation": None
                }
            
            if title is not None:
                conversation.title = title
            
            await self.session.flush()
            await self.session.commit()
            logger.info(f"Updated conversation {conversation_id}")
            
            return {
                "success": True,
                "conversation": self._serialize_conversation(conversation)
            }
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating conversation: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "conversation": None
            }

    async def soft_delete_conversation(
        self, 
        conversation_id: str, 
        user_id: int
    ) -> Dict[str, Any]:
        """Soft delete a conversation."""
        try:
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return {
                    "success": False,
                    "error": "Conversation not found"
                }
            
            conversation.is_deleted = True
            conversation.deleted_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.commit()
            logger.info(f"Soft deleted conversation {conversation_id}")
            
            return {
                "success": True,
                "message": "Conversation deleted successfully"
            }
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== Message Operations ====================

    async def add_message(
        self,
        conversation_id: str,
        user_id: int,
        role: MessageRole,
        content: str,
        token_count: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a message to a conversation and update denormalized fields."""
        try:
            # SECURITY: Validate user query for malicious patterns (only for USER role)
            if role == MessageRole.USER:
                validator = get_query_validator()
                validation = await validator.validate_query(content, user_id)
                
                if not validation["valid"]:
                    logger.warning(
                        f"Malicious query blocked: user_id={user_id}, "
                        f"conversation_id={conversation_id}, "
                        f"threat={validation['threat_type']}, "
                        f"confidence={validation['confidence']:.2f}"
                    )
                    
                    # Log malicious query attempt to database
                    await activity_logger_service.log_activity(
                        db=self.session,
                        user_id=user_id,
                        incident_type="malicious_query_blocked",
                        severity="critical",
                        description=f"Malicious query blocked: {validation['threat_type']}",
                        details={
                            "threat_type": validation["threat_type"],
                            "confidence": validation["confidence"],
                            "reason": validation["reason"],
                            "conversation_id": conversation_id
                        },
                        user_query=content,
                        threat_type=validation["threat_type"]
                    )
                    await self.session.commit()
                    
                    return {
                        "success": False,
                        "error": validation["reason"],
                        "threat_type": validation["threat_type"],
                        "message": None
                    }
            
            # Verify conversation exists and belongs to user
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found for user {user_id}")
                return {
                    "success": False,
                    "error": "Conversation not found",
                    "message": None
                }
            
            # Create message
            message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                token_count=token_count,
                meta=meta,
            )
            self.session.add(message)
            
            # Update denormalized fields in conversation
            conversation.message_count += 1
            conversation.last_message_at = datetime.now(timezone.utc)
            
            await self.session.flush()
            await self.session.commit()
            logger.info(f"Added {role.value} message to conversation {conversation_id}")
            
            return {
                "success": True,
                "message": self._serialize_message(message)
            }
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding message: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": None
            }

    async def get_conversation_history(self, conversation_id: str, user_id: int) -> List[Dict[str, str]]:
        """Return the cached conversation history or fetch the recent conversation context."""
        cache_key = f"conversation:history:{conversation_id}"
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                history = json.loads(cached_data)
                logger.info(f"Retrieved {len(history)} history messages from cache for {conversation_id}")
                return history
        except Exception as exc:
            logger.warning(f"Failed to read history cache: {exc}")

        context_result = await self.get_conversation_context(conversation_id, user_id, last_n=6)
        if not context_result.get("success"):
            return []

        history = [
            {"role": entry["role"].lower(), "content": entry["content"]}
            for entry in context_result.get("context", [])
        ]

        if history:
            await self._cache_history(conversation_id, history)

        return history

    async def cache_conversation_exchange(
        self,
        conversation_id: str,
        user_msg: str,
        assistant_msg: str,
        user_id: Optional[int] = None,
        persist_to_db: bool = False
    ) -> None:
        """Persist the latest exchange to cache and optionally the database."""
        cache_key = f"conversation:history:{conversation_id}"
        try:
            cached_data = await self.cache.get(cache_key)
            history = json.loads(cached_data) if cached_data else []
        except Exception as exc:
            logger.warning(f"Failed to read history cache before update: {exc}")
            history = []

        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})
        history = history[-6:]

        await self._cache_history(conversation_id, history)
        logger.info(f"Cached exchange for {conversation_id}")

        if persist_to_db and user_id is not None:
            await self._persist_messages_to_db(conversation_id, user_id, user_msg, assistant_msg)

    async def _cache_history(self, conversation_id: str, history: List[Dict[str, str]]) -> None:
        """Helper to persist conversation history to cache with a 24-hour TTL."""
        try:
            cache_key = f"conversation:history:{conversation_id}"
            await self.cache.set(
                cache_key,
                json.dumps(history),
                ttl=int(timedelta(hours=24).total_seconds())
            )
        except Exception as exc:
            logger.error(f"Failed to cache history for {conversation_id}: {exc}")

    async def _persist_messages_to_db(
        self,
        conversation_id: str,
        user_id: int,
        user_msg: str,
        assistant_msg: str
    ) -> None:
        """Persist the user and assistant turns to the database."""
        try:
            user_result = await self.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role=MessageRole.USER,
                content=user_msg
            )
            if not user_result.get("success"):
                logger.warning(
                    f"Failed to persist user message for {conversation_id}: {user_result.get('error')}"
                )

            assistant_result = await self.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role=MessageRole.ASSISTANT,
                content=assistant_msg
            )
            if not assistant_result.get("success"):
                logger.warning(
                    f"Failed to persist assistant message for {conversation_id}: {assistant_result.get('error')}"
                )
        except Exception as exc:
            logger.error(f"Failed to persist exchange for {conversation_id}: {exc}")

    async def get_messages(
        self,
        conversation_id: str,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get messages for a conversation with pagination (reverse chronological)."""
        try:
            # Verify conversation exists and belongs to user
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return {
                    "success": False,
                    "error": "Conversation not found",
                    "messages": [],
                    "total": 0
                }
            
            # Get messages ordered by newest first
            stmt = select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(limit).offset(offset)
            
            result = await self.session.execute(stmt)
            messages = result.scalars().all()
            
            # Total count
            count_stmt = select(Message).where(Message.conversation_id == conversation_id)
            count_result = await self.session.execute(count_stmt)
            total = len(count_result.scalars().all())
            
            logger.info(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
            
            return {
                "success": True,
                "conversation": self._serialize_conversation(conversation),
                "total": total,
                "limit": limit,
                "offset": offset,
                "messages": [self._serialize_message(m) for m in messages]
            }
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "messages": [],
                "total": 0
            }

    async def get_conversation_context(
        self,
        conversation_id: str,
        user_id: int,
        last_n: int = 6,
    ) -> Dict[str, Any]:
        """
        Get the last N messages for LLM context window.
        Returns messages in chronological order (oldest first) for proper context.
        """
        try:
            # Verify conversation exists and belongs to user
            conversation = await self.get_conversation(conversation_id, user_id)
            if not conversation:
                logger.warning(f"Conversation not found: {conversation_id}")
                return {
                    "success": False,
                    "error": "Conversation not found",
                    "context": [],
                    "conversation_id": conversation_id
                }
            
            # Get last N messages (newest first, then reverse)
            stmt = select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.desc()).limit(last_n)
            
            result = await self.session.execute(stmt)
            messages = result.scalars().all()
            
            # Reverse to get chronological order for LLM
            messages = list(reversed(messages))
            
            context = [
                {
                    "id": m.id,
                    "role": m.role.value,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ]
            
            logger.info(f"Retrieved context with {len(context)} messages for conversation {conversation_id}")
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "context": context,
                "message_count": len(context)
            }
        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "context": [],
                "conversation_id": conversation_id
            }
