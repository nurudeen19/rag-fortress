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
            stmt = stmt.where(Notification.is_read.is_(is_read))
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        notifications = result.scalars().all()

        # total count (with same filter sans pagination)
        count_stmt = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            count_stmt = count_stmt.where(Notification.is_read.is_(is_read))
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.scalars().all())
        return notifications, total

    async def get_unread_count(self, user_id: int) -> int:
        stmt = select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
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
        stmt = select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
        result = await self.session.execute(stmt)
        notifs = result.scalars().all()
        for n in notifs:
            n.mark_read()
        return len(notifs)

    async def _get_admin_users(self) -> List["User"]:
        """Return all users with the admin role."""
        from app.models.user import User
        from app.models.auth import Role

        admin_role_result = await self.session.execute(
            select(Role).where(Role.name == "admin")
        )
        admin_role = admin_role_result.scalar_one_or_none()

        if not admin_role:
            return []

        admin_users_result = await self.session.execute(
            select(User)
            .join(User.roles)
            .where(Role.id == admin_role.id)
        )
        return admin_users_result.scalars().all()
    
    # Permission override request notifications
    
    async def notify_override_request_submitted(
        self,
        request: "PermissionOverrideRequest",
        approver_id: int,
    ) -> None:
        """Notify approver about new override request."""
        from app.models.user_permission import PermissionLevel
        
        level_name = PermissionLevel(request.requested_permission_level).name
        hours = request.requested_duration_hours
        duration_text = f"{hours} hours" if hours < 48 else f"{hours // 24} days"
        
        message = (
            f"New permission override request from {request.requester.full_name}: "
            f"{level_name} {request.override_type} access for {duration_text}. "
            f"Reason: {request.reason[:100]}..."
        )
        
        await self.create(
            user_id=approver_id,
            message=message,
            notification_type="override_request_submitted",
        )
    
    async def notify_admins_new_override_request(
        self,
        request: "PermissionOverrideRequest",
    ) -> None:
        """Notify all admins about a new override request (org-wide or department)."""
        from app.models.user_permission import PermissionLevel

        admins = await self._get_admin_users()
        if not admins:
            return

        level_name = PermissionLevel(request.requested_permission_level).name
        hours = request.requested_duration_hours
        duration_text = f"{hours} hours" if hours < 48 else f"{hours // 24} days"

        if request.override_type == "org_wide":
            scope_text = "ORG-WIDE"
        else:
            dept_name = request.department.name if getattr(request, "department", None) else None
            scope_text = f"DEPARTMENT ({dept_name})" if dept_name else "DEPARTMENT"

        message = (
            f"New {scope_text} permission request from {request.requester.full_name}: "
            f"{level_name} access for {duration_text}. "
            f"Reason: {request.reason[:100]}..."
        )

        for admin in admins:
            await self.create(
                user_id=admin.id,
                message=message,
                notification_type="override_request_admin",
            )
    
    async def notify_admins_override_escalation(
        self,
        request: "PermissionOverrideRequest",
    ) -> None:
        """Notify admins about escalated request."""
        from app.models.user_permission import PermissionLevel
        
        admins = await self._get_admin_users()
        if not admins:
            return
        
        level_name = PermissionLevel(request.requested_permission_level).name
        hours = request.requested_duration_hours
        duration_text = f"{hours} hours" if hours < 48 else f"{hours // 24} days"
        
        message = (
            f"ESCALATED: Permission request from {request.requester.full_name} "
            f"requires admin review ({level_name} for {duration_text}). "
            f"Department manager did not respond within 24 hours."
        )
        
        for admin in admins:
            await self.create(
                user_id=admin.id,
                message=message,
                notification_type="override_request_escalated",
            )
    
    async def notify_override_request_approved(
        self,
        request: "PermissionOverrideRequest",
    ) -> None:
        """Notify requester that their request was approved."""
        from app.models.user_permission import PermissionLevel
        
        level_name = PermissionLevel(request.override_permission_level).name
        expiry_date = request.valid_until.strftime("%Y-%m-%d %H:%M UTC")
        
        message = (
            f"Your permission override request was APPROVED! "
            f"You now have {level_name} {request.override_type} access "
            f"until {expiry_date}."
        )
        
        if request.approval_notes:
            message += f" Note from approver: {request.approval_notes}"
        
        await self.create(
            user_id=request.user_id,
            message=message,
            notification_type="override_request_approved",
        )
    
    async def notify_override_request_denied(
        self,
        request: "PermissionOverrideRequest",
        denial_reason: str,
    ) -> None:
        """Notify requester that their request was denied."""
        from app.models.user_permission import PermissionLevel
        
        level_name = PermissionLevel(request.override_permission_level).name
        
        message = (
            f"Your permission override request was DENIED. "
            f"Requested: {level_name} {request.override_type} access. "
            f"Reason: {denial_reason}"
        )
        
        await self.create(
            user_id=request.user_id,
            message=message,
            notification_type="override_request_denied",
        )
