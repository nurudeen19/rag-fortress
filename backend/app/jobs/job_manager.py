"""
Job Manager - Manages background job scheduling and execution.
Uses APScheduler for lightweight, in-process job scheduling.
"""

import asyncio
import inspect
from typing import Callable, Any, Optional, Dict
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from app.core import get_logger


logger = get_logger(__name__)


class JobManager:
    """
    Manages background jobs with APScheduler.
    
    Supports:
    - Immediate execution (fire-and-forget)
    - Scheduled execution (one-time at specific time)
    - Recurring execution (interval-based)
    """
    
    _instance: Optional['JobManager'] = None
    
    def __new__(cls) -> 'JobManager':
        """Singleton pattern - only one scheduler per application."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize job manager with background scheduler."""
        if hasattr(self, '_initialized'):
            return
        
        self.scheduler = BackgroundScheduler(
            daemon=True,
            timezone='UTC'
        )
        self._initialized = True
        logger.info("JobManager initialized")
    
    def _make_async_wrapper(self, async_func: Callable, *args, **kwargs) -> Callable:
        """
        Wrap an async function to run in a new event loop.
        
        APScheduler's BackgroundScheduler runs in sync mode, so async functions
        must be wrapped to create and run in a new event loop.
        
        Args:
            async_func: Async function to wrap
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Synchronous wrapper function
        """
        def wrapper():
            try:
                # Create new event loop for this job execution
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Run the async function
                    loop.run_until_complete(async_func(*args, **kwargs))
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"Error in async job {async_func.__name__}: {e}", exc_info=True)
        
        return wrapper
    
    def start(self) -> None:
        """Start the scheduler if not already running."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Job scheduler started")
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("Job scheduler shutdown")
    
    def add_immediate_job(
        self,
        func: Callable,
        *args,
        job_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Execute a job immediately in background.
        
        Automatically wraps async functions to run in a new event loop.
        
        Args:
            func: Callable to execute (sync or async)
            *args: Positional arguments for func
            job_id: Optional unique job identifier
            **kwargs: Keyword arguments for func
        
        Returns:
            Job ID
        """
        # Detect if function is async and wrap it
        if inspect.iscoroutinefunction(func):
            wrapped_func = self._make_async_wrapper(func, *args, **kwargs)
            args = ()
            kwargs = {}
        else:
            wrapped_func = func
        
        job = self.scheduler.add_job(
            wrapped_func,
            args=args,
            kwargs=kwargs,
            id=job_id,
            replace_existing=False,
        )
        logger.info(f"Added immediate job: {job.id}")
        return job.id
    
    def add_scheduled_job(
        self,
        func: Callable,
        run_at: datetime,
        *args,
        job_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Schedule a job to run at a specific time.
        
        Automatically wraps async functions to run in a new event loop.
        
        Args:
            func: Callable to execute (sync or async)
            run_at: When to run the job (datetime)
            *args: Positional arguments for func
            job_id: Optional unique job identifier
            **kwargs: Keyword arguments for func
        
        Returns:
            Job ID
        """
        # Ensure datetime is aware
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=timezone.utc)
        
        # Detect if function is async and wrap it
        if inspect.iscoroutinefunction(func):
            wrapped_func = self._make_async_wrapper(func, *args, **kwargs)
            args = ()
            kwargs = {}
        else:
            wrapped_func = func
        
        job = self.scheduler.add_job(
            wrapped_func,
            trigger=DateTrigger(run_date=run_at),
            args=args,
            kwargs=kwargs,
            id=job_id,
            replace_existing=False,
        )
        logger.info(f"Scheduled job: {job.id} at {run_at}")
        return job.id
    
    def add_recurring_job(
        self,
        func: Callable,
        interval_seconds: int,
        *args,
        job_id: Optional[str] = None,
        max_instances: int = 1,
        **kwargs
    ) -> str:
        """
        Schedule a job to run at regular intervals.
        
        Automatically wraps async functions to run in a new event loop.
        
        Args:
            func: Callable to execute (sync or async)
            interval_seconds: Interval in seconds between executions
            *args: Positional arguments for func
            job_id: Optional unique job identifier
            max_instances: Max concurrent instances (default: 1)
            **kwargs: Keyword arguments for func
        
        Returns:
            Job ID
        """
        # Detect if function is async and wrap it
        if inspect.iscoroutinefunction(func):
            wrapped_func = self._make_async_wrapper(func, *args, **kwargs)
            # Clear args/kwargs since they're already bound in the wrapper
            args = ()
            kwargs = {}
        else:
            wrapped_func = func
        
        job = self.scheduler.add_job(
            wrapped_func,
            trigger=IntervalTrigger(seconds=interval_seconds),
            args=args,
            kwargs=kwargs,
            id=job_id,
            replace_existing=False,
            max_instances=max_instances,
        )
        logger.info(f"Added recurring job: {job.id} (interval: {interval_seconds}s)")
        return job.id
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.
        
        Args:
            job_id: Job identifier
        
        Returns:
            True if job was removed, False if not found
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Job not found or already removed: {job_id} - {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job details.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job info dict or None if not found
        """
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
                "func": job.func_ref,
            }
        return None
    
    def get_jobs(self) -> list[Dict[str, Any]]:
        """Get all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
            }
            for job in jobs
        ]
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to pause job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to resume job {job_id}: {e}")
            return False


def get_job_manager() -> JobManager:
    """Get or create the global JobManager instance."""
    return JobManager()
