"""
User Clearance Cache Utility

Manages caching of user security clearance information including:
- User ID
- Security level (with override consideration)
- Department ID
- Department name

Cache is automatically synchronized with access token expiry.
"""

from typing import Optional, Dict, Any
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import get_cache
from app.models.user import User
from app.models.user_permission import UserPermission, PermissionLevel
from app.models.department import Department
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
                selectinload(User.permission),
                selectinload(User.permission_overrides),
                selectinload(User.department)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            return None
        
        # Get effective security level (includes overrides)
        security_level = self._get_effective_security_level(user)
        
        # Get department-specific security level
        department_security_level = None
        dept_clearance_value = None
        if user.permission and user.permission.department_level_permission:
            dept_level = user.permission.department_level_permission
            if isinstance(dept_level, PermissionLevel):
                department_security_level = dept_level.name
                dept_clearance_value = dept_level.value
            else:
                dept_level_enum = PermissionLevel(dept_level)
                department_security_level = dept_level_enum.name
                dept_clearance_value = dept_level_enum.value
        
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
    
    def _get_effective_security_level(self, user: User) -> PermissionLevel:
        """
        Get effective security level including overrides.
        
        Priority:
        1. Active overrides (highest override level)
        2. Department-level permission
        3. Organization-wide permission
        4. Default to GENERAL
        """
        if not user.permission:
            logger.warning(f"User {user.id} has no permission record, defaulting to GENERAL")
            return PermissionLevel.GENERAL
        
        # Helper to get int value from either int or enum
        def get_level_value(level) -> int:
            if isinstance(level, PermissionLevel):
                return level.value
            return int(level)  # Already an int from database
        
        # Start with org-wide permission
        levels = [get_level_value(user.permission.org_level_permission)]
        
        # Add department-level permission if exists
        if user.permission.department_level_permission:
            levels.append(get_level_value(user.permission.department_level_permission))
        
        # Add active overrides (highest priority)
        # Note: override_permission_level is stored as int in database
        active_overrides = user.get_active_overrides()
        for override in active_overrides:
            levels.append(get_level_value(override.override_permission_level))
            logger.debug(
                f"User {user.id} has active override: "
                f"level={override.override_permission_level}, "
                f"type={override.override_type}, "
                f"reason={override.reason}"
            )
        
        # Return highest level as enum
        max_level_value = max(levels)
        return PermissionLevel(max_level_value)
    
    def _get_cache_key(self, user_id: int) -> str:
        """Generate consistent cache key."""
        return f"user:clearance:{user_id}"


def get_user_clearance_cache(session: AsyncSession) -> UserClearanceCache:
    """Get UserClearanceCache instance."""
    return UserClearanceCache(session)
