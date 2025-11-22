"""
Statistics with simple caching - fetch from DB, cache result, invalidate on changes.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core import get_logger
from app.services.cache_service import CacheService
from app.models.job import Job, JobStatus
from app.models.file_upload import FileUpload, FileStatus
from app.config.cache_settings import cache_settings


logger = get_logger(__name__)


class StatsCache:
    """Simple statistics caching."""
    
    @staticmethod
    async def get_job_stats(session: AsyncSession) -> Dict[str, Any]:
        """
        Get job statistics. Cached after first access.
        """
        cache_key = "stats:jobs"
        
        # Try cache first
        cached = await CacheService.get(cache_key)
        if cached:
            return cached
        
        # Fetch from database
        stats = {}
        for status in JobStatus:
            result = await session.execute(
                select(func.count(Job.id)).where(Job.status == status)
            )
            stats[status.value] = result.scalar() or 0
        
        result = await session.execute(select(func.count(Job.id)))
        stats["total"] = result.scalar() or 0
        
        # Cache for 1 minute
        await CacheService.set(cache_key, stats, ttl=cache_settings.CACHE_TTL_STATS)
        return stats
    
    @staticmethod
    async def get_file_stats(session: AsyncSession, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get file statistics. Cached after first access.
        If user_id provided, returns stats for that user only.
        """
        cache_key = f"stats:files:{user_id}" if user_id else "stats:files"
        
        # Try cache first
        cached = await CacheService.get(cache_key)
        if cached:
            return cached
        
        # Build query
        query = select(func.count(FileUpload.id))
        if user_id:
            query = query.where(FileUpload.uploaded_by_id == user_id)
        
        # Fetch from database
        stats = {}
        for status in FileStatus:
            status_query = query.where(FileUpload.status == status)
            result = await session.execute(status_query)
            stats[status.value] = result.scalar() or 0
        
        result = await session.execute(query)
        stats["total"] = result.scalar() or 0
        
        # Cache for 1 minute
        await CacheService.set(cache_key, stats, ttl=cache_settings.CACHE_TTL_STATS)
        return stats
    
    @staticmethod
    async def get_file_status_counts(session: AsyncSession, user_id: Optional[int] = None) -> Dict[str, int]:
        """
        Get file counts by status. Cached after first access.
        """
        cache_key = f"stats:file_counts:{user_id}" if user_id else "stats:file_counts"
        
        # Try cache first
        cached = await CacheService.get(cache_key)
        if cached:
            return cached
        
        # Build query
        query = select(FileUpload.status, func.count(FileUpload.id)).group_by(FileUpload.status)
        if user_id:
            query = query.where(FileUpload.uploaded_by_id == user_id)
        
        # Fetch from database
        result = await session.execute(query)
        counts = {status.value: count for status, count in result.all()}
        
        # Cache for 1 minute
        await CacheService.set(cache_key, counts, ttl=cache_settings.CACHE_TTL_STATS)
        return counts
    
    @staticmethod
    async def invalidate_job_stats():
        """Clear job stats cache when jobs change."""
        await CacheService.delete("stats:jobs")
        logger.debug("Invalidated job stats cache")
    
    @staticmethod
    async def invalidate_file_stats(user_id: Optional[int] = None):
        """
        Clear file stats cache when files change.
        If user_id provided, clears that user's cache. Otherwise clears global cache.
        """
        if user_id:
            # Clear specific user's cache
            await CacheService.clear_pattern(f"stats:*:{user_id}")
            logger.debug(f"Invalidated file stats cache for user {user_id}")
        else:
            # Clear global file stats
            await CacheService.clear_pattern("stats:files*")
            await CacheService.clear_pattern("stats:file_counts*")
            logger.debug("Invalidated global file stats cache")
