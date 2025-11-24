"""
Activity Log request handlers.

Simplified handlers for activity log operations.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import activity_logger_service

logger = logging.getLogger(__name__)


async def handle_get_activity_logs(
    user_id: Optional[int],
    incident_type: Optional[str],
    severity: Optional[str],
    days: int,
    limit: int,
    offset: int,
    session: AsyncSession
) -> dict:
    """
    Handle get activity logs request with optional filters and pagination.
    
    Args:
        user_id: Optional user ID to filter by
        incident_type: Optional incident type to filter by
        severity: Optional severity level to filter by
        days: Number of days to look back
        limit: Maximum number of results per page
        offset: Number of results to skip for pagination
        session: Database session
        
    Returns:
        Dict with activity logs, pagination info, or error
    """
    try:
        logger.info(
            f"Getting activity logs: user_id={user_id}, incident_type={incident_type}, "
            f"severity={severity}, days={days}, limit={limit}, offset={offset}"
        )
        
        result = await activity_logger_service.get_activity_logs(
            db=session,
            user_id=user_id,
            incident_type=incident_type,
            severity=severity,
            days=days,
            limit=limit,
            offset=offset
        )
        
        # Convert logs to dicts
        logs_list = [log.to_dict() for log in result["logs"]]
        
        return {
            "success": True,
            "logs": logs_list,
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"],
            "has_more": result["has_more"]
        }
        
    except Exception as e:
        logger.error(f"Error getting activity logs: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "logs": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "has_more": False
        }
