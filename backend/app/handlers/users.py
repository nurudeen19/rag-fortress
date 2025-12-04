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
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta

from app.models.user import User
from app.models.auth import Role
from app.config.settings import settings
from app.services.user import (
    UserAccountService,
    RolePermissionService,
    PasswordService,
    InvitationService,
)
from app.services.email.builders.specialized import InvitationEmailBuilder
from app.utils.user_clearance_cache import get_user_clearance_cache

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
                "suspended_at": u.suspended_at,
                "roles": [
                    {
                        "id": role.id,
                        "name": role.name,
                        "description": role.description,
                        "is_system": role.is_system,
                    }
                    for role in (u.roles or [])
                ],
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
        
        # Fetch user with eager-loaded roles
        result = await session.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            return {
                "success": False,
                "error": "User not found",
                "user": None
            }
        
        # Convert roles to response format
        roles = [
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_system": role.is_system,
            }
            for role in (user.roles or [])
        ]
        
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
                "roles": roles,
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
        # Prevent admin from suspending their own account
        if admin_user.id == user_id:
            logger.warning(f"Admin {admin_user.id} attempted to suspend their own account")
            return {
                "success": False,
                "error": "You cannot suspend your own account"
            }
        
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
        # Prevent admin from unsuspending their own account
        if admin_user.id == user_id:
            logger.warning(f"Admin {admin_user.id} attempted to unsuspend their own account")
            return {
                "success": False,
                "error": "You cannot unsuspend your own account"
            }
        
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


def can_invite_user(inviter_clearance: dict, target_dept_id: Optional[int]) -> tuple[bool, Optional[str]]:
    """
    Check if inviter has permission to invite a user to the target department.
    
    Args:
        inviter_clearance: Cached clearance data from get_user_clearance_cache
        target_dept_id: Department ID the user is being invited to
        
    Returns:
        Tuple of (authorized: bool, error_message: Optional[str])
    """
    if inviter_clearance.get("is_admin"):
        return True, None
    
    if inviter_clearance.get("is_department_manager"):
        if target_dept_id == inviter_clearance.get("department_id"):
            return True, None
        return False, "Department managers can only invite users to their own department"
    
    return False, "Insufficient permissions to send invitations"


def validate_clearance_limits(
    requested_org: int,
    requested_dept: Optional[int],
    inviter_org_max: int,
    inviter_dept_max: Optional[int],
    is_admin: bool
) -> tuple[bool, Optional[str]]:
    """
    Validate that requested clearance levels don't exceed inviter's own limits.
    
    Args:
        requested_org: Requested org-wide clearance level (1-4)
        requested_dept: Requested department clearance level (1-4 or None)
        inviter_org_max: Inviter's max org clearance value
        inviter_dept_max: Inviter's max dept clearance value
        is_admin: Whether inviter is admin (no limits)
        
    Returns:
        Tuple of (valid: bool, error_message: Optional[str])
    """
    if is_admin:
        return True, None  # Admins have no clearance limits
    
    if requested_org > inviter_org_max:
        return False, f"Cannot assign organization clearance higher than your own level ({inviter_org_max})"
    
    if requested_dept is not None:
        if inviter_dept_max is None:
            return False, "You do not have department clearance to assign"
        if requested_dept > inviter_dept_max:
            return False, f"Cannot assign department clearance higher than your own level ({inviter_dept_max})"
    
    return True, None


async def handle_invite_user(
    email: str,
    role_id: int,
    admin_user: User,
    invitation_link_template: Optional[str],
    invitation_message: Optional[str] = None,
    department_id: Optional[int] = None,
    is_manager: bool = False,
    org_level_permission: int = 1,
    department_level_permission: Optional[int] = None,
    session: AsyncSession = None
) -> dict:
    """
    Send invitation to new user with optional department assignment.
    
    Enforces role-based authorization:
    - Admins can invite to any department with any clearance
    - Department managers can only invite to their own department with clearance <= their own
    
    Args:
        email: Email address to invite
        role_id: Role to assign to invited user
        admin_user: Admin user sending the invitation
        invitation_link_template: Optional frontend link template
        invitation_message: Optional custom message for invitation
        department_id: Optional department to assign user to
        is_manager: Whether to make user a manager of the department
        org_level_permission: Organization-wide clearance level (1-4)
        department_level_permission: Department-specific clearance level (1-4)
        session: Database session
    
    Returns:
        Dict with success status and message
    """
    try:
        # Get inviter's clearance from cache
        inviter_clearance = await get_user_clearance_cache(admin_user.id, session)
        if not inviter_clearance:
            logger.warning(f"Failed to get clearance cache for user {admin_user.id}")
            return {"success": False, "error": "Could not verify your permissions. Please try again."}
        
        # Check if inviter can invite to target department
        can_invite, invite_error = can_invite_user(inviter_clearance, department_id)
        if not can_invite:
            logger.warning(f"User {admin_user.id} unauthorized to invite to dept {department_id}: {invite_error}")
            return {"success": False, "error": invite_error}
        
        # Validate clearance limits
        is_admin = inviter_clearance.get("is_admin", False)
        inviter_org_max = inviter_clearance.get("org_clearance_value", 1)
        inviter_dept_max = inviter_clearance.get("dept_clearance_value")
        
        clearance_valid, clearance_error = validate_clearance_limits(
            org_level_permission,
            department_level_permission,
            inviter_org_max,
            inviter_dept_max,
            is_admin
        )
        if not clearance_valid:
            logger.warning(f"User {admin_user.id} clearance validation failed: {clearance_error}")
            return {"success": False, "error": clearance_error}
        
        # Get role name
        result = await session.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            logger.warning(f"Role {role_id} not found for invitation by admin {admin_user.id}")
            return {"success": False, "error": "The specified role does not exist"}
        
        # Create invitation via service with clearance fields
        service = InvitationService(session)
        invitation, error = await service.create_invitation(
            email=email,
            inviter_id=admin_user.id,
            role_name=role.name,
            custom_message=invitation_message,
            department_id=department_id,
            is_manager=is_manager,
            org_level_permission=org_level_permission,
            department_level_permission=department_level_permission,
            invitation_link_template=invitation_link_template,
        )
        
        if error:
            logger.warning(f"Failed to create invitation for {email}: {error}")
            # Return user-friendly error message
            if "already exists" in error.lower():
                return {"success": False, "error": "This email is already registered or has a pending invitation"}
            return {"success": False, "error": "Could not send invitation. Please try again."}
        
        logger.info(f"Invitation sent to {email} by admin {admin_user.id} for role {role.name}")
        return {
            "success": True,
            "message": f"Invitation sent to {email}",
            "invitation_id": invitation["id"],
        }
    except Exception as e:
        logger.error(f"Error creating invitation for {email}: {str(e)}", exc_info=True)
        return {"success": False, "error": "An unexpected error occurred. Please try again."}


async def handle_list_invitations(
    status_filter: Optional[str],
    limit: int,
    offset: int,
    session: AsyncSession
) -> dict:
    """
    Handle list user invitations request.
    
    Delegates to InvitationService for all business logic.
    
    Args:
        status_filter: Filter by invitation status (pending, accepted, expired)
        limit: Pagination limit
        offset: Pagination offset
        session: Database session
        
    Returns:
        Dict with invitations list and total count
    """
    try:
        service = InvitationService(session)
        result, error = await service.list_invitations(status_filter, limit, offset)
        
        if error:
            logger.error(f"Error listing invitations: {error}")
            return {"success": False, "error": "Could not retrieve invitations. Please try again."}
        
        return {
            "success": True,
            "total": result.get("total", 0),
            "limit": result.get("limit", limit),
            "offset": result.get("offset", offset),
            "invitations": result.get("invitations", [])
        }
    except Exception as e:
        logger.error(f"Error handling list invitations: {str(e)}", exc_info=True)
        return {"success": False, "error": "Could not retrieve invitations. Please try again."}


async def handle_resend_invitation(
    invitation_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle resending invitation email.
    
    Delegates to InvitationService for all business logic.
    
    Args:
        invitation_id: Invitation ID to resend
        session: Database session
        
    Returns:
        Dict with success/error status
    """
    try:
        service = InvitationService(session)
        success, error = await service.resend_invitation(invitation_id)
        
        if error:
            # Provide user-friendly error messages
            if "not found" in error.lower():
                logger.warning(f"Attempt to resend non-existent invitation {invitation_id}")
                return {"success": False, "error": "Invitation not found"}
            elif "expired" in error.lower():
                logger.info(f"Attempt to resend expired invitation {invitation_id}")
                return {"success": False, "error": "Invitation has expired. Please create a new one."}
            else:
                logger.warning(f"Failed to resend invitation {invitation_id}: {error}")
                return {"success": False, "error": "Could not resend invitation. Please try again."}
        
        logger.info(f"Successfully resent invitation {invitation_id}")
        return {"success": True, "message": "Invitation resent successfully"}
    except Exception as e:
        logger.error(f"Error resending invitation {invitation_id}: {str(e)}", exc_info=True)
        return {"success": False, "error": "An unexpected error occurred. Please try again."}

