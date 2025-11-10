"""
FileUpload model for tracking files through the ingestion lifecycle.

Manages file uploads, approvals, processing status, and security controls.
Supports complete lifecycle management from upload through storage.
Includes department-level file association for access control.
"""
from sqlalchemy import String, Boolean, Text, ForeignKey, DateTime, Integer, Index, Enum as SQLEnum, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from enum import Enum
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.department import Department


class FileStatus(str, Enum):
    """File processing status lifecycle."""
    PENDING = "pending"           # Uploaded, awaiting review
    APPROVED = "approved"         # Approved for processing
    REJECTED = "rejected"         # Rejected by approver
    PROCESSING = "processing"     # Currently being ingested
    PROCESSED = "processed"       # Successfully ingested and stored
    FAILED = "failed"             # Processing failed
    DELETED = "deleted"           # Marked for deletion


class SecurityLevel(int, Enum):
    """
    File security classification (numbered tier structure).
    
    Higher number = more restricted
    """
    GENERAL = 1                    # No restrictions (tier 1)
    RESTRICTED = 2                  # Internal use only (tier 2)
    CONFIDENTIAL = 3              # Restricted access (tier 3)
    HIGHLY_CONFIDENTIAL = 4                # Highly restricted (tier 4)


class IntEnumType(TypeDecorator):
    """TypeDecorator to handle Python int enums in SQLAlchemy with integer columns."""
    impl = Integer
    cache_ok = True
    
    def __init__(self, enum_class):
        super().__init__()
        self.enum_class = enum_class
    
    def process_bind_param(self, value, dialect):
        """Convert enum to integer when binding to database."""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value
        return value
    
    def process_result_value(self, value, dialect):
        """Convert integer back to enum when loading from database."""
        if value is None:
            return None
        return self.enum_class(value)


class FileUpload(Base):
    """
    Track uploaded files through the ingestion pipeline.
    
    Lifecycle:
    1. User uploads file → status=PENDING
    2. Admin reviews → status=APPROVED/REJECTED
    3. System processes → status=PROCESSING
    4. Results in vector store → status=PROCESSED or FAILED
    5. Optional cleanup → status=DELETED
    """
    
    __tablename__ = "file_uploads"
    
    # Core identifiers
    id: Mapped[int] = mapped_column(primary_key=True)
    upload_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # File information
    file_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Bytes
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # File hash for deduplication and integrity
    file_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # SHA-256
    
    # User tracking
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Department association and access control
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    is_department_only: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    # Approval workflow
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approval_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Processing metadata
    file_purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Why this file is being uploaded
    field_selection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of fields to extract
    extraction_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON extraction rules
    
    # Security
    security_level: Mapped[SecurityLevel] = mapped_column(
        IntEnumType(SecurityLevel),
        default=SecurityLevel.GENERAL,
        nullable=False,
        index=True
    )
    
    # Processing tracking
    status: Mapped[FileStatus] = mapped_column(
        SQLEnum(FileStatus, native_enum=False),
        default=FileStatus.PENDING,
        nullable=False,
        index=True
    )
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Processing results
    chunks_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Number of chunks stored
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Error details if FAILED
    
    # Performance & monitoring
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Time to process (ms)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Number of retry attempts
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # Max retries allowed
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Data retention
    retention_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)  # Auto-delete date
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Relationships
    uploaded_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[uploaded_by_id],
        backref="uploaded_files"
    )
    approved_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by_id],
        backref="approved_files"
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        foreign_keys=[department_id],
        backref="files"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_file_upload_status_created", "status", "created_at"),
        Index("idx_file_upload_user_status", "uploaded_by_id", "status"),
        Index("idx_file_upload_security_level", "security_level"),
        Index("idx_file_upload_is_processed", "is_processed"),
        Index("idx_file_upload_retention", "retention_until", "is_archived"),
        Index("idx_file_upload_department_access", "department_id", "is_department_only"),
    )
    
    def __repr__(self) -> str:
        scope = "dept-only" if self.is_department_only else "org-wide"
        return f"<FileUpload(id={self.id}, file_name='{self.file_name}', status={self.status.value}, scope={scope})>"
    
    # Lifecycle methods
    
    def mark_approved(self, approved_by_user_id: int, reason: str = "") -> None:
        """Mark file as approved for processing."""
        self.status = FileStatus.APPROVED
        self.approved_by_id = approved_by_user_id
        self.approval_reason = reason
        self.approved_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_rejected(self, rejected_by_user_id: int, reason: str = "") -> None:
        """Mark file as rejected."""
        self.status = FileStatus.REJECTED
        self.approved_by_id = rejected_by_user_id
        self.approval_reason = reason
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_processing(self) -> None:
        """Mark file as currently being processed."""
        self.status = FileStatus.PROCESSING
        self.processing_started_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_processed(self, chunks_created: int, processing_time_ms: int) -> None:
        """Mark file as successfully processed."""
        self.status = FileStatus.PROCESSED
        self.is_processed = True
        self.chunks_created = chunks_created
        self.processing_time_ms = processing_time_ms
        self.processing_completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.retry_count = 0  # Reset retry count on success
    
    def mark_failed(self, error: str) -> None:
        """Mark file processing as failed."""
        self.processing_error = error
        self.retry_count += 1
        self.updated_at = datetime.now(timezone.utc)
        self.processing_completed_at = datetime.now(timezone.utc)
        
        # If max retries exceeded, mark as failed permanently
        if self.retry_count >= self.max_retries:
            self.status = FileStatus.FAILED
        else:
            self.status = FileStatus.PENDING
    
    def can_retry(self) -> bool:
        """Check if file can be retried."""
        return self.retry_count < self.max_retries and self.status in (FileStatus.PENDING, FileStatus.FAILED)
    
    def is_awaiting_approval(self) -> bool:
        """Check if file is awaiting approval."""
        return self.status == FileStatus.PENDING and self.approved_by_id is None
    
    def is_approved(self) -> bool:
        """Check if file has been approved."""
        return self.status == FileStatus.APPROVED
    
    def is_failed(self) -> bool:
        """Check if file processing failed."""
        return self.status == FileStatus.FAILED
    
    def is_ready_to_delete(self) -> bool:
        """Check if file is ready for deletion based on retention policy."""
        if not self.retention_until:
            return False
        return datetime.now(timezone.utc) > self.retention_until
    
    def is_department_accessible(self, user_department_id: Optional[int]) -> bool:
        """
        Check if user from a specific department can access this file.
        
        Args:
            user_department_id: Department ID of the user (None if org-wide access)
            
        Returns:
            True if user can access file based on department restrictions
        """
        # If file is department-only
        if self.is_department_only:
            # User must be from the same department
            if not self.department_id:
                return False  # File is restricted but no department set (invalid state)
            return user_department_id == self.department_id
        
        # If file is organization-wide, anyone can access
        return True
    
    def set_department_only(self, department_id: int) -> None:
        """
        Mark file as accessible only to specific department.
        
        Args:
            department_id: Department ID to restrict access to
        """
        self.department_id = department_id
        self.is_department_only = True
        self.updated_at = datetime.now(timezone.utc)
    
    def set_organization_wide(self) -> None:
        """Mark file as accessible to entire organization."""
        self.is_department_only = False
        self.updated_at = datetime.now(timezone.utc)
        # Note: department_id can remain set for reference but won't be used for access control
