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
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.department import Department


class OverrideType(str, Enum):
    """Type of permission override.

    Attributes:
        ORG_WIDE: Override applies to organization-wide permission level
        DEPARTMENT: Override applies to department-specific permission level
    """

    ORG_WIDE = "org_wide"
    DEPARTMENT = "department"


class OverrideStatus(str, Enum):
    """Status of permission override request/approval.
    
    Attributes:
        PENDING: Awaiting approval decision
        APPROVED: Approved and active (or will be active during valid window)
        DENIED: Request denied by approver
        EXPIRED: Override has expired
        REVOKED: Manually revoked before expiry
    """
    
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PermissionOverride(Base):
    """Temporary elevated permission override with request/approval workflow.

    Supports both direct grants (by admins) and user-requested overrides that
    require approval. Includes automatic expiration after the valid_until date.

    Attributes:
        id: Unique override ID
        user_id: User this override applies to (FK to users)
        override_type: Type of override (ORG_WIDE or DEPARTMENT)
        department_id: Department for DEPARTMENT overrides (nullable)
        override_permission_level: Elevated permission level during override period
        reason: Business justification for the override
        valid_from: Start datetime of the override
        valid_until: End datetime of the override (auto-expires after this)
        created_by_id: User who created/requested this override
        is_active: Whether override is currently active (can be manually revoked)
        status: Current status (pending/approved/denied/expired/revoked)
        approver_id: User who approved/denied (nullable until decision)
        approval_notes: Approver's comments on decision
        decided_at: When approval/denial decision was made
        trigger_query: Query that triggered this request (optional)
        trigger_file_id: File that couldn't be accessed (optional)
        auto_escalated: Whether request was auto-escalated to admin
        escalated_at: When auto-escalation occurred
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

    # Duration stored as hours - calculated from user request
    # Valid period is calculated on approval, not creation
    requested_duration_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=24,
    )

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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
    
    # Approval workflow fields
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OverrideStatus.APPROVED.value,  # Direct grants are auto-approved
        index=True,
    )
    
    approver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    approval_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Context fields (what triggered this request)
    trigger_query: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    trigger_file_id: Mapped[Optional[int]] = mapped_column(
        Integer,  # Store file ID without FK constraint (file may be deleted)
        nullable=True,
    )
    
    # Auto-escalation tracking
    auto_escalated: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    escalated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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
    
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approver_id],
        uselist=False,
    )
    
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        foreign_keys=[department_id],
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
        Index(
            "ix_permission_overrides_status_created",
            "status",
            "created_at",
        ),
        Index(
            "ix_permission_overrides_user_status",
            "user_id",
            "status",
        ),
    )

    def is_valid(self) -> bool:
        """Check if override is currently valid.

        Returns:
            True if override is approved, active and within valid time window

        Example:
            if override.is_valid():
                # Use override permission
            else:
                # Override has expired, been revoked, or not approved
        """
        now = datetime.now(timezone.utc)
        return (
            self.status == OverrideStatus.APPROVED.value
            and self.is_active
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

        Sets is_active to False and status to REVOKED.

        Example:
            override.revoke()
            await db.commit()
        """
        self.is_active = False
        self.status = OverrideStatus.REVOKED.value
        self.updated_at = datetime.now(timezone.utc)
    
    def is_pending(self) -> bool:
        """Check if override request is pending approval."""
        return self.status == OverrideStatus.PENDING.value
    
    def is_approved(self) -> bool:
        """Check if override has been approved."""
        return self.status == OverrideStatus.APPROVED.value
    
    def is_denied(self) -> bool:
        """Check if override request was denied."""
        return self.status == OverrideStatus.DENIED.value
    
    def can_be_cancelled(self) -> bool:
        """Check if request can be cancelled by requester."""
        return self.status == OverrideStatus.PENDING.value
    
    def hours_since_created(self) -> float:
        """Calculate hours since override was created/requested."""
        delta = datetime.now(timezone.utc) - self.created_at
        return delta.total_seconds() / 3600
    
    def should_auto_escalate(self, escalation_threshold_hours: int = 24) -> bool:
        """Check if pending request should be auto-escalated to admin.
        
        Args:
            escalation_threshold_hours: Hours before escalation (default 24)
            
        Returns:
            True if pending and past escalation threshold
        """
        return (
            self.is_pending()
            and not self.auto_escalated
            and self.override_type == OverrideType.DEPARTMENT.value
            and self.hours_since_created() >= escalation_threshold_hours
        )

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
