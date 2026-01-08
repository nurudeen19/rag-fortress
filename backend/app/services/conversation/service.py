"""Service layer for Conversation and Message CRUD operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timezone, timedelta
import uuid
import json

from app.core.cache import get_cache

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.core import get_logger
from app.core.events import get_event_bus
from app.services.query_validator_service import get_query_validator
from app.config.settings import settings

logger = get_logger(__name__)


class ConversationService:
    """Provides CRUD operations for conversations and messages."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache = get_cache()

    # ==================== Helper Methods ====================

    def _estimate_tokens(self, text: str) -> int:
        """Simple token estimation based on word count.
        
        Uses approximation: tokens ≈ words * 1.3
        For accurate token counts, use tiktoken or similar.
        """
        if not text:
            return 0
        return int(len(text.split()) * 1.3)

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
                Conversation.is_deleted.is_(False),
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
                stmt = stmt.where(Conversation.is_deleted.is_(False))
            
            # Order by most recent activity
            stmt = stmt.order_by(Conversation.last_message_at.desc())
            
            # Count total (without pagination)
            count_stmt = select(Conversation).where(Conversation.user_id == user_id)
            if not include_deleted:
                count_stmt = count_stmt.where(Conversation.is_deleted.is_(False))
            
            count_result = await self.session.execute(count_stmt)
            total = len(count_result.scalars().all())
            
            # Apply pagination
            stmt = stmt.limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            conversations = result.scalars().all()
            
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
                    
                    # Emit activity log event (non-blocking)
                    bus = get_event_bus()
                    await bus.emit("activity_log", {
                        "user_id": user_id,
                        "incident_type": "malicious_query_blocked",
                        "severity": "critical",
                        "description": f"Malicious query blocked: {validation['threat_type']}",
                        "details": {
                            "threat_type": validation["threat_type"],
                            "confidence": validation["confidence"],
                            "reason": validation["reason"],
                            "conversation_id": conversation_id
                        },
                        "user_query": content,
                        "threat_type": validation["threat_type"]
                    })
                    
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
                return history
        except Exception as exc:
            logger.warning(f"Failed to read history cache: {exc}")

        # Use configurable history turns from settings (defaults to 3 turns = 6 messages)
        history_turns = settings.CONVERSATION_HISTORY_TURNS
        last_n = history_turns * 2  # Each turn has user + assistant messages
        
        context_result = await self.get_conversation_context(conversation_id, user_id, last_n=last_n)
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
        persist_to_db: bool = False,
        assistant_meta: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Persist the latest exchange to database first, then cache.
        
        Cache is updated AFTER successful DB commit to maintain consistency.
        If DB persistence fails, cache remains untouched.
        """
        # If persistence to DB is requested, do it FIRST
        if persist_to_db and user_id is not None:
            success = await self.save_conversation_exchange(
                conversation_id=conversation_id,
                user_id=user_id,
                user_msg=user_msg,
                assistant_msg=assistant_msg,
                assistant_meta=assistant_meta
            )
            
            # Only update cache if DB persistence succeeded
            if not success:
                logger.error(f"DB persistence failed for {conversation_id}, skipping cache update")
                return
        
        # Update cache (either after successful DB commit or for cache-only updates)
        cache_key = f"conversation:history:{conversation_id}"
        try:
            cached_data = await self.cache.get(cache_key)
            history = json.loads(cached_data) if cached_data else []
        except Exception as exc:
            logger.warning(f"Failed to read history cache before update: {exc}")
            history = []

        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})
        
        # Use configurable history turns from settings
        history_turns = settings.CONVERSATION_HISTORY_TURNS
        max_messages = history_turns * 2  # Each turn has user + assistant messages
        history = history[-max_messages:]

        await self._cache_history(conversation_id, history)
        logger.info(f"Cached exchange for {conversation_id}")

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

    async def save_conversation_exchange(
        self,
        conversation_id: str,
        user_id: int,
        user_msg: str,
        assistant_msg: str,
        assistant_meta: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save both user and assistant messages in a single atomic transaction.
        
        This ensures either both messages are persisted or neither are,
        preventing dangling user messages without assistant responses.
        
        Returns:
            bool: True if both messages were persisted successfully, False otherwise
        """
        try:
            # Create both message objects
            user_message = Message(
                conversation_id=conversation_id,
                user_id=user_id,
                role=MessageRole.USER,
                content=user_msg,
                token_count=self._estimate_tokens(user_msg)
            )
            
            assistant_message = Message(
                conversation_id=conversation_id,
                user_id=user_id,
                role=MessageRole.ASSISTANT,
                content=assistant_msg,
                token_count=self._estimate_tokens(assistant_msg),
                meta=assistant_meta
            )
            
            # Add both to session
            self.session.add(user_message)
            self.session.add(assistant_message)
            
            # Commit in a single transaction
            await self.session.commit()
            
            logger.info(f"Persisted conversation exchange for {conversation_id} in single transaction")
            return True
            
        except Exception as exc:
            logger.error(f"Failed to persist exchange for {conversation_id}: {exc}")
            await self.session.rollback()
            return False

    async def _persist_messages_to_db(
        self,
        conversation_id: str,
        user_id: int,
        user_msg: str,
        assistant_msg: str,
        assistant_meta: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        DEPRECATED: Use save_conversation_exchange() instead for atomic transactions.
        
        This method is kept for backward compatibility but will log a warning.
        """
        logger.warning(
            "Using deprecated _persist_messages_to_db. "
            "Use save_conversation_exchange() for atomic transactions."
        )
        await self.save_conversation_exchange(
            conversation_id=conversation_id,
            user_id=user_id,
            user_msg=user_msg,
            assistant_msg=assistant_msg,
            assistant_meta=assistant_meta
        )

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
