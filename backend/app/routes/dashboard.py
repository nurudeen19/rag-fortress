"""
Dashboard API routes - admin and user dashboard metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.core.database import get_session
from app.core.cache import get_cache
from app.config.cache_settings import cache_settings
from app.services.dashboard_service import DashboardService
from app.handlers.dashboard import handle_get_user_metrics, invalidate_dashboard_cache


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"],
)


@router.get(
    "/admin/metrics",
    summary="Get Admin Dashboard Metrics",
    description="Get metrics for admin dashboard (total documents, jobs, users, etc.)",
)
async def get_admin_metrics(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get admin dashboard metrics with caching.
    
    Returns:
        Dict with admin metrics including documents, jobs, users, notifications.
        
    Raises:
        HTTPException: If user is not admin.
    """
    # Check if user is admin
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access admin metrics"
        )
    
    cache = get_cache()
    cache_key = "dashboard:admin:metrics"
    
    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        return {"status": "ok", "data": cached, "cached": True}
    
    # Fetch from service
    try:
        metrics = await DashboardService.get_admin_metrics(session)
        
        # Cache for 1 minute
        await cache.set(cache_key, metrics, ttl=cache_settings.CACHE_TTL_STATS)
        
        return {"status": "ok", "data": metrics, "cached": False}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch admin metrics: {str(e)}"
        )


@router.get(
    "/user/metrics",
    summary="Get User Dashboard Metrics",
    description="Get metrics for user dashboard (my documents, notifications, etc.)",
)
async def get_user_metrics(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get user dashboard metrics with caching.
    
    Returns:
        Dict with user metrics including documents, notifications, stats.
        
    Raises:
        HTTPException: If metrics fetch fails.
    """
    try:
        metrics = await handle_get_user_metrics(current_user.id, session)
        return {"status": "ok", "data": metrics}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user metrics: {str(e)}"
        )
