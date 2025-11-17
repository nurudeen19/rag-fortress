"""
Email builders package.
"""

from .specialized import (
    BaseEmailBuilder,
    AccountActivationEmailBuilder,
    PasswordResetEmailBuilder,
    PasswordChangedEmailBuilder,
    InvitationEmailBuilder,
    NotificationEmailBuilder,
    BulkNotificationEmailBuilder,
)

__all__ = [
    "BaseEmailBuilder",
    "AccountActivationEmailBuilder",
    "PasswordResetEmailBuilder",
    "PasswordChangedEmailBuilder",
    "InvitationEmailBuilder",
    "NotificationEmailBuilder",
    "BulkNotificationEmailBuilder",
]
