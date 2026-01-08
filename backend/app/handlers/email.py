"""
Email request handlers with business logic.

Handlers manage validation, business rules, and coordinate with email service.
"""

import logging


from app.services.email import get_email_service
from app.schemas.email import (
    AccountActivationRequest,
    PasswordResetRequest,
    InvitationRequest,
    NotificationRequest,
    BulkNotificationRequest,
)

logger = logging.getLogger(__name__)


async def handle_account_activation(
    request: AccountActivationRequest
) -> dict:
    """
    Handle account activation email request.
    
    Args:
        request: Account activation request data
        
    Returns:
        Dict with success status and recipient info
    """
    try:
        logger.info(f"Processing account activation for {request.recipient_email}")
        
        # Get email service
        email_service = get_email_service()
        
        # Send activation email
        success = await email_service.send_account_activation(
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            activation_token=request.activation_token
        )
        
        if not success:
            logger.warning(f"Failed to send activation email to {request.recipient_email}")
            return {
                "success": False,
                "error": "Failed to send activation email",
                "recipient": str(request.recipient_email)
            }
        
        logger.info(f"Account activation email sent successfully to {request.recipient_email}")
        return {
            "success": True,
            "recipient": str(request.recipient_email)
        }
        
    except Exception as e:
        logger.error(
            f"Error handling account activation request: {str(e)}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "recipient": str(request.recipient_email) if request else None
        }


async def handle_password_reset(
    request: PasswordResetRequest
) -> dict:
    """
    Handle password reset email request.
    
    Args:
        request: Password reset request data
        
    Returns:
        Dict with success status and recipient info
    """
    try:
        logger.info(f"Processing password reset for {request.recipient_email}")
        
        # Get email service
        email_service = get_email_service()
        
        # Send password reset email
        success = await email_service.send_password_reset(
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            reset_token=request.reset_token
        )
        
        if not success:
            logger.warning(f"Failed to send password reset email to {request.recipient_email}")
            return {
                "success": False,
                "error": "Failed to send password reset email",
                "recipient": str(request.recipient_email)
            }
        
        logger.info(f"Password reset email sent successfully to {request.recipient_email}")
        return {
            "success": True,
            "recipient": str(request.recipient_email)
        }
        
    except Exception as e:
        logger.error(
            f"Error handling password reset request: {str(e)}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "recipient": str(request.recipient_email) if request else None
        }


async def handle_invitation(
    request: InvitationRequest
) -> dict:
    """
    Handle team invitation email request.
    
    Args:
        request: Invitation request data
        
    Returns:
        Dict with success status and recipient info
    """
    try:
        logger.info(f"Processing invitation for {request.recipient_email}")
        
        # Get email service
        email_service = get_email_service()
        
        # Send invitation email
        success = await email_service.send_invitation(
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            inviter_name=request.inviter_name,
            organization_name=request.organization_name,
            invitation_token=request.invitation_token,
            custom_message=request.custom_message or ""
        )
        
        if not success:
            logger.warning(f"Failed to send invitation email to {request.recipient_email}")
            return {
                "success": False,
                "error": "Failed to send invitation email",
                "recipient": str(request.recipient_email)
            }
        
        logger.info(f"Invitation email sent successfully to {request.recipient_email}")
        return {
            "success": True,
            "recipient": str(request.recipient_email)
        }
        
    except Exception as e:
        logger.error(
            f"Error handling invitation request: {str(e)}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "recipient": str(request.recipient_email) if request else None
        }


async def handle_notification(
    request: NotificationRequest
) -> dict:
    """
    Handle notification email request.
    
    Args:
        request: Notification request data
        
    Returns:
        Dict with success status and recipient info
    """
    try:
        logger.info(f"Processing notification for {request.recipient_email}")
        
        # Get email service
        email_service = get_email_service()
        
        # Send notification email
        success = await email_service.send_notification(
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            notification_title=request.notification_title,
            notification_message=request.notification_message,
            action_url=request.action_url or "",
            action_text=request.action_text or "View Details"
        )
        
        if not success:
            logger.warning(f"Failed to send notification email to {request.recipient_email}")
            return {
                "success": False,
                "error": "Failed to send notification email",
                "recipient": str(request.recipient_email)
            }
        
        logger.info(f"Notification email sent successfully to {request.recipient_email}")
        return {
            "success": True,
            "recipient": str(request.recipient_email)
        }
        
    except Exception as e:
        logger.error(
            f"Error handling notification request: {str(e)}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "recipient": str(request.recipient_email) if request else None
        }


async def handle_bulk_notification(
    request: BulkNotificationRequest
) -> dict:
    """
    Handle bulk notification email request.
    
    Args:
        request: Bulk notification request data
        
    Returns:
        Dict with success count, failed recipients, and total
    """
    try:
        logger.info(f"Processing bulk notification for {len(request.recipients)} recipients")
        
        # Get email service
        email_service = get_email_service()
        
        # Send bulk notification
        result = await email_service.send_bulk_notification(
            recipients=request.recipients,
            notification_title=request.notification_title,
            notification_message=request.notification_message,
            action_url=request.action_url or "",
            action_text=request.action_text or "View Details"
        )
        
        logger.info(
            f"Bulk notification completed: {result['success_count']}/{result['total']} successful"
        )
        
        return {
            "success": result['success_count'] > 0,
            **result
        }
        
    except Exception as e:
        logger.error(
            f"Error handling bulk notification request: {str(e)}",
            exc_info=True
        )
        return {
            "success": False,
            "error": str(e),
            "success_count": 0,
            "failed": request.recipients if request else [],
            "total": len(request.recipients) if request else 0
        }
