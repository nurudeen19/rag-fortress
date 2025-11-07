"""
User management models for authentication and user data.

This module contains models for users, roles, and permissions.
"""
from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UniqueConstraint, Index
import enum
from app.models.base import Base


class UserRole(str, enum.Enum):
    """Enumeration of user roles."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # User identification
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Password (should be hashed)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # User profile
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        cascade="save-update, merge",
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_user_is_active", "is_active"),
        Index("idx_user_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)


class Role(Base):
    """Role model for permission management."""
    
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Role name (e.g., "admin", "user", "viewer")
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Role description
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Whether this role is a system role (immutable)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
        cascade="save-update, merge",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        cascade="save-update, merge",
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"


class Permission(Base):
    """Permission model for fine-grained access control."""
    
    __tablename__ = "permissions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Permission code (e.g., "document:create", "user:delete")
    code: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Permission description
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Resource being protected (e.g., "document", "user")
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Action being performed (e.g., "create", "read", "update", "delete")
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        cascade="save-update, merge",
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_permission_resource_action", "resource", "action"),
    )
    
    def __repr__(self) -> str:
        return f"<Permission(code='{self.code}', resource='{self.resource}', action='{self.action}')>"


# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)
