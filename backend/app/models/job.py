"""Job model for tracking async tasks and background jobs."""

from sqlalchemy import String, Text, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from app.models.base import Base


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    """Types of jobs."""
    FILE_INGESTION = "file_ingestion"
    EMBEDDING_GENERATION = "embedding_generation"
    VECTOR_STORAGE = "vector_storage"
    CLEANUP = "cleanup"
    PASSWORD_RESET_EMAIL = "password_reset_email"


class Job(Base):
    """Track async jobs for processing and recovery on restart."""
    
    __tablename__ = "jobs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Job identification
    job_type: Mapped[str] = mapped_column(SQLEnum(JobType), nullable=False, index=True)
    status: Mapped[str] = mapped_column(SQLEnum(JobStatus), nullable=False, index=True, default=JobStatus.PENDING)
    
    # Tracking
    reference_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Job metadata
    payload: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string for storing job parameters
    result: Mapped[str] = mapped_column(Text, nullable=True)   # JSON string for storing results
    error: Mapped[str] = mapped_column(Text, nullable=True)    # Error message if job failed
    
    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
