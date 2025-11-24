"""
Activity Logging Service

Simplified service for tracking user actions and security incidents.
Provides comprehensive audit trail with database persistence.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.models.activity_log import ActivityLog

logger = logging.getLogger(__name__)


# ============================================================================
# SIMPLIFIED ACTIVITY LOGGING
# ============================================================================

async def log_activity(
    db: AsyncSession,
    user_id: int,
    incident_type: str,
    severity: str,
    description: str,
    details: Optional[Dict[str, Any]] = None,
    user_clearance_level: Optional[str] = None,
    required_clearance_level: Optional[str] = None,
    access_granted: Optional[bool] = None,
    user_query: Optional[str] = None,
    threat_type: Optional[str] = None,
    conversation_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> ActivityLog:
    """
    Log an activity/incident to the database.
    
    Args:
        db: Database session
        user_id: ID of user performing the action
        incident_type: Type of incident (e.g., "malicious_query_blocked", "document_access_denied")
        severity: Severity level ("info", "warning", "critical")
        description: Human-readable description
        details: Optional structured details (will be JSON-encoded)
        user_clearance_level: Optional user's clearance level
        required_clearance_level: Optional required clearance level
        access_granted: Optional boolean for access decisions
        user_query: Optional user query text
        threat_type: Optional threat classification
        conversation_id: Optional conversation context
        ip_address: Optional IP address
        user_agent: Optional user agent string
        
    Returns:
        ActivityLog: Created log entry
    """
    
    # Create activity log entry
    activity_log = ActivityLog(
        user_id=user_id,
        incident_type=incident_type,
        severity=severity,
        description=description,
        details=json.dumps(details) if details else None,
        user_clearance_level=user_clearance_level,
        required_clearance_level=required_clearance_level,
        access_granted=access_granted,
        user_query=user_query,
        threat_type=threat_type,
        conversation_id=conversation_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(activity_log)
    await db.flush()
    
    # Log to application logger
    log_level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(
        log_level,
        f"Activity logged: user_id={user_id}, type={incident_type}, severity={severity}"
    )
    
    return activity_log


async def get_activity_logs(
    db: AsyncSession,
    user_id: Optional[int] = None,
    incident_type: Optional[str] = None,
    severity: Optional[str] = None,
    days: Optional[int] = 30,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get activity logs with optional filters and pagination.
    
    Args:
        db: Database session
        user_id: Optional filter by user ID
        incident_type: Optional filter by incident type
        severity: Optional filter by severity level
        days: Optional days to look back (default 30, None for all)
        limit: Maximum number of results (default 100)
        offset: Pagination offset (default 0)
        
    Returns:
        Dict containing:
            - logs: List of activity log entries
            - total: Total count matching filters
            - limit: Applied limit
            - offset: Applied offset
            - has_more: Whether more results exist
    """
    
    # Build query with filters
    conditions = []
    
    if user_id is not None:
        conditions.append(ActivityLog.user_id == user_id)
    
    if incident_type:
        conditions.append(ActivityLog.incident_type == incident_type)
    
    if severity:
        conditions.append(ActivityLog.severity == severity)
    
    if days is not None:
        since_date = datetime.utcnow() - timedelta(days=days)
        conditions.append(ActivityLog.created_at >= since_date)
    
    # Build base query
    query = select(ActivityLog)
    if conditions:
        query = query.where(and_(*conditions))
    
    # Get total count
    count_query = select(func.count()).select_from(ActivityLog)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Apply ordering and pagination
    query = query.order_by(desc(ActivityLog.created_at)).limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "logs": [log.to_dict() for log in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": total > (offset + limit)
    }



