"""
Specialized email builders for different email types.

Each builder handles construction and sending of specific email types
following the builder pattern for extensibility.
"""

import logging
from typing import List
from abc import ABC, abstractmethod

from pydantic import EmailStr

from app.config.settings import settings
from app.core import get_email_client
from ..templates import (
    render_account_activation_email,
    render_password_reset_email,
    render_password_changed_email,
    render_invitation_email,
    render_notification_email,
)

logger = logging.getLogger(__name__)


class BaseEmailBuilder(ABC):
    """
    Abstract base class for email builders.
    
    Provides common functionality for all email types.
    """
    
    def __init__(self):
        """Initialize builder with email client."""
        self._client = get_email_client()
    
    @abstractmethod
    async def build_and_send(self, *args, **kwargs) -> bool:
        """
        Build and send email.
        
        Must be implemented by subclasses.
        """


class AccountActivationEmailBuilder(BaseEmailBuilder):
    """Builder for account activation emails."""
    
    async def build_and_send(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        activation_token: str
    ) -> bool:
        """
        Build and send account activation email.
        
        Args:
            recipient_email: Email address of recipient
            recipient_name: Name of recipient
            activation_token: Activation token for verification
            
        Returns:
            True if sent successfully
        """
        try:
            # Build activation URL
            activation_url = f"{settings.EMAIL_VERIFICATION_URL}?token={activation_token}"
            
            # Render email
            subject, html_body = render_account_activation_email(
                recipient_name=recipient_name,
                activation_url=activation_url
            )
            
            # Send email
            success = await self._client.send_email(
                recipient=recipient_email,
                subject=subject,
                html_body=html_body
            )
            
            if success:
                logger.info(f"Account activation email sent to {recipient_email}")
            else:
                logger.warning(f"Failed to send activation email to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(
                f"Error building/sending activation email to {recipient_email}: {str(e)}",
                exc_info=True
            )
            return False


class PasswordResetEmailBuilder(BaseEmailBuilder):
    """Builder for password reset emails."""
    
    async def build_and_send(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        reset_token: str,
        reset_link_template: str = None
    ) -> bool:
        """
        Build and send password reset email.
        
        Args:
            recipient_email: Email address of recipient
            recipient_name: Name of recipient
            reset_token: Password reset token
            reset_link_template: Optional frontend-provided link template with {token} placeholder
            
        Returns:
            True if sent successfully
        """
        try:
            # Build reset URL using template if provided, otherwise use default
            if reset_link_template and "{token}" in reset_link_template:
                # Frontend provided a link template - use it
                reset_url = reset_link_template.replace("{token}", reset_token)
                logger.info(f"Using frontend-provided reset link template for {recipient_email}")
            else:
                # Fallback to default - use FRONTEND_URL as base
                reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
                logger.info(f"Using default reset link for {recipient_email}")
            
            # Render email
            subject, html_body = render_password_reset_email(
                recipient_name=recipient_name,
                reset_url=reset_url
            )
            
            # Send email
            success = await self._client.send_email(
                recipient=recipient_email,
                subject=subject,
                html_body=html_body
            )
            
            if success:
                logger.info(f"Password reset email sent to {recipient_email}")
            else:
                logger.warning(f"Failed to send password reset email to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(
                f"Error building/sending password reset email to {recipient_email}: {str(e)}",
                exc_info=True
            )
            return False


class PasswordChangedEmailBuilder(BaseEmailBuilder):
    """Builder for password changed notification emails."""
    
    async def build_and_send(
        self,
        recipient_email: EmailStr,
        recipient_name: str
    ) -> bool:
        """
        Build and send password changed notification email.
        
        Args:
            recipient_email: Email address of recipient
            recipient_name: Name of recipient
            
        Returns:
            True if sent successfully
        """
        try:
            # Render email
            subject, html_body = render_password_changed_email(
                recipient_name=recipient_name
            )
            
            # Send email
            success = await self._client.send_email(
                recipient=recipient_email,
                subject=subject,
                html_body=html_body
            )
            
            if success:
                logger.info(f"Password changed notification sent to {recipient_email}")
            else:
                logger.warning(f"Failed to send password changed notification to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(
                f"Error building/sending password changed notification to {recipient_email}: {str(e)}",
                exc_info=True
            )
            return False


class InvitationEmailBuilder(BaseEmailBuilder):
    """Builder for team invitation emails."""
    
    async def build_and_send(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        inviter_name: str,
        organization_name: str,
        invitation_token: str,
        custom_message: str = "",
        invitation_link_template: str = None
    ) -> bool:
        """
        Build and send invitation email.
        
        Args:
            recipient_email: Email address of recipient
            recipient_name: Name of recipient
            inviter_name: Name of person sending invitation
            organization_name: Name of organization/team
            invitation_token: Invitation token
            custom_message: Optional custom message
            invitation_link_template: Optional frontend-provided link template with {token} placeholder
            
        Returns:
            True if sent successfully
        """
        try:
            # Build invitation URL using template if provided, otherwise use default
            if invitation_link_template and "{token}" in invitation_link_template:
                # Frontend provided a link template - use it
                invitation_url = invitation_link_template.replace("{token}", invitation_token)
                logger.info(f"Using frontend-provided invitation link template for {recipient_email}")
            else:
                # Fallback to default - use FRONTEND_URL as base
                invitation_url = f"{settings.FRONTEND_URL}/accept-invite?token={invitation_token}"
                logger.info(f"Using default invitation link for {recipient_email}")
            
            # Render email
            subject, html_body = render_invitation_email(
                recipient_name=recipient_name,
                inviter_name=inviter_name,
                organization_name=organization_name,
                invitation_url=invitation_url,
                custom_message=custom_message
            )
            
            # Send email
            success = await self._client.send_email(
                recipient=recipient_email,
                subject=subject,
                html_body=html_body
            )
            
            if success:
                logger.info(f"Invitation email sent to {recipient_email}")
            else:
                logger.warning(f"Failed to send invitation email to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(
                f"Error building/sending invitation email to {recipient_email}: {str(e)}",
                exc_info=True
            )
            return False


class NotificationEmailBuilder(BaseEmailBuilder):
    """Builder for generic notification emails."""
    
    async def build_and_send(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        notification_title: str,
        notification_message: str,
        action_url: str = "",
        action_text: str = "View Details"
    ) -> bool:
        """
        Build and send notification email.
        
        Args:
            recipient_email: Email address of recipient
            recipient_name: Name of recipient
            notification_title: Title of notification
            notification_message: Notification message content
            action_url: Optional action button URL
            action_text: Text for action button
            
        Returns:
            True if sent successfully
        """
        try:
            # Render email
            subject, html_body = render_notification_email(
                recipient_name=recipient_name,
                notification_title=notification_title,
                notification_message=notification_message,
                action_url=action_url,
                action_text=action_text
            )
            
            # Send email
            success = await self._client.send_email(
                recipient=recipient_email,
                subject=subject,
                html_body=html_body
            )
            
            if success:
                logger.info(f"Notification email sent to {recipient_email}")
            else:
                logger.warning(f"Failed to send notification email to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(
                f"Error building/sending notification email to {recipient_email}: {str(e)}",
                exc_info=True
            )
            return False


class BulkNotificationEmailBuilder(BaseEmailBuilder):
    """Builder for bulk notification emails."""
    
    async def build_and_send(self, *args, **kwargs) -> bool:
        """
        Abstract method implementation (not used for bulk).
        
        Use build_and_send_bulk instead.
        """
        raise NotImplementedError("Use build_and_send_bulk for bulk notifications")
    
    async def build_and_send_bulk(
        self,
        recipients: List[EmailStr],
        notification_title: str,
        notification_message: str,
        action_url: str = "",
        action_text: str = "View Details"
    ) -> dict:
        """
        Build and send bulk notification emails.
        
        Args:
            recipients: List of recipient email addresses
            notification_title: Title of notification
            notification_message: Notification message content
            action_url: Optional action button URL
            action_text: Text for action button
            
        Returns:
            Dict with success count and failed recipients
        """
        try:
            # Render email (using generic recipient name for bulk)
            subject, html_body = render_notification_email(
                recipient_name="Team Member",
                notification_title=notification_title,
                notification_message=notification_message,
                action_url=action_url,
                action_text=action_text
            )
            
            # Send bulk email
            result = await self._client.send_bulk_email(
                recipients=recipients,
                subject=subject,
                html_body=html_body
            )
            
            logger.info(
                f"Bulk notification sent: {result['success_count']}/{result['total']} successful"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error building/sending bulk notification email: {str(e)}",
                exc_info=True
            )
            return {
                "success_count": 0,
                "failed": recipients,
                "total": len(recipients)
            }
