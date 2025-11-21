"""Notification API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.user import SuccessResponse

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
    service = NotificationService(session)
    count = await service.get_unread_count(user.id)
    return SuccessResponse(message="Unread count", data={"count": count})


@router.post("/{notification_id}/read", response_model=SuccessResponse)
async def mark_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    service = NotificationService(session)
    ok = await service.mark_read(notification_id, user.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    await session.commit()
    return SuccessResponse(message="Notification marked read")


@router.post("/read-all", response_model=SuccessResponse)
async def mark_all_read(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    service = NotificationService(session)
    changed = await service.mark_all_read(user.id)
    await session.commit()
    return SuccessResponse(message="All notifications marked read", data={"updated": changed})
