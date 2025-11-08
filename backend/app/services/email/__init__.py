"""
Email service package.

Modular, extensible email system with:
- Modern responsive HTML templates (templates/)
- Specialized builders for different email types (builders/)
- Core SMTP client for sending (core/)
- Unified service facade for easy access (service.py)

Architecture:
    templates/ → Modern HTML email templates
    core/ → SMTP client for sending
    builders/ → Specialized email builders
    service.py → Unified service facade
    
Usage:
    from app.services.email import get_email_service
    
    email_service = get_email_service()
    
    # Send account activation
    await email_service.send_account_activation(email, name, token)
    
    # Send password reset
    await email_service.send_password_reset(email, name, token)
    
    # Send invitation
    await email_service.send_invitation(email, name, inviter, org, token, message)
    
    # Send notification
    await email_service.send_notification(email, name, title, message, url, text)
    
    # Send bulk notification
    await email_service.send_bulk_notification(recipients, title, message, url, text)
"""

from .service import EmailService, get_email_service

# Export primary interface
__all__ = [
    "EmailService",
    "get_email_service",
]
