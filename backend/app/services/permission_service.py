"""Permission service for managing user permissions and overrides.

This module provides business logic for:
- Creating and revoking permission overrides
- Checking user access to resources
- Managing override lifecycle and expiration
- Cleanup of expired overrides

Example:
    # Create temporary override for special project
    override = await permission_service.create_override(
        user_id=42,
        override_type="department",
        department_id=3,
        override_permission_level=PermissionLevel.CONFIDENTIAL,
        reason="Q4 audit project - 2 week assignment",
        valid_from=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc) + timedelta(days=14),
        created_by_id=admin_id,
        db=session
    )
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file_upload import FileUpload
from app.models.permission_override import OverrideType, PermissionOverride
from app.models.user import User


class PermissionService:
    """Service for managing user permissions and access control."""

    @staticmethod
    async def create_override(
        user_id: int,
        override_type: str,
        override_permission_level: int,
        reason: str,
        valid_from: datetime,
        valid_until: datetime,
        created_by_id: int,
        db: AsyncSession,
        department_id: Optional[int] = None,
    ) -> PermissionOverride:
        """Create a new permission override for a user.

        Args:
            user_id: User to grant override to
            override_type: Type of override ("org_wide" or "department")
            override_permission_level: Elevated permission level to grant
            reason: Business justification for override
            valid_from: Start time of override
            valid_until: End time of override (expiry)
            created_by_id: User creating this override (audit trail)
            db: Database session
            department_id: Department ID (required if override_type="department")

        Returns:
            Created PermissionOverride object

        Raises:
            ValueError: If override_type is invalid or required fields missing
            
        Example:
            override = await permission_service.create_override(
                user_id=42,
                override_type="department",
                department_id=3,
                override_permission_level=PermissionLevel.CONFIDENTIAL,
                reason="Temporary access for special project",
                valid_from=datetime.now(timezone.utc),
                valid_until=datetime.now(timezone.utc) + timedelta(days=14),
                created_by_id=admin_id,
                db=session
            )
        """
        # Validate override type
        if override_type not in [OverrideType.ORG_WIDE, OverrideType.DEPARTMENT]:
            raise ValueError(
                f"Invalid override_type: {override_type}. "
                f"Must be '{OverrideType.ORG_WIDE}' or '{OverrideType.DEPARTMENT}'"
            )

        # Validate department requirement
        if override_type == OverrideType.DEPARTMENT and not department_id:
            raise ValueError(
                "department_id is required for DEPARTMENT override type"
            )

        # Validate time range
        if valid_until <= valid_from:
            raise ValueError("valid_until must be after valid_from")

        # Create override
        override = PermissionOverride(
            user_id=user_id,
            override_type=override_type,
            department_id=department_id,
            override_permission_level=override_permission_level,
            reason=reason,
            valid_from=valid_from,
            valid_until=valid_until,
            created_by_id=created_by_id,
            is_active=True,
        )

        db.add(override)
        await db.flush()
        
        # Invalidate clearance cache since permission changed
        from app.utils.user_clearance_cache import get_user_clearance_cache
        clearance_cache = get_user_clearance_cache(db)
        await clearance_cache.invalidate(user_id)
        
        return override

    @staticmethod
    async def revoke_override(
        override_id: int,
        db: AsyncSession,
    ) -> Optional[PermissionOverride]:
        """Revoke (deactivate) a permission override.

        Args:
            override_id: ID of override to revoke
            db: Database session

        Returns:
            Revoked override or None if not found

        Example:
            override = await permission_service.revoke_override(42, db)
            if override:
                logger.debug(f"Revoked override for user {override.user_id}")
        """
        override = await db.get(PermissionOverride, override_id)
        if override:
            user_id = override.user_id
            override.revoke()
            await db.flush()
            
            # Invalidate clearance cache since permission changed
            from app.utils.user_clearance_cache import get_user_clearance_cache
            clearance_cache = get_user_clearance_cache(db)
            await clearance_cache.invalidate(user_id)
        
        return override

    @staticmethod
    async def cleanup_expired_overrides(db: AsyncSession) -> int:
        """Mark all expired overrides as inactive.

        Overrides with valid_until < now are marked as inactive so they
        no longer contribute to effective permission calculations.

        Args:
            db: Database session

        Returns:
            Number of overrides marked as expired

        Example:
            count = await permission_service.cleanup_expired_overrides(db)
            logger.info(f"Cleaned up {count} expired overrides")
        """
        now = datetime.now(timezone.utc)

        # Get all expired active overrides
        result = await db.execute(
            select(PermissionOverride).where(
                and_(
                    PermissionOverride.is_active,
                    PermissionOverride.valid_until < now,
                )
            )
        )
        expired = result.scalars().all()

        # Mark as inactive and invalidate caches
        if expired:
            from app.utils.user_clearance_cache import get_user_clearance_cache
            clearance_cache = get_user_clearance_cache(db)
            
            affected_users = set()
            for override in expired:
                override.is_active = False
                affected_users.add(override.user_id)
            
            # Invalidate cache for all affected users
            for user_id in affected_users:
                await clearance_cache.invalidate(user_id)

        await db.flush()
        return len(expired)

    @staticmethod
    async def get_active_overrides_for_user(
        user_id: int,
        db: AsyncSession,
        override_type: Optional[str] = None,
    ) -> list[PermissionOverride]:
        """Get all active overrides for a user.

        Args:
            user_id: User to get overrides for
            db: Database session
            override_type: Optional filter by type ("org_wide" or "department")

        Returns:
            List of active PermissionOverride objects

        Example:
            overrides = await permission_service.get_active_overrides_for_user(42, db)
            for override in overrides:
                logger.debug(f"Override: {override.reason}, expires {override.valid_until}")
        """
        now = datetime.now(timezone.utc)

        query = select(PermissionOverride).where(
            and_(
                PermissionOverride.user_id == user_id,
                PermissionOverride.is_active,
                PermissionOverride.valid_from <= now,
                PermissionOverride.valid_until >= now,
            )
        )

        if override_type:
            query = query.where(PermissionOverride.override_type == override_type)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def can_user_access_file(
        user_id: int,
        file_id: int,
        db: AsyncSession,
    ) -> bool:
        """Check if user can access a file based on security level and permissions.

        Args:
            user_id: User to check
            file_id: File to check access for
            db: Database session

        Returns:
            True if user can access file, False otherwise

        Example:
            can_access = await permission_service.can_user_access_file(42, 1, db)
            if can_access:
                # Allow file download/view
                pass
            else:
                # Deny access
                raise PermissionDenied()
        """
        # Get user and file
        user = await db.get(User, user_id)
        file = await db.get(FileUpload, file_id)

        if not user or not file:
            return False

        # Check if user has permission record
        if not user.user_permission or not user.user_permission.is_active:
            return False

        # Get effective permission considering overrides
        effective_level = user.user_permission.get_effective_permission()

        # Check if permission meets file security requirement
        return effective_level >= file.security_level

    @staticmethod
    async def get_user_permission_summary(
        user_id: int,
        db: AsyncSession,
    ) -> dict:
        """Get comprehensive permission summary for a user.

        Args:
            user_id: User to get summary for
            db: Database session

        Returns:
            Dictionary with permission information

        Example:
            summary = await permission_service.get_user_permission_summary(42, db)
            print(f"Org level: {summary['org_level_permission']}")
            print(f"Effective level: {summary['effective_permission']}")
            print(f"Active overrides: {len(summary['active_overrides'])}")
        """
        # Get user and permissions
        user = await db.get(User, user_id)
        if not user or not user.user_permission:
            return {
                "user_id": user_id,
                "has_permission_record": False,
                "effective_permission": None,
                "active_overrides": [],
            }

        permission = user.user_permission
        active_overrides = permission.get_active_overrides()

        # Build summary
        return {
            "user_id": user_id,
            "has_permission_record": True,
            "is_active": permission.is_active,
            "org_level_permission": permission.org_level_permission.value,
            "department_id": permission.department_id,
            "department_level_permission": (
                permission.department_level_permission.value
                if permission.department_level_permission
                else None
            ),
            "effective_permission": permission.get_effective_permission(),
            "active_overrides": [
                {
                    "id": override.id,
                    "override_type": override.override_type,
                    "override_permission_level": override.override_permission_level,
                    "reason": override.reason,
                    "valid_from": override.valid_from.isoformat(),
                    "valid_until": override.valid_until.isoformat(),
                    "days_remaining": override.days_remaining(),
                }
                for override in active_overrides
            ],
        }

    @staticmethod
    async def extend_override(
        override_id: int,
        new_valid_until: datetime,
        db: AsyncSession,
    ) -> Optional[PermissionOverride]:
        """Extend the expiry date of an active override.

        Args:
            override_id: Override to extend
            new_valid_until: New expiry datetime
            db: Database session

        Returns:
            Extended override or None if not found

        Raises:
            ValueError: If override is expired or new_valid_until is in past

        Example:
            override = await permission_service.extend_override(
                override_id=42,
                new_valid_until=datetime.now(timezone.utc) + timedelta(days=7),
                db=session
            )
        """
        override = await db.get(PermissionOverride, override_id)
        if not override:
            return None

        if override.is_expired():
            raise ValueError("Cannot extend an expired override")

        if new_valid_until <= datetime.now(timezone.utc):
            raise ValueError("new_valid_until must be in the future")

        if new_valid_until < override.valid_until:
            raise ValueError("Cannot shorten override duration with extend operation")

        override.valid_until = new_valid_until
        await db.flush()
        return override

    @staticmethod
    async def get_expiring_soon_overrides(
        days_until_expiry: int = 3,
        db: AsyncSession = None,
    ) -> list[PermissionOverride]:
        """Get all active overrides expiring within N days.

        Useful for notifications and auditing.

        Args:
            days_until_expiry: Number of days threshold (default: 3)
            db: Database session

        Returns:
            List of PermissionOverride objects expiring soon

        Example:
            expiring = await permission_service.get_expiring_soon_overrides(days=3, db=db)
            for override in expiring:
                send_expiry_notification(override.user.email)
        """
        now = datetime.now(timezone.utc)
        threshold = now + timedelta(days=days_until_expiry)

        result = await db.execute(
            select(PermissionOverride).where(
                and_(
                    PermissionOverride.is_active,
                    PermissionOverride.valid_until > now,
                    PermissionOverride.valid_until <= threshold,
                )
            )
        )
        return result.scalars().all()

    @staticmethod
    async def audit_override_history(
        user_id: int,
        db: AsyncSession,
        limit: int = 100,
    ) -> list[PermissionOverride]:
        """Get all overrides (active and inactive) for audit trail.

        Args:
            user_id: User to get history for
            db: Database session
            limit: Maximum results to return

        Returns:
            List of all PermissionOverride objects for user (active and revoked)

        Example:
            history = await permission_service.audit_override_history(42, db)
            for override in history:
                status = "active" if override.is_active else "revoked"
                print(f"{override.created_at} - {override.reason} ({status})")
        """
        result = await db.execute(
            select(PermissionOverride)
            .where(PermissionOverride.user_id == user_id)
            .order_by(PermissionOverride.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


# Create a singleton instance for easy access
permission_service = PermissionService()
