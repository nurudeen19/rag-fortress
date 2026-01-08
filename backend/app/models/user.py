"""
Core user model for authentication and user data.
"""
from sqlalchemy import String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile
    from app.models.user_invitation import UserInvitation
    from app.models.auth import Role
    from app.models.department import Department
    from app.models.user_permission import UserPermission
    from app.models.permission_override import PermissionOverride
    from app.models.conversation import Conversation


class User(Base):
    """User model for authentication and core user data."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Organizational
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    suspension_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="users",
        foreign_keys=[department_id],
    )
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        cascade="save-update, merge",
    )
    invitations_sent: Mapped[list["UserInvitation"]] = relationship(
        "UserInvitation",
        back_populates="invited_by",
        cascade="all, delete-orphan",
    )
    user_permission: Mapped[Optional["UserPermission"]] = relationship(
        "UserPermission",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="UserPermission.user_id"
    )
    
    permission_overrides: Mapped[list["PermissionOverride"]] = relationship(
        "PermissionOverride",
        back_populates="user",
        foreign_keys="PermissionOverride.user_id",
        cascade="all, delete-orphan"
    )
    
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
    
    @property
    def full_name(self) -> str:
        """Get full name from first and last name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_active_overrides(self) -> list["PermissionOverride"]:
        """Get all active, non-expired overrides for this user."""
        now = datetime.now(timezone.utc)

        def _as_aware(dt: datetime) -> datetime:
            # Ensure datetime comparisons are always timezone-aware (UTC)
            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        active = []
        
        for override in self.permission_overrides:
            if (
                override.is_active
                and _as_aware(override.valid_from) <= now <= _as_aware(override.valid_until)
            ):
                active.append(override)
        
        return active
    
    def has_role(self, role_name: str) -> bool:
        return any(role.name == role_name for role in self.roles)
    
    def is_account_locked(self) -> bool:
        return not self.is_active or self.is_suspended
    
    def suspend_account(self, reason: str = "") -> None:
        self.is_suspended = True
        self.suspension_reason = reason
        self.suspended_at = datetime.now(timezone.utc)
    
    def unsuspend_account(self) -> None:
        self.is_suspended = False
        self.suspension_reason = None
        self.suspended_at = None

