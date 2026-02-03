"""
Activity Log Event Handler

Handles activity logging events asynchronously to avoid blocking
the main request flow.
"""

from typing import Dict, Any

from app.events.base import BaseEventHandler
from app.core import get_logger
from app.core.database import get_async_session_factory
from app.services import activity_logger_service


logger = get_logger(__name__)


class ActivityLogEvent(BaseEventHandler):
    """
    Activity logging event handler.
    
    Receives activity log requests and persists them asynchronously.
    This decouples activity logging from the main request flow.
    
    Event data fields:
    - user_id: int (required)
    - incident_type: str (required)
    - severity: str (required)
    - description: str (required)
    - details: Optional[Dict]
    - user_clearance_level: Optional[str]
    - required_clearance_level: Optional[str]
    - access_granted: Optional[bool]
    - user_query: Optional[str]
    - threat_type: Optional[str]
    - ip_address: Optional[str]
    - user_agent: Optional[str]
    
    Usage from services:
        from app.core.events import get_event_bus
        
        bus = get_event_bus()
        await bus.emit("activity_log", {
            "user_id": 1,
            "incident_type": "UNAUTHORIZED_ACCESS",
            "severity": "HIGH",
            "description": "User attempted to access restricted resource"
        })
    """
    
    @property
    def event_type(self) -> str:
        return "activity_log"
    
    async def handle(self, event_data: Dict[str, Any]) -> None:
        """Process activity log event."""
        try:
            # Extract required fields
            log_params = {
                "user_id": event_data["user_id"],
                "incident_type": event_data["incident_type"],
                "severity": event_data["severity"],
                "description": event_data["description"],
            }
            
            # Add optional fields if present
            optional_fields = [
                "details",
                "user_clearance_level",
                "required_clearance_level",
                "access_granted",
                "user_query",
                "threat_type",
                "ip_address",
                "user_agent",
            ]
            
            for field in optional_fields:
                if field in event_data:
                    log_params[field] = event_data[field]
            
            # Create new database session for background task
            # Use session factory directly (not the FastAPI dependency)
            session_factory = get_async_session_factory()
            async with session_factory() as session:
                await activity_logger_service.log_activity(db=session, **log_params)
                await session.commit()
            
            logger.debug(
                f"Activity logged: {log_params['incident_type']} "
                f"(user_id={log_params['user_id']}, severity={log_params['severity']})"
            )
        
        except KeyError as e:
            logger.error(f"Missing required field in activity_log event: {e}")
        except Exception as e:
            logger.error(f"Failed to process activity_log event: {e}", exc_info=True)
