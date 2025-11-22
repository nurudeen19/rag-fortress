"""
Dashboard metrics service - provides admin and user dashboard statistics.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core import get_logger
from app.models.file_upload import FileUpload, FileStatus
from app.models.job import Job, JobStatus
from app.models.notification import Notification
from app.models.user import User


logger = get_logger(__name__)


class DashboardService:
    """Service for fetching dashboard metrics."""
    
    @staticmethod
    async def get_admin_metrics(session: AsyncSession) -> Dict[str, Any]:
        """
        Get admin dashboard metrics.
        
        Returns:
            Dict with:
            - total_documents: Total files in system
            - pending_documents: Documents awaiting approval
            - approved_documents: Documents that are approved
            - total_jobs: Total jobs in queue
            - jobs_processed: Completed jobs
            - jobs_failed: Failed jobs
            - jobs_pending: Pending jobs
            - total_users: Active users
            - total_notifications: All notifications
            - unread_notifications: Unread notifications
            - system_health: System operational status
        """
        metrics = {}
        
        # File metrics
        result = await session.execute(select(func.count(FileUpload.id)))
        metrics["total_documents"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(FileUpload.id)).where(FileUpload.status == FileStatus.PENDING)
        )
        metrics["pending_documents"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(FileUpload.id)).where(FileUpload.status == FileStatus.APPROVED)
        )
        metrics["approved_documents"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(FileUpload.id)).where(FileUpload.status == FileStatus.REJECTED)
        )
        metrics["rejected_documents"] = result.scalar() or 0
        
        # Job metrics
        result = await session.execute(select(func.count(Job.id)))
        metrics["total_jobs"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(Job.id)).where(Job.status == JobStatus.COMPLETED)
        )
        metrics["jobs_processed"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(Job.id)).where(Job.status == JobStatus.FAILED)
        )
        metrics["jobs_failed"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(Job.id)).where(Job.status == JobStatus.PENDING)
        )
        metrics["jobs_pending"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(Job.id)).where(Job.status == JobStatus.PROCESSING)
        )
        metrics["jobs_in_progress"] = result.scalar() or 0
        
        # User metrics
        result = await session.execute(select(func.count(User.id)))
        metrics["total_users"] = result.scalar() or 0
        
        # Notification metrics
        result = await session.execute(select(func.count(Notification.id)))
        metrics["total_notifications"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(Notification.id)).where(Notification.read_at.is_(None))
        )
        metrics["unread_notifications"] = result.scalar() or 0
        
        # System health (basic - can be extended)
        metrics["system_health"] = "healthy"
        
        return metrics
    
    @staticmethod
    async def get_user_metrics(session: AsyncSession, user_id: int) -> Dict[str, Any]:
        """
        Get user dashboard metrics.
        
        Returns:
            Dict with:
            - my_documents: Total documents uploaded by user
            - pending_approval: Documents awaiting approval
            - approved_documents: User's approved documents
            - total_queries: Total queries made by user
            - my_unread_notifications: User's unread notifications
        """
        metrics = {}
        
        # User's file metrics
        result = await session.execute(
            select(func.count(FileUpload.id)).where(FileUpload.uploaded_by_id == user_id)
        )
        metrics["my_documents"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(FileUpload.id)).where(
                and_(
                    FileUpload.uploaded_by_id == user_id,
                    FileUpload.status == FileStatus.PENDING
                )
            )
        )
        metrics["pending_approval"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(FileUpload.id)).where(
                and_(
                    FileUpload.uploaded_by_id == user_id,
                    FileUpload.status == FileStatus.APPROVED
                )
            )
        )
        metrics["approved_documents"] = result.scalar() or 0
        
        # User's notification metrics
        result = await session.execute(
            select(func.count(Notification.id)).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None)
                )
            )
        )
        metrics["my_unread_notifications"] = result.scalar() or 0
        
        # Overall stats visible to user
        result = await session.execute(select(func.count(FileUpload.id)))
        metrics["total_documents"] = result.scalar() or 0
        
        result = await session.execute(
            select(func.count(FileUpload.id)).where(FileUpload.status == FileStatus.APPROVED)
        )
        metrics["total_approved_documents"] = result.scalar() or 0
        
        return metrics
