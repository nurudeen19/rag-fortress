"""
Job Registry Module

Simple job registration without monolithic configuration.
Import and register handlers from jobs/handlers.py here.

To add a new scheduled job:
1. Create handler in jobs/handlers.py
2. Import it here
3. Call register_job() with configuration

Optional: Use settings flags for runtime enable/disable.
"""

from app.jobs.bootstrap import JobConfig, get_job_registry
from app.jobs.handlers import (
    escalate_stale_override_requests,
    expire_old_overrides,
)
from app.config.settings import settings


def register_scheduled_jobs():
    """
    Register all scheduled jobs with the job registry.
    
    Each job is self-contained and can be enabled/disabled
    via environment variables (optional).
    
    Note: This does NOT schedule jobs - it only registers them.
    Scheduling happens in bootstrap.init_jobs().
    """
    registry = get_job_registry()
    
    # Override escalation job
    registry.register(JobConfig(
        job_id="override_request_escalation",
        handler=escalate_stale_override_requests,
        interval_seconds=3600,  # 1 hour
        description="Auto-escalate stale override requests (24h threshold)",
        enabled=getattr(settings, "ENABLE_OVERRIDE_ESCALATION_JOB", True),
        max_instances=1
    ))
    
    # Override expiration job
    registry.register(JobConfig(
        job_id="override_expiration",
        handler=expire_old_overrides,
        interval_seconds=600,  # 10 minutes
        description="Deactivate expired overrides",
        enabled=getattr(settings, "ENABLE_OVERRIDE_EXPIRATION_JOB", True),
        max_instances=1
    ))
    
    # Add more jobs here:
    # registry.register(JobConfig(
    #     job_id="cleanup_old_logs",
    #     handler=cleanup_old_logs,
    #     interval_seconds=86400,  # Daily
    #     description="Clean up old activity logs",
    #     enabled=True,
    #     max_instances=1
    # ))
