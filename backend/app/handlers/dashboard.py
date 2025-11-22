"""
Dashboard handlers - orchestrate service calls with caching.
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache
from app.config.cache_settings import cache_settings
from app.services.dashboard_service import DashboardService


async def handle_get_admin_metrics() -> Dict[str, Any]:
    """
    Get cached admin metrics.
    
    Returns:
        Admin dashboard metrics from cache or database.
    """
    cache = get_cache()
    cache_key = "dashboard:admin:metrics"
    
    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # If not in cache, will be fetched on demand
    # Cache is populated by the route handler
    return {}


async def handle_get_user_metrics(user_id: int, session: AsyncSession) -> Dict[str, Any]:
    """
    Get cached user metrics.
    
    Args:
        user_id: User ID
        session: Database session
        
    Returns:
        User dashboard metrics.
    """
    cache = get_cache()
    cache_key = f"dashboard:user:metrics:{user_id}"
    
    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Fetch from service
    metrics = await DashboardService.get_user_metrics(session, user_id)
    
    # Cache for TTL
    await cache.set(cache_key, metrics, ttl=cache_settings.CACHE_TTL_STATS)
    
    return metrics


async def invalidate_dashboard_cache(user_id: int = None):
    """
    Invalidate dashboard cache when data changes.
    
    Args:
        user_id: If provided, invalidates only that user's cache.
                 If None, invalidates admin cache.
    """
    cache = get_cache()
    
    if user_id:
        # Invalidate specific user's dashboard cache
        await cache.delete(f"dashboard:user:metrics:{user_id}")
    else:
        # Invalidate admin dashboard cache
        await cache.delete("dashboard:admin:metrics")
