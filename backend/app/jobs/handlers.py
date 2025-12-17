"""
Job Handlers Module

Define individual job handlers here. Each handler is a self-contained
async function that can be imported and registered independently.

Job handlers should:
1. Be async functions
2. Handle their own database sessions
3. Log errors appropriately
4. Be idempotent when possible
"""

from app.core import get_logger
from app.core.database import get_session
from app.services.override_request_service import OverrideRequestService


logger = get_logger(__name__)


# ============================================================================
# Override Management Jobs
# ============================================================================

async def escalate_stale_override_requests():
    """
    Auto-escalate override requests that have been pending too long.
    
    Runs hourly to check for requests pending > 24 hours.
    """
    try:
        async with get_session() as session:
            service = OverrideRequestService(session)
            count = await service.process_auto_escalations(
                escalation_threshold_hours=24
            )
            await session.commit()
            
            if count > 0:
                logger.info(f"Auto-escalated {count} override request(s)")
    
    except Exception as e:
        logger.error(f"Error in escalate_stale_override_requests: {e}", exc_info=True)


async def expire_old_overrides():
    """
    Deactivate overrides that have passed their expiration date.
    
    Runs every 10 minutes to keep access control tight.
    """
    try:
        async with get_session() as session:
            service = OverrideRequestService(session)
            count = await service.process_expired_overrides()
            await session.commit()

            if count > 0:
                logger.info(f"Expired {count} override(s)")

    except Exception as e:
        logger.error(f"Error in expire_old_overrides: {e}", exc_info=True)


# ============================================================================
# Add your new job handlers below
# ============================================================================

# Example:
# async def cleanup_old_logs():
#     """Clean up activity logs older than 90 days."""
#     try:
#         async with get_session() as session:
#             # Your cleanup logic here
#             pass
#     except Exception as e:
#         logger.error(f"Error in cleanup_old_logs: {e}", exc_info=True)
