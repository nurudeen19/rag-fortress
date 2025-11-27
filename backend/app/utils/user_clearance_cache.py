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
            "security_level": "CONFIDENTIAL",
            "department_id": 5,
            "department_name": "Engineering"
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
                department_name=clearance["department_name"]
            )
        
        return clearance
    
    async def set_clearance(
        self,
        user_id: int,
        security_level: str,
        department_id: Optional[int],
        department_name: Optional[str]
    ) -> None:
        """
        Manually set user clearance in cache.
        
        Use this after login to cache clearance info with consistent keys.
        Security level should already include any override considerations.
        
        Args:
            user_id: User ID
            security_level: Security level name (e.g., "CONFIDENTIAL")
            department_id: Department ID or None
            department_name: Department name or None
        """
        import json
        
        cache_key = self._get_cache_key(user_id)
        data = {
            "user_id": user_id,
            "security_level": security_level,
            "department_id": department_id,
            "department_name": department_name
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
        
        # Get department info
        department_id = user.department_id
        department_name = user.department.name if user.department else None
        
        return {
            "user_id": user_id,
            "security_level": security_level.name,
            "department_id": department_id,
            "department_name": department_name
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
        
        # Start with org-wide permission
        levels = [user.permission.org_level_permission.value]
        
        # Add department-level permission if exists
        if user.permission.department_level_permission:
            levels.append(user.permission.department_level_permission.value)
        
        # Add active overrides (highest priority)
        active_overrides = user.get_active_overrides()
        for override in active_overrides:
            levels.append(override.override_permission_level)
            logger.debug(
                f"User {user.id} has active override: "
                f"level={override.override_permission_level}, "
                f"type={override.override_type}, "
                f"reason={override.reason}"
            )
        
        # Return highest level
        max_level_value = max(levels)
        return PermissionLevel(max_level_value)
    
    def _get_cache_key(self, user_id: int) -> str:
        """Generate consistent cache key."""
        return f"user:clearance:{user_id}"


def get_user_clearance_cache(session: AsyncSession) -> UserClearanceCache:
    """Get UserClearanceCache instance."""
    return UserClearanceCache(session)
