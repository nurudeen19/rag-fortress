"""
Message model for storing individual messages in conversations.

This model represents individual messages (user queries and AI responses) within a conversation.
Messages are encrypted at rest using HKDF-derived keys from the master encryption key.
"""
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index, Enum as SQLEnum, JSON, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from typing import Optional, Dict, Any, TYPE_CHECKING
import uuid
import enum
from app.models.base import Base
from app.utils.encryption import (
    encrypt_conversation_message,
    decrypt_conversation_message,
    EncryptionError,
    DecryptionError
)
from app.core import get_logger

if TYPE_CHECKING:
    from app.models.conversation import Conversation

logger = get_logger(__name__)


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
    
    Security:
    - Message content is encrypted at rest in the database
    - Uses HKDF-derived keys from master encryption key
    - Encryption happens automatically on insert/update via SQLAlchemy events
    - Decryption happens lazily when accessing the content property
    """
    
    __tablename__ = "messages"
    __allow_unmapped__ = True  # Allow unmapped instance attributes for encryption cache
    
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
    
    # Message content - stored encrypted in DB with version prefix (e.g., "v1:gAAAAAB...")
    role: Mapped[str] = mapped_column(
        SQLEnum(MessageRole, native_enum=False),
        nullable=False
    )
    _content: Mapped[str] = mapped_column("content", Text, nullable=False)
    
    # Internal cache for decrypted content (not persisted to DB)
    # These are unmapped instance attributes (see __allow_unmapped__ above)
    _decrypted_content: Optional[str] = None
    _content_dirty: bool = False  # Track if content needs encryption before save
    
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
    
    # Property for transparent encryption/decryption
    @property
    def content(self) -> str:
        """
        Get decrypted message content.
        
        Lazily decrypts content from database on first access.
        Subsequent accesses use cached decrypted value.
        """
        if self._decrypted_content is None and self._content:
            try:
                self._decrypted_content = decrypt_conversation_message(self._content)
            except (DecryptionError, ValueError) as e:
                # If decryption fails, content might be unencrypted (legacy data)
                logger.error(
                    f"Failed to decrypt message {self.id}: {type(e).__name__}: {str(e)}. "
                    f"Data might be unencrypted (legacy format). Using raw content.",
                    exc_info=True
                )
                self._decrypted_content = self._content
        
        return self._decrypted_content or ""
    
    @content.setter
    def content(self, value: str):
        """
        Set message content (will be encrypted before saving to DB).
        
        Stores plaintext in memory cache and marks for encryption on next flush.
        """
        self._decrypted_content = value
        self._content_dirty = True
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_msg_conv_created', 'conversation_id', 'created_at'),
        Index('idx_msg_role', 'role'),
    )
    
    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id}, content={preview})>"


# SQLAlchemy event listeners for automatic encryption
@event.listens_for(Message, "before_insert")
@event.listens_for(Message, "before_update")
def encrypt_message_content(mapper, connection, target: Message):
    """
    Automatically encrypt message content before insert/update.
    
    This event listener ensures all messages are encrypted before
    being written to the database.
    """
    # Only encrypt if content has been modified
    if target._content_dirty and target._decrypted_content is not None:
        try:
            target._content = encrypt_conversation_message(target._decrypted_content)
            target._content_dirty = False
            logger.debug(f"Encrypted message {target.id} content before {mapper.class_.__name__} save")
        except EncryptionError as e:
            error_msg = f"Failed to encrypt message {target.id} before save: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise EncryptionError(error_msg) from e


@event.listens_for(Message, "load")
def reset_encryption_state(target: Message, context):
    """
    Reset encryption state when loading from database.
    
    This ensures decryption happens lazily on first access.
    """
    target._decrypted_content = None
    target._content_dirty = False

