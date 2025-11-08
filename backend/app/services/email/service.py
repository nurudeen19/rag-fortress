"""
Unified email service providing simple interface for all email operations.
"""

import logging
from typing import List, Optional

from pydantic import EmailStr

from .builders import (
    AccountActivationEmailBuilder,
    PasswordResetEmailBuilder,
    InvitationEmailBuilder,
    NotificationEmailBuilder,
    BulkNotificationEmailBuilder,
)

logger = logging.getLogger(__name__)


class EmailService:
    """
    Unified email service facade.
    
    Provides a simple, high-level interface for sending all types of emails.
    Internally uses specialized builders for different email types.
    """
    
    def __init__(self):
        """Initialize email service with all builders."""
        self.activation_builder = AccountActivationEmailBuilder()
        self.password_reset_builder = PasswordResetEmailBuilder()
        self.invitation_builder = InvitationEmailBuilder()
        self.notification_builder = NotificationEmailBuilder()
        self.bulk_notification_builder = BulkNotificationEmailBuilder()
        logger.info("Email service initialized")
    
    async def send_account_activation(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        activation_token: str
    ) -> bool:
        """
        Send account activation email.
        
        Args:
            recipient_email: Email address of recipient
            recipient_name: Name of recipient
            activation_token: Activation token for verification
            
        Returns:
            True if sent successfully
        """
        return await self.activation_builder.build_and_send(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            activation_token=activation_token
        )
    
    async def send_password_reset(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        reset_token: str
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            recipient_email: Email address of recipient
            recipient_name: Name of recipient
            reset_token: Password reset token
            
        Returns:
            True if sent successfully
        """
        return await self.password_reset_builder.build_and_send(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            reset_token=reset_token
        )
    
    async def send_invitation(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        inviter_name: str,
        organization_name: str,
        invitation_token: str,
        custom_message: str = ""
    ) -> bool:
        """
        Send team invitation email.
        
        Args:
            recipient_email: Email address of recipient
            recipient_name: Name of recipient
            inviter_name: Name of person sending invitation
            organization_name: Name of organization/team
            invitation_token: Invitation token
            custom_message: Optional custom message
            
        Returns:
            True if sent successfully
        """
        return await self.invitation_builder.build_and_send(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            inviter_name=inviter_name,
            organization_name=organization_name,
            invitation_token=invitation_token,
            custom_message=custom_message
        )
    
    async def send_notification(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        notification_title: str,
        notification_message: str,
        action_url: str = "",
        action_text: str = "View Details"
    ) -> bool:
        """
        Send notification email.
        
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
        return await self.notification_builder.build_and_send(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            notification_title=notification_title,
            notification_message=notification_message,
            action_url=action_url,
            action_text=action_text
        )
    
    async def send_bulk_notification(
        self,
        recipients: List[EmailStr],
        notification_title: str,
        notification_message: str,
        action_url: str = "",
        action_text: str = "View Details"
    ) -> dict:
        """
        Send notification email to multiple recipients.
        
        Args:
            recipients: List of recipient email addresses
            notification_title: Title of notification
            notification_message: Notification message content
            action_url: Optional action button URL
            action_text: Text for action button
            
        Returns:
            Dict with success count and failed recipients
        """
        return await self.bulk_notification_builder.build_and_send_bulk(
            recipients=recipients,
            notification_title=notification_title,
            notification_message=notification_message,
            action_url=action_url,
            action_text=action_text
        )


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """
    Get or create singleton email service instance.
    
    Returns:
        EmailService instance
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
