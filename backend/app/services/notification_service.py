"""Service layer for Notification CRUD operations."""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.models.notification import Notification
from app.core import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Provides CRUD operations for notifications."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        message: str,
        notification_type: Optional[str] = None,
        related_file_id: Optional[int] = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            message=message,
            notification_type=notification_type,
            related_file_id=related_file_id,
        )
        self.session.add(notif)
        await self.session.flush()  # obtain id early
        logger.info(f"Created notification {notif.id} for user {user_id}")
        return notif

    async def list_for_user(
        self,
        user_id: int,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Notification], int]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        notifications = result.scalars().all()

        # total count (with same filter sans pagination)
        count_stmt = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            count_stmt = count_stmt.where(Notification.is_read == is_read)
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.scalars().all())
        return notifications, total

    async def get_unread_count(self, user_id: int) -> int:
        stmt = select(Notification).where(Notification.user_id == user_id, Notification.is_read == False)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())

    async def mark_read(self, notification_id: int, user_id: int) -> bool:
        stmt = select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        result = await self.session.execute(stmt)
        notif = result.scalar_one_or_none()
        if not notif:
            return False
        notif.mark_read()
        return True

    async def mark_all_read(self, user_id: int) -> int:
        stmt = select(Notification).where(Notification.user_id == user_id, Notification.is_read == False)
        result = await self.session.execute(stmt)
        notifs = result.scalars().all()
        for n in notifs:
            n.mark_read()
        return len(notifs)
