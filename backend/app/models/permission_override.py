"""Permission override model for temporary elevated access with expiry dates.

This module provides a mechanism to grant temporary elevated permissions to users
for specific assignments, with automatic expiration. Overrides can be organization-wide
or department-specific, with audit trails and reason tracking.

Example:
    Grant employee elevated access for 2-week special project:
    
    override = PermissionOverride(
        user_id=42,
        override_type=OverrideType.DEPARTMENT,
        department_id=3,
        override_permission_level=PermissionLevel.CONFIDENTIAL,
        reason="Temporary access for Q4 audit project",
        valid_from=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc) + timedelta(days=14),
        created_by_id=admin_user_id
    )
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    and_,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class OverrideType(str, Enum):
    """Type of permission override.

    Attributes:
        ORG_WIDE: Override applies to organization-wide permission level
        DEPARTMENT: Override applies to department-specific permission level
    """

    ORG_WIDE = "org_wide"
    DEPARTMENT = "department"


class PermissionOverride(Base):
    """Temporary elevated permission override with expiry date.

    Allows granting users temporary elevated permissions for special assignments
    or projects, with automatic expiration after the valid_until date.

    Attributes:
        id: Unique override ID
        user_id: User this override applies to (FK to users)
        override_type: Type of override (ORG_WIDE or DEPARTMENT)
        department_id: Department for DEPARTMENT overrides (nullable)
        override_permission_level: Elevated permission level during override period
        reason: Business justification for the override
        valid_from: Start datetime of the override
        valid_until: End datetime of the override (auto-expires after this)
        created_by_id: User who created this override (audit trail)
        is_active: Whether override is currently active (can be manually revoked)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "permission_overrides"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    override_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    override_permission_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    valid_from: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
    )

    valid_until: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="permission_overrides",
    )

    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_id],
        uselist=False,
    )

    # Composite indexes for efficient queries
    __table_args__ = (
        Index(
            "ix_permission_overrides_user_active",
            "user_id",
            "is_active",
        ),
        Index(
            "ix_permission_overrides_expiry",
            "valid_until",
            "is_active",
        ),
        Index(
            "ix_permission_overrides_user_type",
            "user_id",
            "override_type",
        ),
        Index(
            "ix_permission_overrides_dept_type",
            "department_id",
            "override_type",
        ),
    )

    def is_valid(self) -> bool:
        """Check if override is currently valid.

        Returns:
            True if override is active and within valid time window, False otherwise

        Example:
            if override.is_valid():
                # Use override permission
            else:
                # Override has expired or been revoked
        """
        now = datetime.now(timezone.utc)
        return (
            self.is_active
            and self.valid_from <= now <= self.valid_until
        )

    def is_expired(self) -> bool:
        """Check if override has passed its expiry date.

        Returns:
            True if current time is past valid_until, False otherwise
        """
        return datetime.now(timezone.utc) > self.valid_until

    def days_remaining(self) -> int:
        """Calculate days remaining until expiry.

        Returns:
            Number of days until valid_until (0 if expired, can be negative)

        Example:
            days = override.days_remaining()
            if days <= 3:
                # Alert: override expiring soon
        """
        remaining = self.valid_until - datetime.now(timezone.utc)
        return remaining.days

    def revoke(self) -> None:
        """Manually revoke this override.

        Sets is_active to False, immediately deactivating the override.

        Example:
            override.revoke()
            await db.commit()
        """
        self.is_active = False

    def __repr__(self) -> str:
        """String representation of the override."""
        status = "valid" if self.is_valid() else "expired"
        return (
            f"<PermissionOverride("
            f"user_id={self.user_id}, "
            f"type={self.override_type}, "
            f"level={self.override_permission_level}, "
            f"status={status}"
            f")>"
        )
