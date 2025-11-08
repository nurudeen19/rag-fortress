"""
Department model for organizational units.

Stores basic department information for organizational tracking and access control.
"""
from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Department(Base):
    """
    Organizational department/unit.
    
    Stores basic department information only.
    Access control is managed via UserPermission model.
    """
    
    __tablename__ = "departments"
    
    # Core identifiers
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Department information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Department head (manager)
    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    manager: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[manager_id],
        backref="managed_department"
    )
    
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="department",
        foreign_keys="User.department_id"
    )
    
    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}', code='{self.code}')>"
