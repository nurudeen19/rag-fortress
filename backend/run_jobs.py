"""
CLI utility for managing background jobs.

Usage:
    python run_jobs.py retry-pending     # Retry all pending jobs
    python run_jobs.py status            # Show job statistics
    python run_jobs.py clear-failed      # Clear failed jobs
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone

# Setup path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core import get_logger
from app.core.database import get_async_session_factory
from app.core.startup import get_startup_controller
from app.models.job import Job, JobStatus
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


async def get_job_statistics():
    """Get statistics about all jobs."""
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        # Count jobs by status
        for status in JobStatus:
            result = await session.execute(
                select(func.count(Job.id)).where(Job.status == status)
            )
            count = result.scalar()
            print(f"  {status.value}: {count}")
        
        # Total jobs
        result = await session.execute(select(func.count(Job.id)))
        total = result.scalar()
        print(f"  Total: {total}")


async def retry_pending_jobs():
    """Retry all pending jobs."""
    try:
        startup_controller = get_startup_controller()
        
        # Initialize job integration if not already done
        if startup_controller.job_integration is None:
            from app.jobs.integration import JobQueueIntegration
            startup_controller.job_integration = JobQueueIntegration(
                get_async_session_factory()
            )
            # Start job manager if not running
            if startup_controller.job_manager is None:
                from app.jobs import get_job_manager
                startup_controller.job_manager = get_job_manager()
                startup_controller.job_manager.start()
        
        # Recover and schedule pending jobs
        count = await startup_controller.job_integration.recover_and_schedule_pending()
        print(f"✓ Successfully scheduled {count} pending jobs")
        return count > 0
    
    except Exception as e:
        logger.error(f"Error retrying pending jobs: {e}", exc_info=True)
        print(f"✗ Error: {e}")
        return False


async def clear_failed_jobs():
    """Clear (delete) all failed jobs."""
    try:
        session_factory = get_async_session_factory()
        async with session_factory() as session:
            # Get count before delete
            result = await session.execute(
                select(func.count(Job.id)).where(Job.status == JobStatus.FAILED)
            )
            count_before = result.scalar()
            
            # Delete failed jobs
            await session.execute(
                session.query(Job).where(Job.status == JobStatus.FAILED).statement.delete()
            )
            await session.commit()
            
            print(f"✓ Deleted {count_before} failed jobs")
            return True
    
    except Exception as e:
        logger.error(f"Error clearing failed jobs: {e}", exc_info=True)
        print(f"✗ Error: {e}")
        return False


async def show_status():
    """Show job queue status."""
    try:
        print("\nJob Queue Status")
        print("=" * 50)
        print("Job counts by status:")
        await get_job_statistics()
        print("=" * 50)
        return True
    
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        print(f"✗ Error: {e}")
        return False


async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "retry-pending":
        success = await retry_pending_jobs()
    elif command == "status":
        success = await show_status()
    elif command == "clear-failed":
        success = await clear_failed_jobs()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
