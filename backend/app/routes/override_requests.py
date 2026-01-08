"""
Permission Override Request Routes

Allows users to request temporary elevated clearance when they encounter
documents they cannot access. Department managers and admins can approve/deny requests.

Endpoints:
- POST   /api/v1/override-requests - Create new request
- GET    /api/v1/override-requests/pending - Get pending requests for approver
- GET    /api/v1/override-requests/my-requests - Get user's own requests
- POST   /api/v1/override-requests/{id}/approve - Approve request
- POST   /api/v1/override-requests/{id}/deny - Deny request
- DELETE /api/v1/override-requests/{id} - Cancel pending request
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user, require_admin_or_department_manager
from app.models.user import User
from app.models.permission_override import OverrideStatus
from app.services.override_request_service import OverrideRequestService
from app.schemas.override_request import (
    OverrideRequestCreate,
    OverrideRequestResponse,
    OverrideRequestListResponse,
    OverrideApprovalRequest,
    OverrideDenialRequest,
    SuccessResponse,
)
from app.utils.user_clearance_cache import get_user_clearance_cache
from app.core import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/override-requests", tags=["override-requests"])


@router.post("", response_model=OverrideRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_override_request(
    request_data: OverrideRequestCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new permission override request.
    
    User must provide:
    - override_type: "org_wide" or "department"
    - requested_permission_level: 1-4 (GENERAL to TOP_SECRET)
    - reason: Business justification
    - Either requested_duration_hours (preset) or custom_duration_days (custom)
    - department_id: Required for department requests
    
    Optional context:
    - trigger_query: Query that triggered this request
    - trigger_file_id: File that couldn't be accessed
    """
    service = OverrideRequestService(session)
    
    override_request, error = await service.create_request(
        requester_id=current_user.id,
        override_type=request_data.override_type,
        requested_permission_level=request_data.requested_permission_level,
        reason=request_data.reason,
        requested_duration_hours=request_data.requested_duration_hours,
        custom_duration_days=request_data.custom_duration_days,
        department_id=request_data.department_id,
        trigger_query=request_data.trigger_query,
        trigger_file_id=request_data.trigger_file_id,
    )
    
    if error:
        logger.warning(f"Override request creation failed: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    await session.commit()
    
    logger.info(
        f"Override request created: id={override_request.id}, "
        f"user={current_user.id}, type={request_data.override_type}"
    )
    
    return OverrideRequestResponse.from_orm(override_request)


@router.get("/pending", response_model=OverrideRequestListResponse)
async def get_pending_requests(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, denied, expired, revoked"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin_or_department_manager),
    session: AsyncSession = Depends(get_session),
):
    """
    Get override requests that current user can approve or view.
    
    - Admins see all requests (filtered by status if provided)
    - Department managers see requests for their department (filtered by status if provided)
    - If no status provided, defaults to 'pending'
    
    Requires admin or department_manager role.
    """
    service = OverrideRequestService(session)
    
    # Default to pending if no status specified
    status_filter = status or OverrideStatus.PENDING.value
    
    requests = await service.get_requests_for_approver(
        approver_id=current_user.id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    
    return OverrideRequestListResponse(
        requests=[OverrideRequestResponse.from_orm(req) for req in requests],
        total=len(requests),
    )


@router.get("/my-requests", response_model=OverrideRequestListResponse)
async def get_my_requests(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get current user's override requests.
    
    Optional status filter: pending, approved, denied, expired, revoked
    """
    service = OverrideRequestService(session)
    
    requests = await service.get_user_requests(
        user_id=current_user.id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    
    return OverrideRequestListResponse(
        requests=[OverrideRequestResponse.from_orm(req) for req in requests],
        total=len(requests),
    )


@router.post("/{request_id}/approve", response_model=OverrideRequestResponse)
async def approve_request(
    request_id: int,
    approval_data: OverrideApprovalRequest,
    current_user: User = Depends(require_admin_or_department_manager),
    session: AsyncSession = Depends(get_session),
):
    """
    Approve a permission override request.
    
    - Validates approver has authority (admin for org_wide, manager for department)
    - Sets status to APPROVED and activates the override
    - Sends notification to requester
    
    Requires admin or department_manager role.
    """
    service = OverrideRequestService(session)
    
    override_request, error = await service.approve_request(
        request_id=request_id,
        approver_id=current_user.id,
        approval_notes=approval_data.approval_notes,
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    await session.commit()
    
    # Invalidate user's clearance cache so they get new permissions
    cache_util = get_user_clearance_cache(session)
    await cache_util.invalidate(override_request.user_id)
    
    logger.info(
        f"Override request approved: id={request_id}, "
        f"approver={current_user.id}"
    )
    
    return OverrideRequestResponse.from_orm(override_request)


@router.post("/{request_id}/deny", response_model=SuccessResponse)
async def deny_request(
    request_id: int,
    denial_data: OverrideDenialRequest,
    current_user: User = Depends(require_admin_or_department_manager),
    session: AsyncSession = Depends(get_session),
):
    """
    Deny a permission override request.
    
    - Validates approver has authority
    - Sets status to DENIED
    - Sends notification to requester with denial reason
    
    Requires admin or department_manager role.
    """
    service = OverrideRequestService(session)
    
    success, error = await service.deny_request(
        request_id=request_id,
        approver_id=current_user.id,
        denial_reason=denial_data.denial_reason,
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    await session.commit()
    
    logger.info(
        f"Override request denied: id={request_id}, "
        f"approver={current_user.id}"
    )
    
    return SuccessResponse(
        success=True,
        message="Request denied successfully"
    )


@router.delete("/{request_id}", response_model=SuccessResponse)
async def cancel_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Cancel a pending override request.
    
    Only the requester can cancel their own pending requests.
    """
    service = OverrideRequestService(session)
    
    success, error = await service.cancel_request(
        request_id=request_id,
        requester_id=current_user.id,
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    await session.commit()
    
    logger.info(
        f"Override request cancelled: id={request_id}, "
        f"user={current_user.id}"
    )
    
    return SuccessResponse(
        success=True,
        message="Request cancelled successfully"
    )
