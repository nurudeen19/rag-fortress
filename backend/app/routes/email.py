"""
Email API routes - thin layer that delegates to handlers.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from app.schemas.email import (
    AccountActivationRequest,
    PasswordResetRequest,
    InvitationRequest,
    NotificationRequest,
    BulkNotificationRequest,
    EmailResponse,
    BulkEmailResponse,
)
from app.handlers.email import (
    handle_account_activation,
    handle_password_reset,
    handle_invitation,
    handle_notification,
    handle_bulk_notification,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/emails",
    tags=["emails"],
)


def _get_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@router.post(
    "/account-activation",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send Account Activation Email",
    description="Send account verification email to new user",
)
async def send_account_activation(
    request: AccountActivationRequest
) -> EmailResponse:
    """
    Send account activation email with verification link.
    
    Args:
        request: Account activation request data
        
    Returns:
        EmailResponse with success status
        
    Raises:
        HTTPException: If email sending fails
    """
    result = await handle_account_activation(request)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to send activation email")
        )
    
    return EmailResponse(
        success=True,
        message="Account activation email sent successfully",
        recipient=result.get("recipient"),
        timestamp=_get_timestamp()
    )


@router.post(
    "/password-reset",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send Password Reset Email",
    description="Send password reset email with reset link",
)
async def send_password_reset(
    request: PasswordResetRequest
) -> EmailResponse:
    """
    Send password reset email with reset link.
    
    Args:
        request: Password reset request data
        
    Returns:
        EmailResponse with success status
        
    Raises:
        HTTPException: If email sending fails
    """
    result = await handle_password_reset(request)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to send password reset email")
        )
    
    return EmailResponse(
        success=True,
        message="Password reset email sent successfully",
        recipient=result.get("recipient"),
        timestamp=_get_timestamp()
    )


@router.post(
    "/invitation",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send Team Invitation Email",
    description="Send invitation email to join team/organization",
)
async def send_invitation(
    request: InvitationRequest
) -> EmailResponse:
    """
    Send team invitation email.
    
    Args:
        request: Invitation request data
        
    Returns:
        EmailResponse with success status
        
    Raises:
        HTTPException: If email sending fails
    """
    result = await handle_invitation(request)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to send invitation email")
        )
    
    return EmailResponse(
        success=True,
        message="Invitation email sent successfully",
        recipient=result.get("recipient"),
        timestamp=_get_timestamp()
    )


@router.post(
    "/notification",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send Notification Email",
    description="Send notification email to single recipient",
)
async def send_notification(
    request: NotificationRequest
) -> EmailResponse:
    """
    Send notification email to single recipient.
    
    Args:
        request: Notification request data
        
    Returns:
        EmailResponse with success status
        
    Raises:
        HTTPException: If email sending fails
    """
    result = await handle_notification(request)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to send notification email")
        )
    
    return EmailResponse(
        success=True,
        message="Notification email sent successfully",
        recipient=result.get("recipient"),
        timestamp=_get_timestamp()
    )


@router.post(
    "/bulk-notification",
    response_model=BulkEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send Bulk Notification Emails",
    description="Send notification email to multiple recipients",
)
async def send_bulk_notification(
    request: BulkNotificationRequest
) -> BulkEmailResponse:
    """
    Send notification email to multiple recipients.
    
    Args:
        request: Bulk notification request data
        
    Returns:
        BulkEmailResponse with success count and failures
        
    Raises:
        HTTPException: If bulk sending completely fails
    """
    result = await handle_bulk_notification(request)
    
    # Consider partial success as success if at least one email sent
    success = result.get("success_count", 0) > 0
    total = result.get("total", 0)
    sent = result.get("success_count", 0)
    failed_list = result.get("failed", [])
    
    # Build results mapping
    results = {}
    for recipient in request.recipients:
        results[str(recipient)] = str(recipient) not in [str(f) for f in failed_list]
    
    return BulkEmailResponse(
        success=success,
        total=total,
        sent=sent,
        failed=len(failed_list),
        results=results,
        timestamp=_get_timestamp()
    )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Email Service Health Check",
    description="Check if email service is operational",
)
async def health_check():
    """
    Check email service health.
    
    Returns:
        Dict with service status
    """
    return {
        "status": "healthy",
        "service": "email",
        "timestamp": _get_timestamp()
    }
