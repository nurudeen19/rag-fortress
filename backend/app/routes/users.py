"""
Admin user management routes.

Routes delegate request handling to handlers for business logic separation.
Requires "admin" role for access.

Endpoints:
- GET  /api/v1/admin/users - List all users (paginated)
- GET  /api/v1/admin/users/{user_id} - Get user details
- POST /api/v1/admin/users/{user_id}/suspend - Suspend user
- POST /api/v1/admin/users/{user_id}/unsuspend - Unsuspend user
- GET  /api/v1/admin/users/{user_id}/roles - Get user roles
- POST /api/v1/admin/users/{user_id}/roles - Assign role to user
- DELETE /api/v1/admin/users/{user_id}/roles/{role_id} - Revoke role
- GET  /api/v1/admin/roles - List all roles
- POST /api/v1/admin/roles - Create new role
- GET  /api/v1/admin/permissions - List all permissions
- POST /api/v1/admin/permissions - Create new permission
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user, require_role, require_admin_or_department_manager
from app.schemas.user import (
    UserResponse,
    UserDetailResponse,
    UserListResponse,
    RoleResponse,
    RoleDetailResponse,
    RoleListResponse,
    PermissionResponse,
    RoleAssignRequest,
    RoleRevokeRequest,
    UserSuspendRequest,
    UserInviteRequest,
    CreateRoleRequest,
    CreatePermissionRequest,
    AssignPermissionToRoleRequest,
    RevokePermissionFromRoleRequest,
    SuccessResponse,
    InvitationsListResponse,
    InvitationLimitsResponse,
    ClearanceLevelOption,
)
from app.models.user import User
from app.core import get_logger
from app.handlers.users import (
    handle_list_users,
    handle_get_user,
    handle_suspend_user,
    handle_unsuspend_user,
    handle_invite_user,
    handle_get_user_roles,
    handle_assign_role_to_user,
    handle_revoke_role_from_user,
    handle_list_roles,
    handle_create_role,
    handle_list_permissions,
    handle_create_permission,
    handle_assign_permission_to_role,
    handle_revoke_permission_from_role,
    handle_list_invitations,
    handle_resend_invitation,
)


logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ============================================================================
# USER MANAGEMENT (ADMIN)
# ============================================================================

@router.get("/users", response_model=UserListResponse)
async def list_users(
    active_only: bool = Query(True, description="Only active users"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    List users with optional filtering.
    
    Requires admin role.
    """
    result = await handle_list_users(
        active_only=active_only,
        department_id=department_id,
        limit=limit,
        offset=offset,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to list users")
        )
    
    return UserListResponse(
        total=result["total"],
        limit=limit,
        offset=offset,
        users=[UserDetailResponse(**u) for u in result["users"]]
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: int,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Get user details by ID. Requires admin role."""
    result = await handle_get_user(user_id, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "User not found")
        )
    
    return UserResponse(**result["user"])


@router.post("/users/{user_id}/suspend", response_model=SuccessResponse)
async def suspend_user(
    user_id: int,
    request: UserSuspendRequest,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Suspend user account. Requires admin role."""
    result = await handle_suspend_user(
        user_id=user_id,
        reason=request.reason or "",
        admin_user=admin,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to suspend user")
        )
    
    return SuccessResponse(message=result.get("message", "User suspended"))


@router.post("/users/{user_id}/unsuspend", response_model=SuccessResponse)
async def unsuspend_user(
    user_id: int,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Unsuspend user account. Requires admin role."""
    result = await handle_unsuspend_user(
        user_id=user_id,
        admin_user=admin,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to unsuspend user")
        )
    
    return SuccessResponse(message=result.get("message", "User unsuspended"))


@router.get("/users/me/invitation-limits", response_model=InvitationLimitsResponse)
async def get_invitation_limits(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get invitation limits and permissions for current user.
    
    Returns information about:
    - Whether user can send invitations
    - Whether user is admin or department manager
    - Which departments user can invite to
    - Maximum clearance levels user can assign
    - Available clearance level options
    """
    from app.utils.user_clearance_cache import get_user_clearance_cache
    from sqlalchemy import select
    from app.models.department import Department
    
    # Get user clearance from cache
    clearance = await get_user_clearance_cache(current_user.id, session)
    
    if not clearance:
        # User cannot invite if clearance not found
        return InvitationLimitsResponse(
            can_invite=False,
            is_admin=False,
            is_department_manager=False,
            allowed_departments=None,
            max_org_clearance=1,
            max_dept_clearance=None,
            clearance_levels=[]
        )
    
    is_admin = clearance.get("is_admin", False)
    is_dept_manager = clearance.get("is_department_manager", False)
    can_invite = is_admin or is_dept_manager
    
    # Determine allowed departments
    allowed_departments = None  # None means all for admins
    if is_dept_manager and not is_admin:
        # Department managers can only invite to their own department
        dept_id = clearance.get("department_id")
        allowed_departments = [dept_id] if dept_id else []
    
    # Get clearance values
    max_org_clearance = clearance.get("org_clearance_value", 1)
    max_dept_clearance = clearance.get("dept_clearance_value")
    
    # Build clearance level options
    clearance_levels = [
        ClearanceLevelOption(value=1, label="GENERAL"),
        ClearanceLevelOption(value=2, label="RESTRICTED"),
        ClearanceLevelOption(value=3, label="CONFIDENTIAL"),
        ClearanceLevelOption(value=4, label="HIGHLY_CONFIDENTIAL"),
    ]
    
    return InvitationLimitsResponse(
        can_invite=can_invite,
        is_admin=is_admin,
        is_department_manager=is_dept_manager,
        allowed_departments=allowed_departments,
        max_org_clearance=max_org_clearance,
        max_dept_clearance=max_dept_clearance,
        clearance_levels=clearance_levels
    )


@router.post("/users/invite", response_model=SuccessResponse)
async def invite_user(
    request: UserInviteRequest,
    inviter: User = Depends(require_admin_or_department_manager),
    session: AsyncSession = Depends(get_session)
):
    """
    Send invitation to new user with optional department assignment.
    
    Requires admin role or department manager status.
    - Admins can invite to any department with any clearance level
    - Department managers can only invite to their own department with clearance <= their own
    """
    result = await handle_invite_user(
        email=request.email,
        role_id=request.role_id,
        admin_user=inviter,
        invitation_message=request.invitation_message,
        department_id=request.department_id,
        is_manager=request.is_manager,
        org_level_permission=request.org_level_permission,
        department_level_permission=request.department_level_permission,
        invitation_link_template=request.invitation_link_template,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to send invitation")
        )
    
    return SuccessResponse(message=result.get("message", "Invitation sent"))


# ============================================================================
# ROLE MANAGEMENT (ADMIN)
# ============================================================================

@router.get("/users/{user_id}/roles", response_model=list[RoleResponse])
async def get_user_roles(
    user_id: int,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Get all roles assigned to user. Requires admin role."""
    result = await handle_get_user_roles(user_id, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to get user roles")
        )
    
    return [RoleResponse(**r) for r in result["roles"]]


@router.post("/users/{user_id}/roles", response_model=SuccessResponse)
async def assign_role_to_user(
    user_id: int,
    request: RoleAssignRequest,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Assign role to user. Requires admin role."""
    result = await handle_assign_role_to_user(
        user_id=user_id,
        role_id=request.role_id,
        admin_user=admin,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to assign role")
        )
    
    return SuccessResponse(message=result.get("message", "Role assigned"))


@router.delete("/users/{user_id}/roles/{role_id}", response_model=SuccessResponse)
async def revoke_role_from_user(
    user_id: int,
    role_id: int,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Revoke role from user. Requires admin role."""
    result = await handle_revoke_role_from_user(
        user_id=user_id,
        role_id=role_id,
        admin_user=admin,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to revoke role")
        )
    
    return SuccessResponse(message=result.get("message", "Role revoked"))


@router.get("/roles", response_model=RoleListResponse)
async def list_roles(
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """List all available roles. Requires admin role."""
    result = await handle_list_roles(session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to list roles")
        )
    
    return RoleListResponse(
        roles=[
            RoleDetailResponse(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                is_system=r["is_system"],
                permissions=[PermissionResponse(**p) for p in r.get("permissions", [])]
            )
            for r in result["roles"]
        ]
    )


@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    request: CreateRoleRequest,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Create new role. Requires admin role."""
    result = await handle_create_role(
        name=request.name,
        description=request.description or "",
        is_system=request.is_system,
        admin_user=admin,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to create role")
        )
    
    return RoleResponse(**result["role"])


# ============================================================================
# PERMISSION MANAGEMENT (ADMIN)
# ============================================================================

@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    resource: Optional[str] = Query(None, description="Filter by resource"),
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """List all permissions, optionally filtered by resource. Requires admin role."""
    result = await handle_list_permissions(resource=resource, session=session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to list permissions")
        )
    
    return [PermissionResponse(**p) for p in result["permissions"]]


@router.post("/permissions", response_model=PermissionResponse, status_code=201)
async def create_permission(
    request: CreatePermissionRequest,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Create new permission. Requires admin role."""
    result = await handle_create_permission(
        code=request.code,
        resource=request.resource,
        action=request.action,
        description=request.description or "",
        admin_user=admin,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to create permission")
        )
    
    return PermissionResponse(**result["permission"])


@router.post("/roles/{role_id}/permissions", response_model=SuccessResponse)
async def assign_permission_to_role(
    role_id: int,
    request: AssignPermissionToRoleRequest,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Assign permission to role. Requires admin role."""
    result = await handle_assign_permission_to_role(
        role_id=role_id,
        permission_id=request.permission_id,
        admin_user=admin,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to assign permission")
        )
    
    return SuccessResponse(message=result.get("message", "Permission assigned"))


@router.delete("/roles/{role_id}/permissions/{permission_id}", response_model=SuccessResponse)
async def revoke_permission_from_role(
    role_id: int,
    permission_id: int,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """Revoke permission from role. Requires admin role."""
    result = await handle_revoke_permission_from_role(
        role_id=role_id,
        permission_id=permission_id,
        admin_user=admin,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to revoke permission")
        )
    
    return SuccessResponse(message=result.get("message", "Permission revoked"))


# ============================================================================
# INVITATION MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/invitations", response_model=InvitationsListResponse)
async def list_invitations(
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, accepted, expired"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    List all user invitations with filtering and pagination.
    
    Requires admin role.
    
    Query Parameters:
    - status_filter: Filter by invitation status (pending, accepted, expired)
    - limit: Number of results per page (1-100, default: 10)
    - offset: Pagination offset (default: 0)
    
    Returns:
        Paginated list of invitations with their details
    """
    from app.handlers.users import handle_list_invitations
    
    result = await handle_list_invitations(
        status_filter=status_filter,
        limit=limit,
        offset=offset,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to list invitations")
        )
    
    return InvitationsListResponse(
        total=result.get("total", 0),
        limit=result.get("limit", limit),
        offset=result.get("offset", offset),
        invitations=result.get("invitations", [])
    )


@router.post("/invitations/{invitation_id}/resend", response_model=SuccessResponse)
async def resend_invitation(
    invitation_id: int,
    admin: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    Resend invitation email for a pending invitation.
    
    Requires admin role.
    
    Path Parameters:
    - invitation_id: ID of the invitation to resend
    
    Returns:
        Success message or error
    """
    from app.handlers.users import handle_resend_invitation
    
    result = await handle_resend_invitation(
        invitation_id=invitation_id,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to resend invitation")
        )
    
    return SuccessResponse(message=result.get("message", "Invitation resent"))

