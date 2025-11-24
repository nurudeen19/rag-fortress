"""
Activity Logging Service

Tracks user access attempts to documents, especially unauthorized access.
Provides audit trail for compliance and security monitoring.

Usage:
    logger = get_activity_logger()
    await logger.log_document_access(
        user_id=user.id,
        document_id=doc.id,
        access_granted=False,
        user_clearance=PermissionLevel.RESTRICTED,
        doc_security_level=PermissionLevel.HIGHLY_CONFIDENTIAL
    )
"""

import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user_permission import PermissionLevel

logger = logging.getLogger(__name__)


class DocumentAccessLog:
    """
    Represents a document access attempt.
    
    Note: This is a simple in-memory representation.
    TODO: Create actual database model for persistence.
    """
    def __init__(
        self,
        user_id: int,
        document_id: int,
        document_name: str,
        access_granted: bool,
        user_clearance: PermissionLevel,
        doc_security_level: PermissionLevel,
        reason: Optional[str] = None,
        query: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.user_id = user_id
        self.document_id = document_id
        self.document_name = document_name
        self.access_granted = access_granted
        self.user_clearance = user_clearance
        self.doc_security_level = doc_security_level
        self.reason = reason
        self.query = query
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "user_id": self.user_id,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "access_granted": self.access_granted,
            "user_clearance": self.user_clearance.name if self.user_clearance else None,
            "doc_security_level": self.doc_security_level.name if self.doc_security_level else None,
            "reason": self.reason,
            "query": self.query[:100] if self.query else None,  # Truncate for logging
            "timestamp": self.timestamp.isoformat()
        }


class ActivityLogger:
    """
    Logs user activity for audit trail and compliance.
    
    Current Implementation: Logs to application logger
    Future Enhancement: Persist to database table
    
    Use Cases:
    1. Track unauthorized access attempts
    2. Compliance reporting (who accessed what when)
    3. User behavior analytics
    4. Security incident investigation
    5. Access request workflows (user discovers restricted content)
    """
    
    def __init__(self):
        self._memory_logs: List[DocumentAccessLog] = []
        self._max_memory_logs = 1000  # Keep last 1000 logs in memory
    
    async def log_document_access(
        self,
        user_id: int,
        document_id: int,
        document_name: str,
        access_granted: bool,
        user_clearance: PermissionLevel,
        doc_security_level: PermissionLevel,
        reason: Optional[str] = None,
        query: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ):
        """
        Log a document access attempt.
        
        Args:
            user_id: ID of user attempting access
            document_id: ID of document being accessed
            document_name: Name of document (for readability)
            access_granted: Whether access was granted
            user_clearance: User's effective permission level
            doc_security_level: Document's security level
            reason: Optional reason for denial
            query: Optional user query that triggered access
            db: Optional database session for persistence
        """
        
        access_log = DocumentAccessLog(
            user_id=user_id,
            document_id=document_id,
            document_name=document_name,
            access_granted=access_granted,
            user_clearance=user_clearance,
            doc_security_level=doc_security_level,
            reason=reason,
            query=query
        )
        
        # Log to application logger
        log_level = logging.WARNING if not access_granted else logging.INFO
        log_message = (
            f"Document access: user_id={user_id}, doc_id={document_id}, "
            f"granted={access_granted}, user_clearance={user_clearance.name}, "
            f"doc_level={doc_security_level.name}"
        )
        
        if not access_granted:
            log_message += f", reason={reason}"
        
        logger.log(log_level, log_message)
        
        # Store in memory (for quick retrieval)
        self._memory_logs.append(access_log)
        if len(self._memory_logs) > self._max_memory_logs:
            self._memory_logs.pop(0)  # Remove oldest
        
        # TODO: Persist to database
        # if db:
        #     await self._persist_to_db(access_log, db)
    
    async def log_bulk_access(
        self,
        user_id: int,
        access_results: List[dict],
        query: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ):
        """
        Log multiple document access attempts at once (e.g., from vector search).
        
        Args:
            user_id: ID of user attempting access
            access_results: List of dicts with keys:
                - document_id, document_name, access_granted,
                - user_clearance, doc_security_level, reason
            query: Optional user query
            db: Optional database session
        """
        for result in access_results:
            await self.log_document_access(
                user_id=user_id,
                document_id=result["document_id"],
                document_name=result["document_name"],
                access_granted=result["access_granted"],
                user_clearance=result["user_clearance"],
                doc_security_level=result["doc_security_level"],
                reason=result.get("reason"),
                query=query,
                db=db
            )
    
    def get_recent_logs(self, limit: int = 100) -> List[DocumentAccessLog]:
        """Get recent access logs from memory."""
        return self._memory_logs[-limit:]
    
    def get_unauthorized_attempts(self, user_id: Optional[int] = None) -> List[DocumentAccessLog]:
        """Get unauthorized access attempts, optionally filtered by user."""
        logs = [log for log in self._memory_logs if not log.access_granted]
        
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]
        
        return logs
    
    def get_user_activity_summary(self, user_id: int) -> dict:
        """
        Get summary of user's access activity.
        
        Returns:
            Dict with keys:
                - total_attempts: Total access attempts
                - granted: Successful access count
                - denied: Denied access count
                - documents_accessed: List of document IDs
                - clearance_violations: Count of attempts above clearance
        """
        user_logs = [log for log in self._memory_logs if log.user_id == user_id]
        
        granted = sum(1 for log in user_logs if log.access_granted)
        denied = sum(1 for log in user_logs if not log.access_granted)
        
        # Clearance violations: attempted to access doc above clearance
        violations = sum(
            1 for log in user_logs
            if not log.access_granted and log.doc_security_level > log.user_clearance
        )
        
        documents = set(log.document_id for log in user_logs)
        
        return {
            "user_id": user_id,
            "total_attempts": len(user_logs),
            "granted": granted,
            "denied": denied,
            "documents_accessed": list(documents),
            "clearance_violations": violations,
            "recent_logs": [log.to_dict() for log in user_logs[-10:]]  # Last 10
        }
    
    # TODO: Database persistence methods
    # async def _persist_to_db(self, access_log: DocumentAccessLog, db: AsyncSession):
    #     """Persist access log to database."""
    #     # Create DocumentAccessLog model in app/models/
    #     # Insert into database with all fields
    #     pass
    # 
    # async def get_access_logs_from_db(
    #     self,
    #     db: AsyncSession,
    #     user_id: Optional[int] = None,
    #     document_id: Optional[int] = None,
    #     start_date: Optional[datetime] = None,
    #     end_date: Optional[datetime] = None,
    #     access_granted: Optional[bool] = None
    # ) -> List[DocumentAccessLog]:
    #     """Query access logs from database with filters."""
    #     pass


# Singleton instance
_activity_logger = None


def get_activity_logger() -> ActivityLogger:
    """
    Get singleton instance of ActivityLogger.
    
    Returns:
        ActivityLogger: Shared logger instance
    """
    global _activity_logger
    if _activity_logger is None:
        _activity_logger = ActivityLogger()
    return _activity_logger
