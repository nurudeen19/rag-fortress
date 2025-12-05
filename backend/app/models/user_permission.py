"""
UserPermission model for managing access control.

Defines user security levels at organization-wide and department-specific levels.
Enables granular access control for files and resources.
"""
from sqlalchemy import String, Integer, ForeignKey, Boolean, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from enum import Enum
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.department import Department
    from app.models.permission_override import PermissionOverride


class PermissionLevel(int, Enum):
    """
    Permission/clearance levels for access control.
    
    Higher number = higher clearance level
    Used for comparing against security tiers
    """
    GENERAL = 1                    # Open company-wide
    RESTRICTED = 2                  # Managerial data access
    CONFIDENTIAL = 3                # Confidential information
    HIGHLY_CONFIDENTIAL = 4         # Sensitive management access


class UserPermission(Base):
    """
    User permission/clearance levels.
    
    Stores two levels of permissions:
    1. org_level_permission - Organization-wide clearance
    2. department_level_permission - Department-specific clearance
    
    A user's effective access is the maximum of their org-wide and department permissions.
    """
    
    __tablename__ = "user_permissions"
    
    # Core identifiers
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Organization-wide permission level
    org_level_permission: Mapped[PermissionLevel] = mapped_column(
        Integer,
        default=PermissionLevel.GENERAL,
        nullable=False
    )
    
    # Department-specific permission level
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    department_level_permission: Mapped[Optional[PermissionLevel]] = mapped_column(
        Integer,
        nullable=True
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="permission",
        foreign_keys=[user_id]
    )
    
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        foreign_keys=[department_id]
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_user_permission_org_level", "org_level_permission"),
        Index("idx_user_permission_dept_level", "department_id", "department_level_permission"),
        Index("idx_user_permission_is_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<UserPermission(user_id={self.user_id}, "
            f"org_level={self.org_level_permission}, "
            f"dept_level={self.department_level_permission})>"
        )
    
    # Permission methods
    
    def get_effective_permission(self) -> int:
        """
        Get the effective permission level considering overrides.
        
        Priority order:
        1. Active overrides (highest override level takes priority)
        2. Department-level permission
        3. Organization-wide permission
        
        Returns:
            Highest permission level the user currently has
        """
        levels = [self.org_level_permission.value]
        
        if self.department_level_permission:
            levels.append(self.department_level_permission.value)
        
        # Add any active overrides (from user's overrides, not user_permission)
        if self.user and self.user.permission_overrides:
            for override in self.user.get_active_overrides():
                levels.append(override.override_permission_level)
        
        return max(levels) if levels else self.org_level_permission.value
    
    def get_active_overrides(self) -> list["PermissionOverride"]:
        """
        Get all active, non-expired overrides for this user.
        
        Returns:
            List of valid PermissionOverride objects
            
        Example:
            for override in permission.get_active_overrides():
                print(f"Override: {override.reason}, expires in {override.days_remaining()} days")
        """
        from datetime import timezone
        
        if not self.user:
            return []
        
        return self.user.get_active_overrides()
    
    def has_active_override(
        self,
        override_type: Optional[str] = None,
        department_id: Optional[int] = None,
    ) -> bool:
        """
        Check if user has any active overrides (optionally filtered).
        
        Args:
            override_type: Filter by override type ('org_wide' or 'department')
            department_id: Filter by department (only for DEPARTMENT overrides)
            
        Returns:
            True if matching active override exists
            
        Example:
            if permission.has_active_override(override_type='org_wide'):
                print("User has org-wide override")
            
            if permission.has_active_override(override_type='department', department_id=3):
                print("User has override for department 3")
        """
        for override in self.get_active_overrides():
            if override_type and override.override_type != override_type:
                continue
            if department_id and override.department_id != department_id:
                continue
            return True
        
        return False
    
    def get_override_for_level(
        self,
        target_level: int,
        override_type: str,
    ) -> Optional["PermissionOverride"]:
        """
        Get first active override that meets or exceeds target level.
        
        Args:
            target_level: Permission level to check
            override_type: Type of override to look for
            
        Returns:
            PermissionOverride if found, None otherwise
        """
        for override in self.get_active_overrides():
            if (
                override.override_type == override_type
                and override.override_permission_level >= target_level
            ):
                return override
        
        return None
    
    def can_access_security_level(self, required_level: int) -> bool:
        """
        Check if user can access a resource with given security level.
        
        Args:
            required_level: SecurityLevel value required for access
            
        Returns:
            True if user's permission >= required level
        """
        return self.get_effective_permission() >= required_level
    
    def has_org_level(self, level: int) -> bool:
        """Check if user has specific org-wide permission level."""
        return self.org_level_permission.value >= level
    
    def has_department_level(self, level: int) -> bool:
        """Check if user has specific department-level permission."""
        if not self.department_level_permission:
            return False
        return self.department_level_permission.value >= level
