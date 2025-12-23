"""
Job Bootstrap Module

Centralized job registration and scheduling. Provides config-driven job management
with guardrails, health checks, and observability.

Features:
- Config-driven job registration with enabled flags
- Automatic max_instances=1 enforcement
- Startup health summary logging
- Isolated job scheduling (errors don't block core initialization)
"""

from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core import get_logger
from app.core.database import get_session
from app.jobs import JobManager
from app.config.settings import settings
from app.services.override_request_service import OverrideRequestService


logger = get_logger(__name__)


@dataclass
class JobConfig:
    """
    Configuration for a scheduled job.
    
    Attributes:
        job_id: Unique identifier for the job
        handler: Async function to execute
        interval_seconds: Execution interval in seconds
        description: Human-readable description
        enabled: Whether the job should be scheduled (can be env-controlled)
        max_instances: Maximum concurrent instances (default 1 for safety)
        on_error: Optional error callback
    """
    job_id: str
    handler: Callable
    interval_seconds: int
    description: str
    enabled: bool = True
    max_instances: int = 1
    on_error: Optional[Callable] = None
    
    def __post_init__(self):
        """Validate job configuration."""
        if self.interval_seconds < 1:
            raise ValueError(f"Job {self.job_id}: interval_seconds must be >= 1")
        if self.max_instances < 1:
            raise ValueError(f"Job {self.job_id}: max_instances must be >= 1")
        if self.max_instances > 1:
            logger.warning(
                f"Job {self.job_id} has max_instances={self.max_instances} > 1. "
                "This may cause race conditions."
            )


class JobRegistry:
    """
    Registry of all scheduled jobs.
    
    Provides centralized management, configuration, and observability.
    """
    
    def __init__(self):
        self._jobs: List[JobConfig] = []
        self._scheduled_jobs: Dict[str, Dict[str, Any]] = {}
    
    def register(self, job: JobConfig) -> None:
        """
        Register a job configuration.
        
        Args:
            job: Job configuration to register
        """
        # Check for duplicate job IDs
        if any(j.job_id == job.job_id for j in self._jobs):
            raise ValueError(f"Job ID '{job.job_id}' already registered")
        
        self._jobs.append(job)
        logger.debug(f"Registered job: {job.job_id} ({job.description})")
    
    def get_jobs(self, enabled_only: bool = False) -> List[JobConfig]:
        """
        Get list of registered jobs.
        
        Args:
            enabled_only: If True, return only enabled jobs
        
        Returns:
            List of job configurations
        """
        if enabled_only:
            return [j for j in self._jobs if j.enabled]
        return self._jobs.copy()
    
    def get_job(self, job_id: str) -> Optional[JobConfig]:
        """
        Get a specific job by ID.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job configuration or None if not found
        """
        for job in self._jobs:
            if job.job_id == job_id:
                return job
        return None
    
    def mark_scheduled(self, job_id: str, scheduler_job_id: str) -> None:
        """
        Mark a job as scheduled.
        
        Args:
            job_id: Our job ID
            scheduler_job_id: APScheduler job ID
        """
        self._scheduled_jobs[job_id] = {
            "scheduler_job_id": scheduler_job_id,
            "scheduled_at": datetime.now(timezone.utc).isoformat()
        }
    
    def is_scheduled(self, job_id: str) -> bool:
        """Check if a job has been scheduled."""
        return job_id in self._scheduled_jobs
    
    def get_scheduled_count(self) -> int:
        """Get number of successfully scheduled jobs."""
        return len(self._scheduled_jobs)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get health summary of job system.
        
        Returns:
            Dict with job statistics and status
        """
        total_jobs = len(self._jobs)
        enabled_jobs = len([j for j in self._jobs if j.enabled])
        disabled_jobs = total_jobs - enabled_jobs
        scheduled_jobs = self.get_scheduled_count()
        
        return {
            "total_jobs": total_jobs,
            "enabled_jobs": enabled_jobs,
            "disabled_jobs": disabled_jobs,
            "scheduled_jobs": scheduled_jobs,
            "jobs": [
                {
                    "job_id": job.job_id,
                    "description": job.description,
                    "enabled": job.enabled,
                    "scheduled": self.is_scheduled(job.job_id),
                    "interval_seconds": job.interval_seconds,
                    "max_instances": job.max_instances
                }
                for job in self._jobs
            ]
        }


# ============================================================================
# Global Registry Instance
# ============================================================================

_job_registry: Optional[JobRegistry] = None


def get_job_registry() -> JobRegistry:
    """Get the global job registry instance."""
    global _job_registry
    if _job_registry is None:
        _job_registry = JobRegistry()
    return _job_registry


# ============================================================================
# Job Registration
# ============================================================================

def configure_jobs() -> JobRegistry:
    """
    Configure and register all scheduled jobs.
    
    Jobs are now registered in jobs/registry.py for better modularity.
    This function delegates to the registry module.
    
    Returns:
        Configured job registry
    """
    from app.jobs.registry import register_scheduled_jobs
    
    # Register all scheduled jobs from registry module
    register_scheduled_jobs()
    
    return get_job_registry()


# ============================================================================
# Initialization
# ============================================================================

async def init_jobs(job_manager: JobManager) -> JobRegistry:
    """
    Initialize and schedule all registered jobs.
    
    This should be called during application startup AFTER core services
    (database, cache) are initialized. Errors in individual jobs won't
    block application startup.
    
    Args:
        job_manager: Initialized JobManager instance
    
    Returns:
        Job registry with scheduling status
    """
    logger.info("Initializing scheduled jobs...")
    
    # Configure jobs
    registry = configure_jobs()
    
    # Get enabled jobs
    enabled_jobs = registry.get_jobs(enabled_only=True)
    
    if not enabled_jobs:
        logger.warning("No jobs enabled for scheduling")
        return registry
    
    logger.info(f"Scheduling {len(enabled_jobs)} enabled job(s)...")
    
    # Schedule each job
    success_count = 0
    for job in enabled_jobs:
        try:
            scheduler_job_id = job_manager.add_recurring_job(
                job.handler,
                interval_seconds=job.interval_seconds,
                job_id=job.job_id,
                max_instances=job.max_instances
            )
            
            registry.mark_scheduled(job.job_id, scheduler_job_id)
            success_count += 1
            
            logger.info(
                f"✓ Scheduled: {job.job_id} "
                f"(interval={job.interval_seconds}s, max_instances={job.max_instances})"
            )
        
        except Exception as e:
            logger.error(
                f"✗ Failed to schedule {job.job_id}: {e}",
                exc_info=True
            )
            # Continue scheduling other jobs
    
    # Log summary
    health = registry.get_health_summary()
    logger.info(
        f"✓ Job initialization complete: "
        f"{health['scheduled_jobs']}/{health['enabled_jobs']} jobs scheduled "
        f"({health['disabled_jobs']} disabled)"
    )
    
    # Log detailed status if any failures
    if success_count < len(enabled_jobs):
        logger.warning(
            f"Some jobs failed to schedule. "
            f"Success: {success_count}/{len(enabled_jobs)}"
        )
    
    return registry


def get_job_health_summary() -> Dict[str, Any]:
    """
    Get health summary of job system for monitoring/debugging.
    
    Returns:
        Job statistics and status information
    """
    registry = get_job_registry()
    return registry.get_health_summary()
