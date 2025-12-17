"""
Event Handlers Module

Define event handlers here. Each handler receives event_data dict
and processes it in the background.

Event handlers should:
1. Be async functions
2. Accept event_data: Dict[str, Any] parameter
3. Handle their own database sessions
4. Catch and log errors (don't let them propagate)
"""

from typing import Dict, Any

from app.core import get_logger
from app.core.database import get_session
from app.services import activity_logger_service


logger = get_logger(__name__)


# ============================================================================
# Activity Logging Events
# ============================================================================

async def handle_activity_log(event_data: Dict[str, Any]) -> None:
    """
    Background handler for activity logging events.
    
    Receives activity log requests and persists them asynchronously.
    This decouples activity logging from the main request flow.
    
    Event data fields:
    - user_id: int
    - incident_type: str
    - severity: str
    - description: str
    - details: Optional[Dict]
    - user_clearance_level: Optional[str]
    - required_clearance_level: Optional[str]
    - access_granted: Optional[bool]
    - user_query: Optional[str]
    - threat_type: Optional[str]
    - ip_address: Optional[str]
    - user_agent: Optional[str]
    """
    try:
        # Extract activity log parameters from event data
        log_params = {
            "user_id": event_data["user_id"],
            "incident_type": event_data["incident_type"],
            "severity": event_data["severity"],
            "description": event_data["description"],
            "details": event_data.get("details"),
            "user_clearance_level": event_data.get("user_clearance_level"),
            "required_clearance_level": event_data.get("required_clearance_level"),
            "access_granted": event_data.get("access_granted"),
            "user_query": event_data.get("user_query"),
            "threat_type": event_data.get("threat_type"),
            "ip_address": event_data.get("ip_address"),
            "user_agent": event_data.get("user_agent"),
        }
        
        # Create new database session for background task
        async with get_session() as session:
            await activity_logger_service.log_activity(db=session, **log_params)
            await session.commit()
        
        logger.debug(
            f"Activity logged via event: {log_params['incident_type']} "
            f"(user_id={log_params['user_id']}, severity={log_params['severity']})"
        )
    
    except Exception as e:
        logger.error(f"Failed to handle activity_log event: {e}", exc_info=True)


# ============================================================================
# Add your new event handlers below
# ============================================================================

# Example:
# async def handle_user_registered(event_data: Dict[str, Any]) -> None:
#     """Handle user registration events."""
#     try:
#         user_id = event_data["user_id"]
#         email = event_data["email"]
#         # Send welcome email, etc.
#     except Exception as e:
#         logger.error(f"Failed to handle user_registered event: {e}", exc_info=True)
