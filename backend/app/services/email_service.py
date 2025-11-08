"""
Email service module for sending transactional emails.

Supports multiple email types with HTML templates:
- Account activation/verification
- Password reset
- User invitation
- General notifications
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmailBuilder:
    """
    Builder pattern for constructing and sending emails.
    
    This class provides a flexible interface for creating and sending various
    types of emails with consistent configuration and error handling.
    """
    
    def __init__(self):
        """Initialize email builder with settings from configuration."""
        self.smtp_config = self._build_smtp_config()
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
    
    def _build_smtp_config(self) -> ConnectionConfig:
        """Build SMTP connection configuration from settings."""
        return ConnectionConfig(
            MAIL_USERNAME=settings.SMTP_USERNAME,
            MAIL_PASSWORD=settings.SMTP_PASSWORD,
            MAIL_FROM=settings.SMTP_FROM_EMAIL,
            MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
            MAIL_PORT=settings.SMTP_PORT,
            MAIL_SERVER=settings.SMTP_SERVER,
            MAIL_STARTTLS=settings.SMTP_USE_TLS,
            MAIL_SSL_TLS=settings.SMTP_USE_SSL,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
    
    async def send_account_activation(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        activation_token: str,
    ) -> bool:
        """
        Send account activation/verification email.
        
        Args:
            recipient_email: Email address to send to
            recipient_name: Full name of recipient
            activation_token: Token for email verification
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            verification_url = f"{settings.EMAIL_VERIFICATION_URL}?token={activation_token}"
            
            html_body = self._render_account_activation_template(
                name=recipient_name,
                verification_url=verification_url,
            )
            
            message = MessageSchema(
                subject="Activate Your RAG Fortress Account",
                recipients=[recipient_email],
                body=html_body,
                subtype=MessageType.html,
            )
            
            return await self._send_message(message)
        
        except Exception as e:
            logger.error(f"Failed to send activation email to {recipient_email}: {str(e)}")
            return False
    
    async def send_password_reset(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        reset_token: str,
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            recipient_email: Email address to send to
            recipient_name: Full name of recipient
            reset_token: Token for password reset
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            reset_url = f"{settings.PASSWORD_RESET_URL}?token={reset_token}"
            
            html_body = self._render_password_reset_template(
                name=recipient_name,
                reset_url=reset_url,
            )
            
            message = MessageSchema(
                subject="Reset Your RAG Fortress Password",
                recipients=[recipient_email],
                body=html_body,
                subtype=MessageType.html,
            )
            
            return await self._send_message(message)
        
        except Exception as e:
            logger.error(f"Failed to send password reset email to {recipient_email}: {str(e)}")
            return False
    
    async def send_user_invitation(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        inviter_name: str,
        invite_token: str,
        message: Optional[str] = None,
    ) -> bool:
        """
        Send user invitation email.
        
        Args:
            recipient_email: Email address to send to
            recipient_name: Full name of recipient
            inviter_name: Name of person sending invite
            invite_token: Token for accepting invitation
            message: Optional custom message from inviter
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            invite_url = f"{settings.INVITE_URL}?token={invite_token}"
            
            html_body = self._render_invitation_template(
                recipient_name=recipient_name,
                inviter_name=inviter_name,
                invite_url=invite_url,
                custom_message=message,
            )
            
            message_obj = MessageSchema(
                subject=f"{inviter_name} Invited You to Join RAG Fortress",
                recipients=[recipient_email],
                body=html_body,
                subtype=MessageType.html,
            )
            
            return await self._send_message(message_obj)
        
        except Exception as e:
            logger.error(f"Failed to send invitation email to {recipient_email}: {str(e)}")
            return False
    
    async def send_notification(
        self,
        recipient_email: EmailStr,
        recipient_name: str,
        subject: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
    ) -> bool:
        """
        Send generic notification email.
        
        Args:
            recipient_email: Email address to send to
            recipient_name: Full name of recipient
            subject: Email subject line
            title: Email title/heading
            message: Email body message
            action_url: Optional URL for call-to-action button
            action_text: Optional text for call-to-action button
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            html_body = self._render_notification_template(
                name=recipient_name,
                title=title,
                message=message,
                action_url=action_url,
                action_text=action_text,
            )
            
            message_obj = MessageSchema(
                subject=subject,
                recipients=[recipient_email],
                body=html_body,
                subtype=MessageType.html,
            )
            
            return await self._send_message(message_obj)
        
        except Exception as e:
            logger.error(f"Failed to send notification email to {recipient_email}: {str(e)}")
            return False
    
    async def send_bulk_notification(
        self,
        recipients: List[Dict[str, str]],
        subject: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Send notification to multiple recipients.
        
        Args:
            recipients: List of dicts with 'email' and 'name' keys
            subject: Email subject line
            title: Email title/heading
            message: Email body message
            action_url: Optional URL for call-to-action button
            action_text: Optional text for call-to-action button
        
        Returns:
            Dict mapping email addresses to send success status
        """
        results = {}
        
        for recipient in recipients:
            try:
                email = recipient.get("email")
                name = recipient.get("name", "User")
                
                success = await self.send_notification(
                    recipient_email=email,
                    recipient_name=name,
                    subject=subject,
                    title=title,
                    message=message,
                    action_url=action_url,
                    action_text=action_text,
                )
                results[email] = success
            
            except Exception as e:
                logger.error(f"Error sending bulk notification to {email}: {str(e)}")
                results[email] = False
        
        return results
    
    async def _send_message(self, message: MessageSchema) -> bool:
        """
        Send email message using FastMail.
        
        Args:
            message: MessageSchema object to send
        
        Returns:
            True if successful, False otherwise
        """
        try:
            fm = FastMail(self.smtp_config)
            await fm.send_message(message)
            logger.info(f"Email sent successfully to {message.recipients}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _render_account_activation_template(
        self,
        name: str,
        verification_url: str,
    ) -> str:
        """Render HTML template for account activation email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Activate Your Account</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; margin: 20px 0; border-radius: 5px; }}
                .button {{ background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
                .token-info {{ background-color: #fff; padding: 10px; border-left: 4px solid #4CAF50; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to RAG Fortress</h1>
                </div>
                
                <div class="content">
                    <p>Hi {name},</p>
                    
                    <p>Thank you for registering! To complete your account setup and verify your email address, please click the button below:</p>
                    
                    <center>
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </center>
                    
                    <p>Or copy and paste this link in your browser:</p>
                    <div class="token-info">
                        <small>{verification_url}</small>
                    </div>
                    
                    <p>This link will expire in 24 hours.</p>
                    
                    <p>If you did not create this account, please ignore this email.</p>
                </div>
                
                <div class="footer">
                    <p>RAG Fortress Team</p>
                    <p>&copy; {datetime.now(timezone.utc).year} RAG Fortress. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _render_password_reset_template(
        self,
        name: str,
        reset_url: str,
    ) -> str:
        """Render HTML template for password reset email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; margin: 20px 0; border-radius: 5px; }}
                .button {{ background-color: #FF9800; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
                .warning {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #FF9800; margin: 10px 0; }}
                .token-info {{ background-color: #fff; padding: 10px; border-left: 4px solid #FF9800; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                
                <div class="content">
                    <p>Hi {name},</p>
                    
                    <p>We received a request to reset your password. If you made this request, click the button below to create a new password:</p>
                    
                    <center>
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </center>
                    
                    <p>Or copy and paste this link in your browser:</p>
                    <div class="token-info">
                        <small>{reset_url}</small>
                    </div>
                    
                    <div class="warning">
                        <strong>Security Notice:</strong> This link will expire in 1 hour. If you did not request a password reset, please ignore this email. Your password will not be changed until you create a new one.
                    </div>
                    
                    <p>For security reasons, never share this link with anyone.</p>
                </div>
                
                <div class="footer">
                    <p>RAG Fortress Security Team</p>
                    <p>&copy; {datetime.now(timezone.utc).year} RAG Fortress. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _render_invitation_template(
        self,
        recipient_name: str,
        inviter_name: str,
        invite_url: str,
        custom_message: Optional[str] = None,
    ) -> str:
        """Render HTML template for user invitation email."""
        custom_msg_html = f"<p><strong>Message from {inviter_name}:</strong></p><p>{custom_message}</p>" if custom_message else ""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>You're Invited to RAG Fortress</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; margin: 20px 0; border-radius: 5px; }}
                .button {{ background-color: #2196F3; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
                .message-box {{ background-color: #e3f2fd; padding: 15px; border-left: 4px solid #2196F3; margin: 15px 0; border-radius: 3px; }}
                .token-info {{ background-color: #fff; padding: 10px; border-left: 4px solid #2196F3; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>You're Invited!</h1>
                </div>
                
                <div class="content">
                    <p>Hi {recipient_name},</p>
                    
                    <p><strong>{inviter_name}</strong> has invited you to join their team on <strong>RAG Fortress</strong>.</p>
                    
                    {custom_msg_html}
                    
                    <p>Click the button below to accept the invitation and create your account:</p>
                    
                    <center>
                        <a href="{invite_url}" class="button">Accept Invitation</a>
                    </center>
                    
                    <p>Or copy and paste this link in your browser:</p>
                    <div class="token-info">
                        <small>{invite_url}</small>
                    </div>
                    
                    <div class="message-box">
                        <p><strong>About RAG Fortress:</strong> RAG Fortress is a powerful document retrieval and knowledge management platform. Once you accept, you'll have full access to shared documents and resources.</p>
                    </div>
                    
                    <p>This invitation will expire in 7 days.</p>
                    
                    <p>Questions? Contact the RAG Fortress support team.</p>
                </div>
                
                <div class="footer">
                    <p>RAG Fortress Team</p>
                    <p>&copy; {datetime.now(timezone.utc).year} RAG Fortress. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _render_notification_template(
        self,
        name: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
    ) -> str:
        """Render HTML template for generic notification email."""
        action_button_html = ""
        if action_url and action_text:
            action_button_html = f"""
            <center>
                <a href="{action_url}" class="button">{action_text}</a>
            </center>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #673AB7; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; margin: 20px 0; border-radius: 5px; }}
                .button {{ background-color: #673AB7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                </div>
                
                <div class="content">
                    <p>Hi {name},</p>
                    
                    <p>{message}</p>
                    
                    {action_button_html}
                </div>
                
                <div class="footer">
                    <p>RAG Fortress Team</p>
                    <p>&copy; {datetime.now(timezone.utc).year} RAG Fortress. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """


# Singleton instance
email_builder = EmailBuilder()


async def send_account_activation_email(
    recipient_email: EmailStr,
    recipient_name: str,
    activation_token: str,
) -> bool:
    """Convenience function to send account activation email."""
    return await email_builder.send_account_activation(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        activation_token=activation_token,
    )


async def send_password_reset_email(
    recipient_email: EmailStr,
    recipient_name: str,
    reset_token: str,
) -> bool:
    """Convenience function to send password reset email."""
    return await email_builder.send_password_reset(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        reset_token=reset_token,
    )


async def send_invitation_email(
    recipient_email: EmailStr,
    recipient_name: str,
    inviter_name: str,
    invite_token: str,
    message: Optional[str] = None,
) -> bool:
    """Convenience function to send user invitation email."""
    return await email_builder.send_user_invitation(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        inviter_name=inviter_name,
        invite_token=invite_token,
        message=message,
    )


async def send_notification_email(
    recipient_email: EmailStr,
    recipient_name: str,
    subject: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    action_text: Optional[str] = None,
) -> bool:
    """Convenience function to send generic notification email."""
    return await email_builder.send_notification(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        subject=subject,
        title=title,
        message=message,
        action_url=action_url,
        action_text=action_text,
    )
