"""
Email client for sending emails via SMTP.

Initialized at application startup and provides email sending functionality
throughout the application lifecycle.
"""

import logging
from typing import List, Optional

from fastapi_mail import FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmailClient:
    """
    Core email client for sending emails via SMTP.
    
    Provides low-level email sending functionality with proper error handling.
    Should be initialized once at application startup.
    """
    
    def __init__(self):
        """Initialize email client with connection config."""
        self._config = settings.get_connection_config()
        self._mail = FastMail(self._config)
        self._initialized = False
        logger.info("Email client created (not yet initialized)")
    
    async def initialize(self):
        """
        Initialize email client during application startup.
        
        This allows for async initialization if needed in the future.
        """
        if not self._initialized:
            logger.info("Email client initialized and ready")
            self._initialized = True
    
    async def shutdown(self):
        """
        Cleanup email client during application shutdown.
        """
        if self._initialized:
            logger.info("Email client shutting down")
            self._initialized = False
    
    def is_configured(self) -> bool:
        """
        Check if email client is properly configured.

        Returns:
            True if SMTP server is configured
        """
        # Email is configured if we have a server and port
        # Credentials are optional (e.g., MailHog doesn't require authentication)
        return bool(self._config.MAIL_SERVER and self._config.MAIL_PORT)
    
    async def send_email(
        self,
        recipient: EmailStr,
        subject: str,
        html_body: str,
        recipients: Optional[List[EmailStr]] = None
    ) -> bool:
        """
        Send an email using SMTP.
        
        Args:
            recipient: Primary recipient email address
            subject: Email subject line
            html_body: HTML content of email
            recipients: Additional recipients (for bulk emails)
            
        Returns:
            True if email sent successfully, False otherwise
            
        Raises:
            Exception: If critical SMTP error occurs
        """
        if not self._initialized:
            logger.warning("Email client not initialized")
            return False
        
        if not self.is_configured():
            logger.warning("Email client not configured (missing SMTP credentials)")
            return False
        
        try:
            # Prepare recipients list
            if recipients is None:
                recipients = [recipient]
            elif recipient not in recipients:
                recipients = [recipient] + list(recipients)
            
            # Create message
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=html_body,
                subtype=MessageType.html,
            )
            
            # Send email
            await self._mail.send_message(message)
            
            logger.info(
                f"Email sent successfully: '{subject}' to {len(recipients)} recipient(s)"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send email '{subject}' to {recipient}: {str(e)}",
                exc_info=True
            )
            return False
    
    async def send_bulk_email(
        self,
        recipients: List[EmailStr],
        subject: str,
        html_body: str
    ) -> dict:
        """
        Send email to multiple recipients.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject line
            html_body: HTML content of email
            
        Returns:
            Dict with success count and failed recipients
        """
        if not self._initialized:
            logger.warning("Email client not initialized")
            return {"success_count": 0, "failed": recipients, "total": len(recipients)}
        
        if not self.is_configured():
            logger.warning("Email client not configured (missing SMTP credentials)")
            return {"success_count": 0, "failed": recipients, "total": len(recipients)}
        
        if not recipients:
            logger.warning("No recipients provided for bulk email")
            return {"success_count": 0, "failed": [], "total": 0}
        
        try:
            # Create message for all recipients
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=html_body,
                subtype=MessageType.html,
            )
            
            # Send email
            await self._mail.send_message(message)
            
            logger.info(
                f"Bulk email sent successfully: '{subject}' to {len(recipients)} recipients"
            )
            
            return {
                "success_count": len(recipients),
                "failed": [],
                "total": len(recipients)
            }
            
        except Exception as e:
            logger.error(
                f"Failed to send bulk email '{subject}': {str(e)}",
                exc_info=True
            )
            
            return {
                "success_count": 0,
                "failed": recipients,
                "total": len(recipients)
            }


# Global instance (initialized at startup)
email_client: Optional[EmailClient] = None


def get_email_client() -> EmailClient:
    """
    Get the global email client instance.
    
    Returns:
        EmailClient instance
        
    Raises:
        RuntimeError: If email client not initialized
    """
    if email_client is None:
        raise RuntimeError(
            "Email client not initialized. "
            "Ensure application startup completed successfully."
        )
    return email_client


def init_email_client() -> EmailClient:
    """
    Initialize the global email client instance.
    
    Called during application startup.
    
    Returns:
        EmailClient instance
    """
    global email_client
    if email_client is None:
        email_client = EmailClient()
        logger.info("Global email client instance created")
    return email_client
