"""Notification operation handlers - business logic for notification operations."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.notification import Notification
from app.services.notification_service import NotificationService
from app.config.cache_settings import cache_settings
from app.core.cache import get_cache
from app.core import get_logger


logger = get_logger(__name__)


async def handle_create_notification(
    user_id: int,
    message: str,
    session: AsyncSession,
    notification_type: Optional[str] = None,
    related_file_id: Optional[int] = None,
) -> dict:
    """
    Create a notification and invalidate user's unread count cache.
    """
    try:
        service = NotificationService(session)
        notif = await service.create(user_id, message, notification_type, related_file_id)
        
        # Invalidate cache for this user's unread count (new notification added)
        cache = get_cache()
        await cache.delete(f"notif:unread_count:{user_id}")
        
        logger.info(f"Created notification {notif.id} for user {user_id}, invalidated cache")
        return {"success": True, "notification_id": notif.id}
    except Exception as e:
        logger.error(f"Create notification failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_get_unread_count(user: User, session: AsyncSession) -> dict:
    """
    Get unread notification count for user.
    Uses cache to avoid querying database on every request.
    Cache is invalidated when notifications are marked as read or new ones are created.
    """
    try:
        cache = get_cache()
        cache_key = f"notif:unread_count:{user.id}"
        
        # Try cache first
        cached_count = await cache.get(cache_key)
        if cached_count is not None:
            return {"success": True, "count": cached_count}
        
        # Fetch from service (queries database)
        service = NotificationService(session)
        count = await service.get_unread_count(user.id)
        
        # Cache the result
        await cache.set(cache_key, count, ttl=cache_settings.CACHE_TTL_STATS)
        
        return {"success": True, "count": count}
    except Exception as e:
        logger.error(f"Get unread count failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_mark_notification_read(
    notification_id: int,
    user: User,
    session: AsyncSession
) -> dict:
    """
    Mark a notification as read and invalidate user's unread count cache.
    """
    try:
        service = NotificationService(session)
        ok = await service.mark_read(notification_id, user.id)
        
        if not ok:
            return {"success": False, "error": "Notification not found"}
        
        await session.commit()
        
        # Invalidate cache for this user's unread count
        cache = get_cache()
        await cache.delete(f"notif:unread_count:{user.id}")
        
        logger.info(f"Marked notification {notification_id} as read for user {user.id}")
        return {"success": True}
    except Exception as e:
        await session.rollback()
        logger.error(f"Mark notification read failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def handle_mark_all_notifications_read(user: User, session: AsyncSession) -> dict:
    """
    Mark all notifications as read and invalidate user's unread count cache.
    """
    try:
        service = NotificationService(session)
        changed = await service.mark_all_read(user.id)
        
        await session.commit()
        
        # Invalidate cache for this user's unread count
        cache = get_cache()
        await cache.delete(f"notif:unread_count:{user.id}")
        
        logger.info(f"Marked all {changed} notifications as read for user {user.id}")
        return {"success": True, "updated": changed}
    except Exception as e:
        await session.rollback()
        logger.error(f"Mark all notifications read failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
