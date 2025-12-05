"""Notification model for in-app user alerts."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Notification(Base):
    """Stores user notifications (e.g., file rejection, approval, system messages)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    # message content (short text, allow up to ~2KB)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # optional file relationship for file-specific events
    related_file_id: Mapped[Optional[int]] = mapped_column(ForeignKey("file_uploads.id", ondelete="CASCADE"), nullable=True, index=True)

    # notification type string (e.g., 'file_rejected', 'file_approved') for UI grouping
    notification_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    # read tracking
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # relationships (optional backrefs for convenience)
    user = relationship("User", backref="notifications")
    related_file = relationship("FileUpload", backref="notifications")

    __table_args__ = (
        Index("idx_notifications_user_unread", "user_id", "is_read"),
        Index("idx_notifications_type_created", "notification_type", "created_at"),
    )

    def mark_read(self) -> None:
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notification(id={self.id}, user_id={self.user_id}, read={self.is_read}, type={self.notification_type})>"
