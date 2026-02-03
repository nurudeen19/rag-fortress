"""Data ingestion job seeder - creates initial job queue entry."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.job import Job, JobStatus, JobType
from app.seeders.base import BaseSeed

logger = logging.getLogger(__name__)


class JobsSeeder(BaseSeed):
    """Seeder for creating initial jobs for data ingestion processing."""
    
    name = "jobs"
    description = "Creates initial data ingestion job queue entries"
    required_tables = ["jobs"]
    
    async def run(self, session: AsyncSession, **kwargs) -> dict:
        """Create initial job queue entry for data ingestion."""
        try:
            # Validate required tables exist
            tables_exist, missing_tables = await self.validate_tables_exist(session)
            if not tables_exist:
                error_msg = (
                    f"Required table(s) missing: {', '.join(missing_tables)}. "
                    "Please run migrations first: python migrate.py"
                )
                logger.error(error_msg)
                return {"success": False, "message": error_msg}
            
            logger.info("Seeding initial jobs...")
            
            # Check if ingestion job already exists
            stmt = select(Job).where(
                Job.job_type == JobType.FILE_INGESTION,
                Job.status == JobStatus.PENDING,
            )
            result = await session.execute(stmt)
            existing_job = result.scalar_one_or_none()
            
            if existing_job:
                logger.info(f"Initial ingestion job already exists (ID: {existing_job.id})")
                return {
                    "success": True,
                    "message": "Initial jobs already seeded",
                    "jobs_created": 0,
                    "existing_jobs": 1,
                }
            
            # Create initial data ingestion job
            # This job will process files that are already approved
            initial_job = Job(
                job_type=JobType.FILE_INGESTION,
                status=JobStatus.PENDING,
                reference_id=0,  # System-wide job, not tied to specific file
                reference_type="system",
                payload=None,  # Will be populated by processor
                max_retries=3,
                retry_count=0,
            )
            
            session.add(initial_job)
            await session.flush()
            
            logger.info(f"Created initial data ingestion job (ID: {initial_job.id})")
            
            await session.commit()
            
            return {
                "success": True,
                "message": "Initial jobs seeded successfully",
                "jobs_created": 1,
                "initial_job_id": initial_job.id,
            }
        
        except Exception as e:
            logger.error(f"Failed to seed jobs: {e}", exc_info=True)
            return {"success": False, "message": f"Seeding failed: {str(e)}"}
