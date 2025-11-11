"""
User management request handlers (Admin operations).

Handlers manage business logic for:
- User listing and retrieval
- User suspension and activation
- Role assignment and revocation
- Permission management
- Role management
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import (
    UserAccountService,
    RolePermissionService,
)

logger = logging.getLogger(__name__)


# ============================================================================
# USER MANAGEMENT HANDLERS
# ============================================================================

async def handle_list_users(
    active_only: bool,
    department_id: Optional[int],
    limit: int,
    offset: int,
    session: AsyncSession
) -> dict:
    """
    Handle list users request.
    
    Args:
        active_only: Filter only active users
        department_id: Optional department filter
        limit: Pagination limit
        offset: Pagination offset
        session: Database session
        
    Returns:
        Dict with users list and pagination info
    """
    try:
        logger.info(f"Listing users with limit={limit}, offset={offset}")
        
        user_service = UserAccountService(session)
        
        users = await user_service.list_users(
            active_only=active_only,
            department_id=department_id,
            limit=limit,
            offset=offset
        )
        
        user_list = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "full_name": f"{u.first_name} {u.last_name}".strip(),
                "department_id": u.department_id,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "is_suspended": u.is_suspended,
                "suspension_reason": u.suspension_reason,
            }
            for u in users
        ]
        
        logger.info(f"Retrieved {len(user_list)} users")
        
        return {
            "success": True,
            "total": len(user_list),
            "limit": limit,
            "offset": offset,
            "users": user_list
        }
        
    except Exception as e:
        logger.error(f"Error handling list users request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "users": [],
            "total": 0
        }


async def handle_get_user(
    user_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle get user details request.
    
    Args:
        user_id: User ID to retrieve
        session: Database session
        
    Returns:
        Dict with user data, or error
    """
    try:
        logger.info(f"Getting user {user_id}")
        
        user_service = UserAccountService(session)
        user = await user_service.get_user(user_id)
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            return {
                "success": False,
                "error": "User not found",
                "user": None
            }
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": f"{user.first_name} {user.last_name}".strip(),
                "department_id": user.department_id,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_suspended": user.is_suspended,
                "suspension_reason": user.suspension_reason,
                "suspended_at": user.suspended_at,
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling get user request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "user": None
        }


async def handle_suspend_user(
    user_id: int,
    reason: str,
    admin_user,
    session: AsyncSession
) -> dict:
    """
    Handle suspend user request.
    
    Args:
        user_id: User ID to suspend
        reason: Suspension reason
        admin_user: Admin performing the action
        session: Database session
        
    Returns:
        Dict with success status, or error
    """
    try:
        logger.info(f"Suspending user {user_id} by admin {admin_user.id}")
        
        user_service = UserAccountService(session)
        
        success, error = await user_service.suspend_user_account(
            user_id=user_id,
            reason=reason or ""
        )
        
        if not success:
            logger.warning(f"Failed to suspend user {user_id}: {error}")
            return {
                "success": False,
                "error": error or "Failed to suspend user"
            }
        
        logger.warning(f"User {user_id} suspended by admin {admin_user.id}: {reason}")
        
        return {
            "success": True,
            "message": f"User {user_id} suspended"
        }
        
    except Exception as e:
        logger.error(f"Error handling suspend user request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def handle_unsuspend_user(
    user_id: int,
    admin_user,
    session: AsyncSession
) -> dict:
    """
    Handle unsuspend user request.
    
    Args:
        user_id: User ID to unsuspend
        admin_user: Admin performing the action
        session: Database session
        
    Returns:
        Dict with success status, or error
    """
    try:
        logger.info(f"Unsuspending user {user_id} by admin {admin_user.id}")
        
        user_service = UserAccountService(session)
        
        success, error = await user_service.unsuspend_user_account(user_id)
        
        if not success:
            logger.warning(f"Failed to unsuspend user {user_id}: {error}")
            return {
                "success": False,
                "error": error or "Failed to unsuspend user"
            }
        
        logger.info(f"User {user_id} unsuspended by admin {admin_user.id}")
        
        return {
            "success": True,
            "message": f"User {user_id} unsuspended"
        }
        
    except Exception as e:
        logger.error(f"Error handling unsuspend user request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# ROLE MANAGEMENT HANDLERS
# ============================================================================

async def handle_get_user_roles(
    user_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle get user roles request.
    
    Args:
        user_id: User ID
        session: Database session
        
    Returns:
        Dict with roles list
    """
    try:
        logger.info(f"Getting roles for user {user_id}")
        
        role_service = RolePermissionService(session)
        roles = await role_service.get_user_roles(user_id)
        
        role_list = [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "is_system": r.is_system
            }
            for r in roles
        ]
        
        return {
            "success": True,
            "roles": role_list
        }
        
    except Exception as e:
        logger.error(f"Error handling get user roles request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "roles": []
        }


async def handle_assign_role_to_user(
    user_id: int,
    role_id: int,
    admin_user,
    session: AsyncSession
) -> dict:
    """
    Handle assign role to user request.
    
    Args:
        user_id: User ID
        role_id: Role ID
        admin_user: Admin performing the action
        session: Database session
        
    Returns:
        Dict with success status, or error
    """
    try:
        logger.info(f"Assigning role {role_id} to user {user_id} by admin {admin_user.id}")
        
        role_service = RolePermissionService(session)
        
        success, error = await role_service.assign_role_to_user(user_id, role_id)
        
        if not success:
            logger.warning(f"Failed to assign role: {error}")
            return {
                "success": False,
                "error": error or "Failed to assign role"
            }
        
        logger.info(f"Role {role_id} assigned to user {user_id}")
        
        return {
            "success": True,
            "message": f"Role assigned to user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error handling assign role request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def handle_revoke_role_from_user(
    user_id: int,
    role_id: int,
    admin_user,
    session: AsyncSession
) -> dict:
    """
    Handle revoke role from user request.
    
    Args:
        user_id: User ID
        role_id: Role ID
        admin_user: Admin performing the action
        session: Database session
        
    Returns:
        Dict with success status, or error
    """
    try:
        logger.info(f"Revoking role {role_id} from user {user_id} by admin {admin_user.id}")
        
        role_service = RolePermissionService(session)
        
        success, error = await role_service.revoke_role_from_user(user_id, role_id)
        
        if not success:
            logger.warning(f"Failed to revoke role: {error}")
            return {
                "success": False,
                "error": error or "Failed to revoke role"
            }
        
        logger.info(f"Role {role_id} revoked from user {user_id}")
        
        return {
            "success": True,
            "message": f"Role revoked from user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error handling revoke role request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def handle_list_roles(
    session: AsyncSession
) -> dict:
    """
    Handle list all roles request.
    
    Args:
        session: Database session
        
    Returns:
        Dict with roles list
    """
    try:
        logger.info("Listing all roles")
        
        role_service = RolePermissionService(session)
        roles = await role_service.list_roles()
        
        role_list = [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "is_system": r.is_system,
                "permissions": [
                    {
                        "id": p.id,
                        "code": p.code,
                        "resource": p.resource,
                        "action": p.action,
                        "description": p.description
                    }
                    for p in r.permissions
                ]
            }
            for r in roles
        ]
        
        return {
            "success": True,
            "roles": role_list
        }
        
    except Exception as e:
        logger.error(f"Error handling list roles request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "roles": []
        }


async def handle_create_role(
    name: str,
    description: str,
    is_system: bool,
    admin_user,
    session: AsyncSession
) -> dict:
    """
    Handle create role request.
    
    Args:
        name: Role name
        description: Role description
        is_system: Whether it's a system role
        admin_user: Admin performing the action
        session: Database session
        
    Returns:
        Dict with new role data, or error
    """
    try:
        logger.info(f"Creating role {name} by admin {admin_user.id}")
        
        role_service = RolePermissionService(session)
        
        role, error = await role_service.create_role(
            name=name,
            description=description or "",
            is_system=is_system
        )
        
        if error or not role:
            logger.warning(f"Failed to create role: {error}")
            return {
                "success": False,
                "error": error or "Failed to create role",
                "role": None
            }
        
        logger.info(f"Role {name} created")
        
        return {
            "success": True,
            "role": {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_system": role.is_system
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling create role request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "role": None
        }


# ============================================================================
# PERMISSION MANAGEMENT HANDLERS
# ============================================================================

async def handle_list_permissions(
    resource: Optional[str],
    session: AsyncSession
) -> dict:
    """
    Handle list permissions request.
    
    Args:
        resource: Optional resource filter
        session: Database session
        
    Returns:
        Dict with permissions list
    """
    try:
        logger.info(f"Listing permissions (resource={resource})")
        
        role_service = RolePermissionService(session)
        permissions = await role_service.list_permissions(resource=resource)
        
        permission_list = [
            {
                "id": p.id,
                "code": p.code,
                "resource": p.resource,
                "action": p.action,
                "description": p.description
            }
            for p in permissions
        ]
        
        return {
            "success": True,
            "permissions": permission_list
        }
        
    except Exception as e:
        logger.error(f"Error handling list permissions request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "permissions": []
        }


async def handle_create_permission(
    code: str,
    resource: str,
    action: str,
    description: str,
    admin_user,
    session: AsyncSession
) -> dict:
    """
    Handle create permission request.
    
    Args:
        code: Permission code
        resource: Resource name
        action: Action name
        description: Description
        admin_user: Admin performing the action
        session: Database session
        
    Returns:
        Dict with new permission data, or error
    """
    try:
        logger.info(f"Creating permission {code} by admin {admin_user.id}")
        
        role_service = RolePermissionService(session)
        
        permission, error = await role_service.create_permission(
            code=code,
            resource=resource,
            action=action,
            description=description or ""
        )
        
        if error or not permission:
            logger.warning(f"Failed to create permission: {error}")
            return {
                "success": False,
                "error": error or "Failed to create permission",
                "permission": None
            }
        
        logger.info(f"Permission {code} created")
        
        return {
            "success": True,
            "permission": {
                "id": permission.id,
                "code": permission.code,
                "resource": permission.resource,
                "action": permission.action,
                "description": permission.description
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling create permission request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "permission": None
        }


async def handle_assign_permission_to_role(
    role_id: int,
    permission_id: int,
    admin_user,
    session: AsyncSession
) -> dict:
    """
    Handle assign permission to role request.
    
    Args:
        role_id: Role ID
        permission_id: Permission ID
        admin_user: Admin performing the action
        session: Database session
        
    Returns:
        Dict with success status, or error
    """
    try:
        logger.info(f"Assigning permission {permission_id} to role {role_id} by admin {admin_user.id}")
        
        role_service = RolePermissionService(session)
        
        success, error = await role_service.assign_permission_to_role(
            role_id=role_id,
            permission_id=permission_id
        )
        
        if not success:
            logger.warning(f"Failed to assign permission: {error}")
            return {
                "success": False,
                "error": error or "Failed to assign permission"
            }
        
        logger.info(f"Permission {permission_id} assigned to role {role_id}")
        
        return {
            "success": True,
            "message": f"Permission assigned to role {role_id}"
        }
        
    except Exception as e:
        logger.error(f"Error handling assign permission request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def handle_revoke_permission_from_role(
    role_id: int,
    permission_id: int,
    admin_user,
    session: AsyncSession
) -> dict:
    """
    Handle revoke permission from role request.
    
    Args:
        role_id: Role ID
        permission_id: Permission ID
        admin_user: Admin performing the action
        session: Database session
        
    Returns:
        Dict with success status, or error
    """
    try:
        logger.info(f"Revoking permission {permission_id} from role {role_id} by admin {admin_user.id}")
        
        role_service = RolePermissionService(session)
        
        success, error = await role_service.revoke_permission_from_role(
            role_id=role_id,
            permission_id=permission_id
        )
        
        if not success:
            logger.warning(f"Failed to revoke permission: {error}")
            return {
                "success": False,
                "error": error or "Failed to revoke permission"
            }
        
        logger.info(f"Permission {permission_id} revoked from role {role_id}")
        
        return {
            "success": True,
            "message": f"Permission revoked from role {role_id}"
        }
        
    except Exception as e:
        logger.error(f"Error handling revoke permission request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
