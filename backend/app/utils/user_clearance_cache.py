"""
User Clearance Cache Utility

Manages caching of user security clearance information including:
- User ID
- Security level (with override consideration)
- Department ID
- Department name

Cache is automatically synchronized with access token expiry.
"""

from typing import Optional, Dict, Any, Tuple
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import get_cache
from app.models.user import User
from app.models.user_permission import PermissionLevel
from app.config.settings import settings
from app.core import get_logger

logger = get_logger(__name__)


class UserClearanceCache:
    """
    Utility for caching user clearance information.
    
    Automatically fetches and caches user security data if not present.
    Cache TTL matches access token expiry for consistency.
    
    Usage:
        cache_util = UserClearanceCache(session)
        clearance = await cache_util.get_clearance(user_id)
        
        # Returns:
        {
            "user_id": 42,
            "security_level": "CONFIDENTIAL",  # Org-wide level (with overrides)
            "department_security_level": "HIGHLY_CONFIDENTIAL",  # Department-specific level
            "department_id": 5,
            "department_name": "Engineering",
            "is_admin": False,
            "is_department_manager": True,
            "org_clearance_value": 3,  # Numeric value for limits
            "dept_clearance_value": 4
        }
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.cache = get_cache()
        # Match token expiry
        self.ttl = int(timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds())
    
    async def get_clearance(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user clearance information from cache or database.
        
        Automatically caches if not present. Returns effective security level
        including any active overrides.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with user_id, security_level (str), department_id, department_name
            None if user not found
        """
        # Try cache first
        cached = await self._get_from_cache(user_id)
        if cached:
            logger.debug(f"Cache hit for user_id={user_id}")
            return cached
        
        # Cache miss - fetch from DB
        logger.info(f"Cache miss for user_id={user_id}, fetching from database")
        clearance = await self._fetch_from_db(user_id)
        
        if clearance:
            # Cache it
            await self.set_clearance(
                user_id=clearance["user_id"],
                security_level=clearance["security_level"],
                department_id=clearance["department_id"],
                department_name=clearance["department_name"],
                department_security_level=clearance.get("department_security_level"),
                is_admin=clearance.get("is_admin", False),
                is_department_manager=clearance.get("is_department_manager", False),
                org_clearance_value=clearance.get("org_clearance_value", 1),
                dept_clearance_value=clearance.get("dept_clearance_value")
            )
        
        return clearance
    
    async def set_clearance(
        self,
        user_id: int,
        security_level: str,
        department_id: Optional[int],
        department_name: Optional[str],
        department_security_level: Optional[str] = None,
        is_admin: bool = False,
        is_department_manager: bool = False,
        org_clearance_value: int = 1,
        dept_clearance_value: Optional[int] = None
    ) -> None:
        """
        Manually set user clearance in cache.
        
        Use this after login to cache clearance info with consistent keys.
        Security level should already include any override considerations.
        
        Args:
            user_id: User ID
            security_level: Org-wide security level name (e.g., "CONFIDENTIAL")
            department_id: Department ID or None
            department_name: Department name or None
            department_security_level: Department-specific security level or None
            is_admin: Whether user has admin role
            is_department_manager: Whether user is a department manager
            org_clearance_value: Numeric value of org clearance
            dept_clearance_value: Numeric value of dept clearance
        """
        import json
        
        cache_key = self._get_cache_key(user_id)
        data = {
            "user_id": user_id,
            "security_level": security_level,
            "department_security_level": department_security_level,
            "department_id": department_id,
            "department_name": department_name,
            "is_admin": is_admin,
            "is_department_manager": is_department_manager,
            "org_clearance_value": org_clearance_value,
            "dept_clearance_value": dept_clearance_value
        }
        
        await self.cache.set(
            cache_key,
            json.dumps(data),
            ttl=self.ttl
        )
        
        logger.info(f"Cached clearance for user_id={user_id}, level={security_level}")
    
    async def invalidate(self, user_id: int) -> None:
        """
        Invalidate cached clearance for a user.
        
        Use when user permissions change (override added/removed, etc).
        
        Args:
            user_id: User ID to invalidate
        """
        cache_key = self._get_cache_key(user_id)
        await self.cache.delete(cache_key)
        logger.info(f"Invalidated clearance cache for user_id={user_id}")
    
    async def _get_from_cache(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get clearance from cache."""
        import json
        
        cache_key = self._get_cache_key(user_id)
        cached_data = await self.cache.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        return None
    
    async def _fetch_from_db(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch user clearance from database.
        
        Computes effective security level including overrides.
        """
        # Load user with all permission-related data
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.user_permission),
                selectinload(User.permission_overrides),
                selectinload(User.department)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            return None
        
        # Get effective security levels (org + department, includes overrides)
        security_level, dept_level = self._get_effective_security_level(user)

        department_security_level = dept_level.name if dept_level else None
        dept_clearance_value = dept_level.value if dept_level else None
        
        # Check if user is admin or department manager
        is_admin = user.has_role("admin")
        is_department_manager = False
        if user.department_id and user.department:
            is_department_manager = user.department.manager_id == user.id
        
        # Get department info
        department_id = user.department_id
        department_name = user.department.name if user.department else None
        
        return {
            "user_id": user_id,
            "security_level": security_level.name,
            "department_security_level": department_security_level,
            "department_id": department_id,
            "department_name": department_name,
            "is_admin": is_admin,
            "is_department_manager": is_department_manager,
            "org_clearance_value": security_level.value,
            "dept_clearance_value": dept_clearance_value
        }
    
    def _get_effective_security_level(
        self, user: User
    ) -> Tuple[PermissionLevel, Optional[PermissionLevel]]:
        """Get effective org and department clearance levels with overrides."""
        if not user.user_permission:
            logger.warning(
                f"User {user.id} has no permission record, defaulting to GENERAL"
            )
            return PermissionLevel.GENERAL, None

        def get_level_value(level) -> int:
            if isinstance(level, PermissionLevel):
                return level.value
            return int(level)

        org_level_value = get_level_value(user.user_permission.org_level_permission)

        dept_level_value: Optional[int] = None
        if user.user_permission.department_level_permission:
            dept_level_value = get_level_value(
                user.user_permission.department_level_permission
            )

        active_overrides = user.get_active_overrides()
        for override in active_overrides:
            override_level = get_level_value(override.override_permission_level)
            if override.override_type == "org_wide":
                org_level_value = max(org_level_value, override_level)
                logger.debug(
                    f"User {user.id} has active org-wide override: "
                    f"level={override.override_permission_level}, "
                    f"reason={override.reason}"
                )
            elif (
                override.override_type == "department"
                and user.department_id
                and override.department_id == user.department_id
            ):
                base_dept = dept_level_value or org_level_value
                dept_level_value = max(base_dept, override_level)
                logger.debug(
                    f"User {user.id} has active department override for dept "
                    f"{user.department_id}: level={override.override_permission_level}, "
                    f"reason={override.reason}"
                )

        org_level = PermissionLevel(org_level_value)
        dept_level = (
            PermissionLevel(dept_level_value) if dept_level_value is not None else None
        )
        return org_level, dept_level
    
    def _get_cache_key(self, user_id: int) -> str:
        """Generate consistent cache key."""
        return f"user:clearance:{user_id}"


def get_user_clearance_cache(user_id_or_session, session: Optional[AsyncSession] = None):
    """
    Get user clearance information or cache instance.
    
    Can be called two ways:
    1. get_user_clearance_cache(session) -> Returns UserClearanceCache instance
    2. get_user_clearance_cache(user_id, session) -> Returns coroutine for clearance data
    
    Args:
        user_id_or_session: Either user_id (int) or AsyncSession
        session: AsyncSession (only when first arg is user_id)
        
    Returns:
        UserClearanceCache instance if called with session only,
        Coroutine that returns clearance dict if called with user_id and session
    """
    # Check if first argument is a session (when called with just session)
    if isinstance(user_id_or_session, AsyncSession):
        # get_user_clearance_cache(session) -> return instance
        return UserClearanceCache(user_id_or_session)
    else:
        # get_user_clearance_cache(user_id, session) -> return coroutine
        user_id = user_id_or_session
        if session is None:
            raise ValueError("session parameter required when user_id is provided")
        cache_instance = UserClearanceCache(session)
        return cache_instance.get_clearance(user_id)
