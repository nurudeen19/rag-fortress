"""
Message model for storing individual messages in conversations.

This model represents individual messages (user queries and AI responses) within a conversation.
"""
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from typing import Optional, Dict, Any, TYPE_CHECKING
import uuid
import enum
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class MessageRole(str, enum.Enum):
    """Role types for messages in a conversation."""
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class Message(Base):
    """
    Message model representing individual messages in a conversation.
    
    This is the child table that stores actual message content.
    Each message belongs to a conversation (parent table).
    """
    
    __tablename__ = "messages"
    
    # Primary key (stored as CHAR(36) for MySQL compatibility)
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign key to conversation (stored as CHAR(36) for MySQL compatibility)
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Message content
    role: Mapped[str] = mapped_column(
        SQLEnum(MessageRole),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Optional: Token count for cost tracking
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Optional: Metadata for sources, citations, relevance scores
    # Example: {"sources": [{"document": "file.pdf", "score": 0.95}], "model": "gpt-4"}
    # Using 'meta' instead of 'metadata' to avoid conflict with SQLAlchemy's reserved attribute
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Timestamp for ordering (inherited created_at from Base, but add index)
    # The created_at from Base is already present, we just need to ensure it's indexed
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_msg_conv_created', 'conversation_id', 'created_at'),
        Index('idx_msg_role', 'role'),
    )
    
    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id}, content={preview})>"

