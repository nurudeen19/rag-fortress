"""
Conversation model for chat history management.

This model represents a conversation/chat session between a user and the AI assistant.
"""
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
import uuid
import enum
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.message import Message


class ConversationCategory(str, enum.Enum):
    """Categories for organizing conversations."""
    GENERAL = "GENERAL"
    RESEARCH = "RESEARCH"
    SUPPORT = "SUPPORT"
    ANALYSIS = "ANALYSIS"


class Conversation(Base):
    """
    Conversation model representing a chat session.
    
    This is the parent table that stores conversation metadata and summary information.
    Actual messages are stored in the Message model (child table).
    """
    
    __tablename__ = "conversations"
    
    # Primary key (stored as CHAR(36) for MySQL compatibility)
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # Foreign key to user
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Conversation metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        SQLEnum(ConversationCategory),
        default=ConversationCategory.GENERAL,
        nullable=False
    )
    
    # Denormalized fields for performance (avoid joins for list queries)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Soft delete for data retention
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_conv_user_updated', 'user_id', 'last_message_at'),
        Index('idx_conv_user_deleted', 'user_id', 'is_deleted'),
    )
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title}, user_id={self.user_id})>"

