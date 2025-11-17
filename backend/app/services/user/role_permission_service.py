"""
Role and permission service for managing user roles and permissions.
Handles role assignment, revocation, and permission checking.
"""

from typing import Optional, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.auth import Role, Permission
from app.core import get_logger


logger = get_logger(__name__)


class RolePermissionService:
    """Service for managing roles and permissions."""
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
    
    # ==================== ROLE MANAGEMENT ====================
    
    async def assign_role_to_user(
        self,
        user_id: int,
        role_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Assign a role to a user.
        
        Args:
            user_id: User ID
            role_id: Role ID to assign
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return False, "User not found"
            
            role = await self.session.get(Role, role_id)
            if not role:
                return False, "Role not found"
            
            # Check if user already has this role
            if role in user.roles:
                return True, None  # Already assigned
            
            user.roles.append(role)
            await self.session.flush()
            
            logger.info(f"Role '{role.name}' assigned to user '{user.username}'")
            return True, None
        
        except Exception as e:
            logger.error(f"Assign role error: {e}")
            return False, "Failed to assign role"
    
    async def revoke_role_from_user(
        self,
        user_id: int,
        role_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Revoke a role from a user.
        
        Args:
            user_id: User ID
            role_id: Role ID to revoke
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return False, "User not found"
            
            role = await self.session.get(Role, role_id)
            if not role:
                return False, "Role not found"
            
            # Check if user has this role
            if role not in user.roles:
                return True, None  # Not assigned
            
            user.roles.remove(role)
            await self.session.flush()
            
            logger.info(f"Role '{role.name}' revoked from user '{user.username}'")
            return True, None
        
        except Exception as e:
            logger.error(f"Revoke role error: {e}")
            return False, "Failed to revoke role"
    
    async def assign_roles_to_user(
        self,
        user_id: int,
        role_ids: List[int]
    ) -> Tuple[bool, Optional[str]]:
        """
        Assign multiple roles to a user (replaces existing roles).
        
        Args:
            user_id: User ID
            role_ids: List of role IDs to assign
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return False, "User not found"
            
            # Fetch all roles
            result = await self.session.execute(
                select(Role).where(Role.id.in_(role_ids))
            )
            roles = result.scalars().all()
            
            if len(roles) != len(role_ids):
                return False, "One or more roles not found"
            
            # Replace roles
            user.roles = roles
            await self.session.flush()
            
            role_names = ", ".join([r.name for r in roles])
            logger.info(f"Roles assigned to user '{user.username}': {role_names}")
            return True, None
        
        except Exception as e:
            logger.error(f"Assign roles error: {e}")
            return False, "Failed to assign roles"
    
    async def get_user_roles(self, user_id: int) -> List[Role]:
        """
        Get all roles assigned to a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of Role objects
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return []
            
            return user.roles
        
        except Exception as e:
            logger.error(f"Get user roles error: {e}")
            raise
    
    async def user_has_role(self, user_id: int, role_name: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            user_id: User ID
            role_name: Role name to check
        
        Returns:
            True if user has role, False otherwise
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return False
            
            return user.has_role(role_name)
        
        except Exception as e:
            logger.error(f"Check user role error: {e}")
            raise
    
    # ==================== PERMISSION MANAGEMENT ====================
    
    async def create_role(
        self,
        name: str,
        description: str = "",
        is_system: bool = False
    ) -> Tuple[Optional[Role], Optional[str]]:
        """
        Create a new role.
        
        Args:
            name: Role name
            description: Role description
            is_system: Whether this is a system role
        
        Returns:
            Tuple of (created_role, error_message)
        """
        try:
            # Check if role already exists
            result = await self.session.execute(
                select(Role).where(Role.name == name)
            )
            if result.scalar_one_or_none():
                return None, "Role already exists"
            
            role = Role(
                name=name,
                description=description,
                is_system=is_system
            )
            
            self.session.add(role)
            await self.session.flush()
            
            logger.info(f"Role created: '{role.name}'")
            return role, None
        
        except Exception as e:
            logger.error(f"Create role error: {e}")
            return None, "Failed to create role"
    
    async def assign_permission_to_role(
        self,
        role_id: int,
        permission_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Assign a permission to a role.
        
        Args:
            role_id: Role ID
            permission_id: Permission ID
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            role = await self.session.get(Role, role_id)
            if not role:
                return False, "Role not found"
            
            permission = await self.session.get(Permission, permission_id)
            if not permission:
                return False, "Permission not found"
            
            # Check if role already has this permission
            if permission in role.permissions:
                return True, None  # Already assigned
            
            role.permissions.append(permission)
            await self.session.flush()
            
            logger.info(f"Permission '{permission.code}' assigned to role '{role.name}'")
            return True, None
        
        except Exception as e:
            logger.error(f"Assign permission error: {e}")
            return False, "Failed to assign permission"
    
    async def revoke_permission_from_role(
        self,
        role_id: int,
        permission_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Revoke a permission from a role.
        
        Args:
            role_id: Role ID
            permission_id: Permission ID
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            role = await self.session.get(Role, role_id)
            if not role:
                return False, "Role not found"
            
            permission = await self.session.get(Permission, permission_id)
            if not permission:
                return False, "Permission not found"
            
            # Check if role has this permission
            if permission not in role.permissions:
                return True, None  # Not assigned
            
            role.permissions.remove(permission)
            await self.session.flush()
            
            logger.info(f"Permission '{permission.code}' revoked from role '{role.name}'")
            return True, None
        
        except Exception as e:
            logger.error(f"Revoke permission error: {e}")
            return False, "Failed to revoke permission"
    
    async def get_role_permissions(self, role_id: int) -> List[Permission]:
        """
        Get all permissions for a role.
        
        Args:
            role_id: Role ID
        
        Returns:
            List of Permission objects
        """
        try:
            role = await self.session.get(Role, role_id)
            if not role:
                return []
            
            return role.permissions
        
        except Exception as e:
            logger.error(f"Get role permissions error: {e}")
            raise
    
    async def get_user_permissions(self, user_id: int) -> List[Permission]:
        """
        Get all permissions for a user (via their roles).
        
        Args:
            user_id: User ID
        
        Returns:
            List of Permission objects (deduplicated)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return []
            
            # Collect all permissions from all roles
            permissions = []
            permission_codes = set()
            
            for role in user.roles:
                for permission in role.permissions:
                    if permission.code not in permission_codes:
                        permissions.append(permission)
                        permission_codes.add(permission.code)
            
            return permissions
        
        except Exception as e:
            logger.error(f"Get user permissions error: {e}")
            raise
    
    async def user_has_permission(
        self,
        user_id: int,
        permission_code: str
    ) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_id: User ID
            permission_code: Permission code to check
        
        Returns:
            True if user has permission, False otherwise
        """
        try:
            permissions = await self.get_user_permissions(user_id)
            return any(p.code == permission_code for p in permissions)
        
        except Exception as e:
            logger.error(f"Check user permission error: {e}")
            raise
    
    async def create_permission(
        self,
        code: str,
        resource: str,
        action: str,
        description: str = ""
    ) -> Tuple[Optional[Permission], Optional[str]]:
        """
        Create a new permission.
        
        Args:
            code: Unique permission code (e.g., "file_upload_approve")
            resource: Resource type (e.g., "file_upload")
            action: Action (e.g., "approve")
            description: Permission description
        
        Returns:
            Tuple of (created_permission, error_message)
        """
        try:
            # Check if permission already exists
            result = await self.session.execute(
                select(Permission).where(Permission.code == code)
            )
            if result.scalar_one_or_none():
                return None, "Permission already exists"
            
            permission = Permission(
                code=code,
                resource=resource,
                action=action,
                description=description
            )
            
            self.session.add(permission)
            await self.session.flush()
            
            logger.info(f"Permission created: '{permission.code}'")
            return permission, None
        
        except Exception as e:
            logger.error(f"Create permission error: {e}")
            return None, "Failed to create permission"
    
    async def list_roles(self) -> List[Role]:
        """
        Get all available roles.
        
        Returns:
            List of Role objects
        """
        try:
            from sqlalchemy.orm import selectinload
            result = await self.session.execute(
                select(Role).options(selectinload(Role.permissions))
            )
            return result.scalars().all()
        
        except Exception as e:
            logger.error(f"List roles error: {e}")
            raise
    
    async def list_permissions(self, resource: Optional[str] = None) -> List[Permission]:
        """
        Get all permissions, optionally filtered by resource.
        
        Args:
            resource: Optional resource filter
        
        Returns:
            List of Permission objects
        """
        try:
            query = select(Permission)
            
            if resource:
                query = query.where(Permission.resource == resource)
            
            result = await self.session.execute(query)
            return result.scalars().all()
        
        except Exception as e:
            logger.error(f"List permissions error: {e}")
            raise
