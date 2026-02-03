"""
Password reset token model for tracking token state and expiry.
"""

from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.models.base import Base


class PasswordResetToken(Base):
    """Store password reset tokens with email, expiry, and status."""
    
    __tablename__ = "password_reset_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # User and email info
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Token data
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    
    # Token lifecycle
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Expiry
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Composite index for efficient lookups
    __table_args__ = (
        Index("idx_token_email_valid", "token", "email", "is_used", "expires_at"),
    )
    
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        now = datetime.now(timezone.utc)
        return (
            not self.is_used and
            now <= self.expires_at
        )
    
    def is_expired(self) -> bool:
        """Check if token has expired."""
        now = datetime.now(timezone.utc)
        return now > self.expires_at
