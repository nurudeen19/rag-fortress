"""
Error Report Service - Manage user-reported errors.

Handles:
- Creating error reports from user submissions
- Retrieving reports (user's own, admin all)
- Updating report status and notes (admin)
- Image attachment management
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.error_report import ErrorReport, ErrorReportStatus, ErrorReportCategory
from app.models.user import User
from app.schemas.error_report import (
    ErrorReportCreateRequest,
    ErrorReportResponse,
    ErrorReportDetailResponse,
    ErrorReportAdminUpdateRequest,
)
from app.core import get_logger

logger = get_logger(__name__)


class ErrorReportService:
    """Service for managing error reports."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.image_upload_dir = "/data/error_reports"
    
    async def create_report(
        self,
        user_id: int,
        request: ErrorReportCreateRequest,
        user_agent: Optional[str] = None,
        request_context: Optional[str] = None,
    ) -> Tuple[bool, ErrorReportResponse | dict]:
        """
        Create a new error report from user submission.
        
        Args:
            user_id: ID of user submitting report
            request: Error report creation request
            user_agent: Browser/client user agent
            request_context: JSON context of request
            
        Returns:
            Tuple of (success: bool, response: ErrorReportResponse | error_dict)
        """
        try:
            error_report = ErrorReport(
                user_id=user_id,
                conversation_id=request.conversation_id,
                title=request.title,
                description=request.description,
                category=request.category,
                status=ErrorReportStatus.OPEN,
                user_agent=user_agent,
                request_context=request_context,
            )
            
            self.session.add(error_report)
            await self.session.flush()
            await self.session.refresh(error_report)
            
            logger.info(f"Created error report {error_report.id} from user {user_id}")
            
            return (
                True,
                ErrorReportResponse.model_validate(error_report),
            )
        
        except Exception as e:
            logger.error(f"Failed to create error report: {e}", exc_info=True)
            return (False, {"error": str(e)})
    
    async def attach_image(
        self,
        report_id: int,
        filename: str,
        image_url: Optional[str] = None,
    ) -> bool:
        """
        Attach image to error report.
        
        Args:
            report_id: ID of error report
            filename: Filename of uploaded image
            image_url: URL if stored externally
            
        Returns:
            True if successful
        """
        try:
            stmt = select(ErrorReport).where(ErrorReport.id == report_id)
            result = await self.session.execute(stmt)
            report = result.scalar_one_or_none()
            
            if not report:
                logger.warning(f"Error report {report_id} not found for image attachment")
                return False
            
            report.image_filename = filename
            report.image_url = image_url
            
            logger.info(f"Attached image {filename} to error report {report_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to attach image to report: {e}", exc_info=True)
            return False
    
    async def get_user_reports(
        self,
        user_id: int,
        status: Optional[ErrorReportStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ErrorReportResponse]:
        """
        Get error reports submitted by a user.
        
        Args:
            user_id: ID of user
            status: Optional status filter
            limit: Number of reports to return
            offset: Pagination offset
            
        Returns:
            List of error reports
        """
        try:
            query = select(ErrorReport).where(ErrorReport.user_id == user_id)
            
            if status:
                query = query.where(ErrorReport.status == status)
            
            query = query.order_by(ErrorReport.created_at.desc()).limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            reports = result.scalars().all()
            
            return [ErrorReportResponse.model_validate(r) for r in reports]
        
        except Exception as e:
            logger.error(f"Failed to get user reports: {e}", exc_info=True)
            return []
    
    async def get_user_reports_count(self, user_id: int, status: Optional[ErrorReportStatus] = None) -> int:
        """Get count of user's error reports."""
        try:
            query = select(ErrorReport).where(ErrorReport.user_id == user_id)
            
            if status:
                query = query.where(ErrorReport.status == status)
            
            result = await self.session.execute(query)
            return len(result.scalars().all())
        
        except Exception as e:
            logger.error(f"Failed to count user reports: {e}", exc_info=True)
            return 0
    
    async def get_all_reports_admin(
        self,
        status: Optional[ErrorReportStatus] = None,
        category: Optional[ErrorReportCategory] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ErrorReportDetailResponse], int, dict]:
        """
        Get all error reports for admin view.
        
        Args:
            status: Optional status filter
            category: Optional category filter
            limit: Number of reports
            offset: Pagination offset
            
        Returns:
            Tuple of (reports, total_count, status_counts)
        """
        try:
            # Build query
            query = select(ErrorReport).options(
                joinedload(ErrorReport.user),
            )
            
            if status:
                query = query.where(ErrorReport.status == status)
            
            if category:
                query = query.where(ErrorReport.category == category)
            
            # Get paginated results
            query_paginated = query.order_by(ErrorReport.created_at.desc()).limit(limit).offset(offset)
            result = await self.session.execute(query_paginated)
            reports = result.unique().scalars().all()
            
            # Get total count
            count_query = select(ErrorReport)
            if status:
                count_query = count_query.where(ErrorReport.status == status)
            if category:
                count_query = count_query.where(ErrorReport.category == category)
            
            count_result = await self.session.execute(count_query)
            total = len(count_result.scalars().all())
            
            # Get status counts for dashboard
            status_counts = await self._get_status_counts()
            
            # Format response
            detail_reports = []
            for r in reports:
                detail = ErrorReportDetailResponse(
                    id=r.id,
                    user_id=r.user_id,
                    user_name=r.user.email if r.user else None,
                    title=r.title,
                    description=r.description,
                    category=r.category,
                    status=r.status,
                    conversation_id=r.conversation_id,
                    image_filename=r.image_filename,
                    user_agent=r.user_agent,
                    admin_notes=r.admin_notes,
                    assigned_to=r.assigned_to,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                    resolved_at=r.resolved_at,
                )
                detail_reports.append(detail)
            
            return detail_reports, total, status_counts
        
        except Exception as e:
            logger.error(f"Failed to get admin reports: {e}", exc_info=True)
            return [], 0, {}
    
    async def _get_status_counts(self) -> dict:
        """Get count of reports by status."""
        try:
            result = await self.session.execute(select(ErrorReport))
            all_reports = result.scalars().all()
            
            counts = {
                "open": len([r for r in all_reports if r.status == ErrorReportStatus.OPEN]),
                "investigating": len([r for r in all_reports if r.status == ErrorReportStatus.INVESTIGATING]),
                "acknowledged": len([r for r in all_reports if r.status == ErrorReportStatus.ACKNOWLEDGED]),
                "resolved": len([r for r in all_reports if r.status == ErrorReportStatus.RESOLVED]),
            }
            return counts
        
        except Exception as e:
            logger.error(f"Failed to get status counts: {e}", exc_info=True)
            return {}
    
    async def update_report_admin(
        self,
        report_id: int,
        update: ErrorReportAdminUpdateRequest,
    ) -> Tuple[bool, Optional[ErrorReportDetailResponse]]:
        """
        Update error report (admin only).
        
        Args:
            report_id: ID of report to update
            update: Update request with new status/notes
            
        Returns:
            Tuple of (success: bool, updated_report: ErrorReportDetailResponse | None)
        """
        try:
            stmt = select(ErrorReport).where(ErrorReport.id == report_id).options(
                joinedload(ErrorReport.user),
            )
            result = await self.session.execute(stmt)
            report = result.unique().scalar_one_or_none()
            
            if not report:
                logger.warning(f"Error report {report_id} not found for update")
                return False, None
            
            if update.status:
                report.status = update.status
                if update.status == ErrorReportStatus.RESOLVED:
                    report.resolved_at = datetime.now(timezone.utc)
            
            if update.admin_notes:
                report.admin_notes = update.admin_notes
            
            if update.assigned_to:
                report.assigned_to = update.assigned_to
            
            await self.session.flush()
            await self.session.refresh(report)
            
            logger.info(f"Updated error report {report_id}")
            
            detail = ErrorReportDetailResponse(
                id=report.id,
                user_id=report.user_id,
                user_name=report.user.email if report.user else None,
                title=report.title,
                description=report.description,
                category=report.category,
                status=report.status,
                conversation_id=report.conversation_id,
                image_filename=report.image_filename,
                user_agent=report.user_agent,
                admin_notes=report.admin_notes,
                assigned_to=report.assigned_to,
                created_at=report.created_at,
                updated_at=report.updated_at,
                resolved_at=report.resolved_at,
            )
            
            return True, detail
        
        except Exception as e:
            logger.error(f"Failed to update error report: {e}", exc_info=True)
            return False, None


def get_error_report_service(session: AsyncSession) -> ErrorReportService:
    """Get error report service instance."""
    return ErrorReportService(session)
