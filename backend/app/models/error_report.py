"""
Error Report model for user-reported issues and errors.

Allows users to report errors they encounter, with optional image attachment.
Admins can view, categorize, and track resolution of reported errors.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base


class ErrorReportStatus(str, enum.Enum):
    """Status of error report."""
    OPEN = "open"              # User submitted, awaiting review
    INVESTIGATING = "investigating"  # Admin is looking into it
    ACKNOWLEDGED = "acknowledged"    # Confirmed issue
    RESOLVED = "resolved"      # Issue fixed
    DUPLICATE = "duplicate"    # Duplicate of another report
    NOT_REPRODUCIBLE = "not_reproducible"  # Could not reproduce
    WONT_FIX = "wont_fix"      # Decided not to fix


class ErrorReportCategory(str, enum.Enum):
    """Category of reported error."""
    LLM_ERROR = "llm_error"          # LLM generation failed
    RETRIEVAL_ERROR = "retrieval_error"  # Document retrieval failed
    VALIDATION_ERROR = "validation_error"  # Input/output validation
    PERFORMANCE = "performance"      # Slow performance
    UI_UX = "ui_ux"                  # User interface issue
    PERMISSIONS = "permissions"      # Access/permission issue
    DATA_ACCURACY = "data_accuracy"  # Wrong information returned
    SYSTEM_ERROR = "system_error"    # General system error
    OTHER = "other"                  # Uncategorized


class ErrorReport(Base):
    """
    User-reported errors and issues.
    
    Allows end users to report problems they encounter, including:
    - Error messages they received
    - Unexpected behavior
    - Performance issues
    - Data accuracy concerns
    
    Admins can then investigate and track resolution.
    """
    
    __tablename__ = "error_reports"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User who reported the error
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", foreign_keys=[user_id])
    
    # Conversation context (optional - link to where error occurred)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    
    # Report content
    title = Column(String(255), nullable=False, index=True)  # "Wrong answer", "Slow response", etc.
    description = Column(Text, nullable=False)  # Detailed description of what happened
    
    # Error categorization (user-provided, can be auto-detected)
    category = Column(SQLEnum(ErrorReportCategory), nullable=False, default=ErrorReportCategory.OTHER, index=True)
    
    # Image attachment
    image_filename = Column(String(255), nullable=True)  # Filename of uploaded image
    image_url = Column(String(512), nullable=True)       # URL to image (if stored externally)
    
    # System context (auto-captured from request)
    user_agent = Column(String(512), nullable=True)  # Browser/client info
    request_context = Column(Text, nullable=True)    # JSON: endpoint, method, timestamp, etc.
    
    # Status tracking
    status = Column(SQLEnum(ErrorReportStatus), nullable=False, default=ErrorReportStatus.OPEN, index=True)
    
    # Admin follow-up
    admin_notes = Column(Text, nullable=True)  # Notes from admin investigation
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Admin assigned
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    
    # Timestamps
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # When resolved
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_error_reports_user_status", "user_id", "status"),
        Index("ix_error_reports_status_category", "status", "category"),
        Index("ix_error_reports_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<ErrorReport(id={self.id}, user_id={self.user_id}, status={self.status}, category={self.category})>"
