"""Service layer for Conversation and Message CRUD operations."""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import uuid

from app.models.conversation import Conversation, ConversationCategory
from app.models.message import Message, MessageRole
from app.core import get_logger

logger = get_logger(__name__)


class ConversationService:
    """Provides CRUD operations for conversations and messages."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== Conversation Operations ====================

    async def create_conversation(
        self,
        user_id: int,
        title: str = "New Conversation",
        category: ConversationCategory = ConversationCategory.GENERAL,
    ) -> Conversation:
        """Create a new conversation for a user."""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            category=category,
            message_count=0,
            last_message_at=datetime.now(timezone.utc),
        )
        self.session.add(conversation)
        await self.session.flush()
        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation

    async def get_conversation(
        self, 
        conversation_id: str, 
        user_id: int
    ) -> Optional[Conversation]:
        """Get a conversation by ID, ensuring it belongs to the user."""
        stmt = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_conversations(
        self,
        user_id: int,
        category: Optional[ConversationCategory] = None,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Conversation], int]:
        """List all conversations for a user with pagination."""
        stmt = select(Conversation).where(Conversation.user_id == user_id)
        
        if not include_deleted:
            stmt = stmt.where(Conversation.is_deleted == False)
        
        if category:
            stmt = stmt.where(Conversation.category == category)
        
        # Order by most recent activity
        stmt = stmt.order_by(Conversation.last_message_at.desc())
        
        # Count total (without pagination)
        count_stmt = select(Conversation).where(Conversation.user_id == user_id)
        if not include_deleted:
            count_stmt = count_stmt.where(Conversation.is_deleted == False)
        if category:
            count_stmt = count_stmt.where(Conversation.category == category)
        
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.scalars().all())
        
        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        conversations = result.scalars().all()
        
        return list(conversations), total

    async def update_conversation(
        self,
        conversation_id: str,
        user_id: int,
        title: Optional[str] = None,
        category: Optional[ConversationCategory] = None,
    ) -> Optional[Conversation]:
        """Update conversation metadata."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        if title is not None:
            conversation.title = title
        if category is not None:
            conversation.category = category
        
        await self.session.flush()
        logger.info(f"Updated conversation {conversation_id}")
        return conversation

    async def soft_delete_conversation(
        self, 
        conversation_id: str, 
        user_id: int
    ) -> bool:
        """Soft delete a conversation."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False
        
        conversation.is_deleted = True
        conversation.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        logger.info(f"Soft deleted conversation {conversation_id}")
        return True

    # ==================== Message Operations ====================

    async def add_message(
        self,
        conversation_id: str,
        user_id: int,
        role: MessageRole,
        content: str,
        token_count: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Optional[Message]:
        """Add a message to a conversation and update denormalized fields."""
        # Verify conversation exists and belongs to user
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found for user {user_id}")
            return None
        
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
        logger.info(f"Added {role} message to conversation {conversation_id}")
        return message

    async def get_messages(
        self,
        conversation_id: str,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Message], int]:
        """Get messages for a conversation with pagination (reverse chronological)."""
        # Verify conversation exists and belongs to user
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return [], 0
        
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
        
        return list(messages), total

    async def get_conversation_context(
        self,
        conversation_id: str,
        user_id: int,
        last_n: int = 6,
    ) -> List[Message]:
        """
        Get the last N messages for LLM context window.
        Returns messages in chronological order (oldest first) for proper context.
        """
        # Verify conversation exists and belongs to user
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return []
        
        # Get last N messages (newest first, then reverse)
        stmt = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(last_n)
        
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        
        # Reverse to get chronological order for LLM
        return list(reversed(messages))
