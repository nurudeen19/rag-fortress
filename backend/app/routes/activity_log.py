"""
Activity Log API routes.

Simplified endpoints:
- GET /api/v1/activity - Get activity logs with optional filters and pagination (Admin only)
- GET /api/v1/activity/incident-types - Get available incident types (Admin only)
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import require_role
from app.models.user import User
from app.schemas.activity_log import (
    ActivityLogsListResponse,
    IncidentTypesResponse,
    IncidentTypeInfo,
)
from app.handlers import activity_log as activity_log_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/activity", tags=["activity"])


@router.get("", response_model=ActivityLogsListResponse)
async def get_activity_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, critical)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip for pagination"),
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_session)
):
    """
    Get activity logs with optional filters and pagination.
    
    **Admin only endpoint**
    
    Query parameters:
    - user_id: Filter by specific user (optional, shows all if not provided)
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
    
    result = await activity_log_handler.handle_get_activity_logs(
        user_id=user_id,
        incident_type=incident_type,
        severity=severity,
        days=days,
        limit=limit,
        offset=offset,
        session=db
    )
    
    return result


@router.get("/incident-types", response_model=IncidentTypesResponse)
async def get_incident_types(
    admin: User = Depends(require_role("admin"))
):
    """
    Get list of available incident types for filtering.
    
    **Admin only endpoint**
    
    Returns common incident types that can be used for filtering.
    New types can be added dynamically without code changes.
    """
    
    # Standard incident types with descriptions
    incident_types = [
        IncidentTypeInfo(
            value="document_access_granted",
            name="Document Access Granted",
            description="User successfully accessed a document"
        ),
        IncidentTypeInfo(
            value="document_access_denied",
            name="Document Access Denied",
            description="User was denied access to a document"
        ),
        IncidentTypeInfo(
            value="malicious_query_blocked",
            name="Malicious Query Blocked",
            description="Malicious query was blocked by security filter"
        ),
        IncidentTypeInfo(
            value="query_validation_failed",
            name="Query Validation Failed",
            description="Query failed validation checks"
        ),
        IncidentTypeInfo(
            value="retrieval_no_context",
            name="No Context Retrieved",
            description="Query did not find relevant documents above quality threshold"
        ),
        IncidentTypeInfo(
            value="insufficient_clearance",
            name="Insufficient Clearance",
            description="User attempted to access above their clearance level"
        ),
        IncidentTypeInfo(
            value="clearance_override_used",
            name="Clearance Override Used",
            description="User accessed document using a permission override"
        ),
        IncidentTypeInfo(
            value="bulk_document_request",
            name="Bulk Document Request",
            description="User requested access to multiple documents at once"
        ),
        IncidentTypeInfo(
            value="sensitive_data_access",
            name="Sensitive Data Access",
            description="User accessed sensitive/confidential data"
        ),
        IncidentTypeInfo(
            value="suspicious_activity",
            name="Suspicious Activity",
            description="Suspicious activity pattern detected"
        ),
        IncidentTypeInfo(
            value="access_pattern_anomaly",
            name="Access Pattern Anomaly",
            description="Unusual access pattern detected"
        ),
    ]
    
    return IncidentTypesResponse(
        success=True,
        incident_types=incident_types
    )
