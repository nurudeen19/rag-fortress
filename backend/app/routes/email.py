"""
Email routes for sending transactional and notification emails.

Provides endpoints for triggering account activation, password reset,
invitation, and general notification emails.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import EmailStr

from app.services.email_service import (
    send_account_activation_email,
    send_password_reset_email,
    send_invitation_email,
    send_notification_email,
    email_builder,
)
from app.schemas.email import (
    EmailRequest,
    AccountActivationRequest,
    PasswordResetRequest,
    InvitationRequest,
    BulkNotificationRequest,
    EmailResponse,
    BulkEmailResponse,
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
    description="Send email with account verification link to new user",
)
async def send_account_activation(
    request: AccountActivationRequest,
) -> Dict[str, Any]:
    """
    Send account activation/verification email.
    
    This endpoint sends an email to the provided address with a link
    to verify and activate the account. The link includes a token
    that expires after 24 hours.
    
    Args:
        request: AccountActivationRequest with recipient info and token
    
    Returns:
        EmailResponse with success status and message
    
    Raises:
        HTTPException: If email sending fails
    """
    try:
        logger.info(f"Sending account activation email to {request.recipient_email}")
        
        success = await send_account_activation_email(
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            activation_token=request.activation_token,
        )
        
        if not success:
            logger.warning(f"Failed to send activation email to {request.recipient_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send activation email. Please try again later.",
            )
        
        return EmailResponse(
            success=True,
            message="Account activation email sent successfully",
            recipient=request.recipient_email,
            timestamp=_get_timestamp(),
        ).dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending account activation email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending the email.",
        )


@router.post(
    "/password-reset",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send Password Reset Email",
    description="Send email with password reset link to user",
)
async def send_password_reset(
    request: PasswordResetRequest,
) -> Dict[str, Any]:
    """
    Send password reset email.
    
    This endpoint sends an email with a link to reset the user's password.
    The link includes a token that expires after 1 hour.
    
    Args:
        request: PasswordResetRequest with recipient info and token
    
    Returns:
        EmailResponse with success status and message
    
    Raises:
        HTTPException: If email sending fails
    """
    try:
        logger.info(f"Sending password reset email to {request.recipient_email}")
        
        success = await send_password_reset_email(
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            reset_token=request.reset_token,
        )
        
        if not success:
            logger.warning(f"Failed to send password reset email to {request.recipient_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email. Please try again later.",
            )
        
        return EmailResponse(
            success=True,
            message="Password reset email sent successfully",
            recipient=request.recipient_email,
            timestamp=_get_timestamp(),
        ).dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending the email.",
        )


@router.post(
    "/invitation",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send User Invitation Email",
    description="Send invitation email to prospective user",
)
async def send_user_invitation(
    request: InvitationRequest,
) -> Dict[str, Any]:
    """
    Send user invitation email.
    
    This endpoint sends an invitation to a user to join a team or workspace.
    The link includes a token that expires after 7 days.
    
    Args:
        request: InvitationRequest with recipient info and token
    
    Returns:
        EmailResponse with success status and message
    
    Raises:
        HTTPException: If email sending fails
    """
    try:
        logger.info(f"Sending invitation email to {request.recipient_email}")
        
        success = await send_invitation_email(
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            inviter_name=request.inviter_name,
            invite_token=request.invite_token,
            message=request.message,
        )
        
        if not success:
            logger.warning(f"Failed to send invitation email to {request.recipient_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send invitation email. Please try again later.",
            )
        
        return EmailResponse(
            success=True,
            message="Invitation email sent successfully",
            recipient=request.recipient_email,
            timestamp=_get_timestamp(),
        ).dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending invitation email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending the email.",
        )


@router.post(
    "/notification",
    response_model=EmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send General Notification Email",
    description="Send customizable notification email to user",
)
async def send_notification(
    request: EmailRequest,
) -> Dict[str, Any]:
    """
    Send generic notification email.
    
    This endpoint sends a customizable notification email with optional
    call-to-action button.
    
    Args:
        request: EmailRequest with recipient info and email content
    
    Returns:
        EmailResponse with success status and message
    
    Raises:
        HTTPException: If email sending fails
    """
    try:
        logger.info(f"Sending notification email to {request.recipient_email}")
        
        success = await send_notification_email(
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            subject=request.subject,
            title=request.title,
            message=request.message,
            action_url=request.action_url,
            action_text=request.action_text,
        )
        
        if not success:
            logger.warning(f"Failed to send notification email to {request.recipient_email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send notification email. Please try again later.",
            )
        
        return EmailResponse(
            success=True,
            message="Notification email sent successfully",
            recipient=request.recipient_email,
            timestamp=_get_timestamp(),
        ).dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending the email.",
        )


@router.post(
    "/bulk-notification",
    response_model=BulkEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send Bulk Notification Email",
    description="Send notification email to multiple recipients",
)
async def send_bulk_notification(
    request: BulkNotificationRequest,
) -> Dict[str, Any]:
    """
    Send notification email to multiple recipients.
    
    This endpoint sends the same notification email to multiple users.
    Each email is personalized with the recipient's name.
    
    Args:
        request: BulkNotificationRequest with recipients and email content
    
    Returns:
        BulkEmailResponse with success status and per-recipient results
    
    Raises:
        HTTPException: If bulk send operation fails
    """
    try:
        if not request.recipients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one recipient is required.",
            )
        
        logger.info(f"Sending bulk notification to {len(request.recipients)} recipients")
        
        results = await email_builder.send_bulk_notification(
            recipients=request.recipients,
            subject=request.subject,
            title=request.title,
            message=request.message,
            action_url=request.action_url,
            action_text=request.action_text,
        )
        
        sent_count = sum(1 for success in results.values() if success)
        failed_count = len(results) - sent_count
        
        return BulkEmailResponse(
            success=failed_count == 0,
            total=len(results),
            sent=sent_count,
            failed=failed_count,
            results=results,
            timestamp=_get_timestamp(),
        ).dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending bulk notification emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending bulk emails.",
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Email Service Health Check",
    description="Check if email service is configured and working",
)
async def email_health() -> Dict[str, Any]:
    """
    Check email service health.
    
    Returns information about email service configuration and availability.
    
    Returns:
        Dict with service status and configuration details
    """
    try:
        from app.config.settings import settings
        
        # Basic validation of configuration
        has_smtp_config = (
            settings.SMTP_USERNAME and
            settings.SMTP_PASSWORD and
            settings.SMTP_SERVER
        )
        
        return {
            "status": "healthy" if has_smtp_config else "unconfigured",
            "smtp_configured": has_smtp_config,
            "smtp_server": settings.SMTP_SERVER if has_smtp_config else None,
            "smtp_port": settings.SMTP_PORT,
            "from_email": settings.SMTP_FROM_EMAIL,
            "tls_enabled": settings.SMTP_USE_TLS,
            "ssl_enabled": settings.SMTP_USE_SSL,
            "timestamp": _get_timestamp(),
        }
    
    except Exception as e:
        logger.error(f"Error checking email service health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking email service health.",
        )
