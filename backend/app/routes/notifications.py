"""Notification API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.user import SuccessResponse
from app.handlers.notification import (
    handle_get_unread_count,
    handle_mark_notification_read,
    handle_mark_all_notifications_read,
)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("/", response_model=SuccessResponse)
async def list_notifications(
    is_read: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    service = NotificationService(session)
    notifs, total = await service.list_for_user(user.id, is_read=is_read, limit=limit, offset=offset)
    data = [
        {
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
            "notification_type": n.notification_type,
            "related_file_id": n.related_file_id,
        }
        for n in notifs
    ]
    return SuccessResponse(message="Notifications fetched", data={"total": total, "items": data})


@router.get("/unread/count", response_model=SuccessResponse)
async def unread_count(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await handle_get_unread_count(user, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to get unread count")
        )
    
    return SuccessResponse(message="Unread count", data={"count": result["count"]})


@router.post("/{notification_id}/read", response_model=SuccessResponse)
async def mark_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await handle_mark_notification_read(notification_id, user, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Notification not found")
        )
    
    return SuccessResponse(message="Notification marked read")


@router.post("/read-all", response_model=SuccessResponse)
async def mark_all_read(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await handle_mark_all_notifications_read(user, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to mark all as read")
        )
    
    return SuccessResponse(message="All notifications marked read", data={"updated": result["updated"]})
