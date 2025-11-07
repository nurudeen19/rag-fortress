"""
UserInvitation model for tracking user invitations.
"""
from sqlalchemy import String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserInvitation(Base):
    """Track user invitations sent by admins to join the platform."""
    
    __tablename__ = "user_invitations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    invited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    invitation_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    invited_by: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="invitations_sent",
        foreign_keys=[invited_by_id],
    )
    
    __table_args__ = (
        Index("idx_invitation_email", "email"),
        Index("idx_invitation_token", "token"),
        Index("idx_invitation_status", "status"),
        Index("idx_invitation_expires_at", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<UserInvitation(id={self.id}, email='{self.email}', status='{self.status}')>"
    
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if invitation is still valid for acceptance."""
        return self.status == "pending" and not self.is_expired()
