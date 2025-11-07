"""
UserProfile model for extended user information.
"""
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(Base):
    """Extended user profile information separated from core user data."""
    
    __tablename__ = "user_profiles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    about: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
        
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
        foreign_keys=[user_id],
    )
    
    __table_args__ = (
        Index("idx_user_profile_user_id", "user_id"),
    )
    
    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, job_title='{self.job_title}')>"
