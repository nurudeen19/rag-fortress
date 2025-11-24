"""
Activity Log API routes.

Simplified endpoints:
- GET /api/v1/activity - Get activity logs with optional filters and pagination
- GET /api/v1/activity/incident-types - Get available incident types
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.handlers import activity_log as activity_log_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/activity", tags=["activity"])


@router.get("")
async def get_activity_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID (defaults to current user)"),
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, critical)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Get activity logs with optional filters and pagination.
    
    Query parameters:
    - user_id: Filter by specific user (defaults to current user)
    - incident_type: Filter by incident type (e.g., "malicious_query_blocked")
    - severity: Filter by severity level (info, warning, critical)
    - days: Number of days to look back (1-365)
    - limit: Results per page (1-500)
    - offset: Skip N results for pagination
    
    Returns paginated logs with metadata:
    - logs: Array of activity log entries
    - total: Total count matching filters
    - limit: Results per page
    - offset: Current offset
    - has_more: Whether more results exist
    """
    
    # If no user_id specified, default to current user
    filter_user_id = user_id if user_id is not None else current_user.id
    
    result = await activity_log_handler.handle_get_activity_logs(
        user_id=filter_user_id,
        incident_type=incident_type,
        severity=severity,
        days=days,
        limit=limit,
        offset=offset,
        session=db
    )
    
    return result


@router.get("/incident-types")
async def get_incident_types(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available incident types for filtering.
    
    Returns common incident types that can be used with
    the /by-type endpoint. New types can be added dynamically
    without code changes (flexibility - no enum restriction).
    """
    
    # Standard incident types with descriptions
    # These are suggestions - any string value is valid
    incident_types = [
        {
            "value": "document_access_granted",
            "name": "Document Access Granted",
            "description": "User successfully accessed a document"
        },
        {
            "value": "document_access_denied",
            "name": "Document Access Denied",
            "description": "User was denied access to a document"
        },
        {
            "value": "malicious_query_blocked",
            "name": "Malicious Query Blocked",
            "description": "Malicious query was blocked by security filter"
        },
        {
            "value": "query_validation_failed",
            "name": "Query Validation Failed",
            "description": "Query failed validation checks"
        },
        {
            "value": "insufficient_clearance",
            "name": "Insufficient Clearance",
            "description": "User attempted to access above their clearance level"
        },
        {
            "value": "clearance_override_used",
            "name": "Clearance Override Used",
            "description": "User accessed document using a permission override"
        },
        {
            "value": "bulk_document_request",
            "name": "Bulk Document Request",
            "description": "User requested access to multiple documents at once"
        },
        {
            "value": "sensitive_data_access",
            "name": "Sensitive Data Access",
            "description": "User accessed sensitive/confidential data"
        },
        {
            "value": "suspicious_activity",
            "name": "Suspicious Activity",
            "description": "Suspicious activity pattern detected"
        },
        {
            "value": "access_pattern_anomaly",
            "name": "Access Pattern Anomaly",
            "description": "Unusual access pattern detected"
        },
    ]
    
    return {
        "success": True,
        "incident_types": incident_types
    }
