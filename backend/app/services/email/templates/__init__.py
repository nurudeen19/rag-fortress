"""
Email templates package.
"""

from .renders import (
    render_account_activation_email,
    render_password_reset_email,
    render_invitation_email,
    render_notification_email,
)

__all__ = [
    "render_account_activation_email",
    "render_password_reset_email",
    "render_invitation_email",
    "render_notification_email",
]
