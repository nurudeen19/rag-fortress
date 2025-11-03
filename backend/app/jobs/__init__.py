"""
Simple background task tracking for document ingestion.
"""

from enum import Enum


class IngestionStatus(str, Enum):
    """Status of background ingestion task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
