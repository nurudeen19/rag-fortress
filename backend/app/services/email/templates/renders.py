"""
Specialized email templates for different email types.
"""

from app.config import settings

from .base import get_base_template


def render_account_activation_email(
    recipient_name: str,
    activation_url: str
) -> tuple[str, str]:
    """
    Render account activation email.
    
    Args:
        recipient_name: Name of the recipient
        activation_url: Account verification URL with token
        
    Returns:
        Tuple of (subject, html_body)
    """
    app_name = settings.APP_NAME
    app_description = settings.APP_DESCRIPTION
    subject = f"Activate Your {app_name} Account"
    preview = f"Hi {recipient_name}, verify your email to get started with {app_name}."
    
    content = f"""
        <h1 class="heading">Welcome to {app_name}! 🎉</h1>

        <p class="text">Hi <strong>{recipient_name}</strong>,</p>

        <p class="text">
            Thank you for signing up! We're excited to have you on board.
            To complete your registration and start using {app_name}, please verify your email address.
        </p>

        <p class="text">
            {app_description} is built to keep your documents secure and your teams productive.
        </p>

        <p class="text">
            Click the button below to activate your account:
        </p>

        <!-- Button -->
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin: 32px 0;">
            <tr>
                <td>
                    <a href="{activation_url}" class="button">
                        Activate My Account
                    </a>
                </td>
            </tr>
        </table>

        <p class="text">
            This link will expire in 24 hours for security purposes.
        </p>

        <div class="divider"></div>

        <p class="text" style="font-size: 14px; color: #718096;">
            If you didn't create an account with {app_name}, you can safely ignore this email.
        </p>

        <p class="text" style="font-size: 14px; color: #718096;">
            <strong>Having trouble?</strong> Copy and paste this link into your browser:<br>
            <a href="{activation_url}" style="color: #4f46e5; word-break: break-all;">{activation_url}</a>
        </p>
    """

    html_body = get_base_template(
        title=subject,
        preview_text=preview,
        content_html=content,
        app_name=app_name,
        app_description=app_description,
    )

    return subject, html_body


def render_password_reset_email(
    recipient_name: str,
    reset_url: str
) -> tuple[str, str]:
    """
    Render password reset email.
    
    Args:
        recipient_name: Name of the recipient
        reset_url: Password reset URL with token
        
    Returns:
        Tuple of (subject, html_body)
    """
    app_name = settings.APP_NAME
    app_description = settings.APP_DESCRIPTION
    subject = f"Reset Your {app_name} Password"
    preview = f"Hi {recipient_name}, you requested to reset your {app_name} password."
    
    content = f"""
        <h1 class="heading">Password Reset Request 🔒</h1>

        <p class="text">Hi <strong>{recipient_name}</strong>,</p>

        <p class="text">
            We received a request to reset your {app_name} account password.
            If you made this request, click the button below to set a new password.
        </p>

        <!-- Button -->
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin: 32px 0;">
            <tr>
                <td>
                    <a href="{reset_url}" class="button">
                        Reset My Password
                    </a>
                </td>
            </tr>
        </table>

        <p class="text">
            This link will expire in 1 hour for security purposes.
        </p>

        <div class="divider"></div>

        <p class="text" style="font-size: 14px; color: #718096;">
            <strong>Didn't request this?</strong> If you didn't request a password reset,
            please ignore this email or contact support if you have concerns about your {app_description} workspace.
        </p>

        <p class="text" style="font-size: 14px; color: #718096;">
            <strong>Having trouble?</strong> Copy and paste this link into your browser:<br>
            <a href="{reset_url}" style="color: #4f46e5; word-break: break-all;">{reset_url}</a>
        </p>
    """
    
    html_body = get_base_template(
        title=subject,
        preview_text=preview,
        content_html=content,
        app_name=app_name,
        app_description=app_description,
    )
    
    return subject, html_body


def render_invitation_email(
    recipient_name: str,
    inviter_name: str,
    organization_name: str,
    invitation_url: str,
    custom_message: str = ""
) -> tuple[str, str]:
    """
    Render team invitation email.

    Args:
        recipient_name: Name of the recipient
        inviter_name: Name of person sending invitation
        organization_name: Name of organization/team
        invitation_url: Invitation acceptance URL with token
        custom_message: Optional custom message from inviter

    Returns:
        Tuple of (subject, html_body)
    """
    app_name = settings.APP_NAME
    app_description = settings.APP_DESCRIPTION
    subject = f"You're Invited to Join {organization_name} on {app_name}"
    preview = f"{inviter_name} invited you to join {organization_name} on {app_name}."

    custom_msg_html = ""
    if custom_message:
        custom_msg_html = f"""
        <div style="background-color: #f7fafc; border-left: 4px solid #4f46e5; padding: 16px; margin: 24px 0; border-radius: 4px;">
            <p class="text" style="margin: 0; font-style: italic;">
                "{custom_message}"
            </p>
        </div>
        """

    content = f"""
        <h1 class="heading">You've Been Invited! 📧</h1>

        <p class="text">Hi <strong>{recipient_name}</strong>,</p>

        <p class="text">
            <strong>{inviter_name}</strong> has invited you to join <strong>{organization_name}</strong>
            on {app_name}, {app_description}.
        </p>

        {custom_msg_html}

        <p class="text">
            Click the button below to accept the invitation and create your account:
        </p>

        <!-- Button -->
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin: 32px 0;">
            <tr>
                <td>
                    <a href="{invitation_url}" class="button">
                        Accept Invitation
                    </a>
                </td>
            </tr>
        </table>

        <p class="text">
            This invitation will expire in 7 days.
        </p>

        <div class="divider"></div>

        <p class="text" style="font-size: 14px; color: #718096;">
            <strong>What is {app_name}?</strong> {app_description} that helps teams manage and query their knowledge base using advanced AI.
        </p>

        <p class="text" style="font-size: 14px; color: #718096;">
            <strong>Having trouble?</strong> Copy and paste this link into your browser:<br>
            <a href="{invitation_url}" style="color: #4f46e5; word-break: break-all;">{invitation_url}</a>
        </p>
    """

    html_body = get_base_template(
        title=subject,
        preview_text=preview,
        content_html=content,
        app_name=app_name,
        app_description=app_description,
    )

    return subject, html_body


def render_notification_email(
    recipient_name: str,
    notification_title: str,
    notification_message: str,
    action_url: str = "",
    action_text: str = "View Details"
) -> tuple[str, str]:
    """
    Render generic notification email.

    Args:
        recipient_email: Email address of recipient
        recipient_name: Name of recipient
        notification_title: Title of the notification
        notification_message: Main notification message
        action_url: Optional URL for action button
        action_text: Text for action button

    Returns:
        Tuple of (subject, html_body)
    """
    app_name = settings.APP_NAME
    app_description = settings.APP_DESCRIPTION
    subject = notification_title
    preview = notification_message[:100]

    action_button_html = ""
    if action_url:
        action_button_html = f"""
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin: 32px 0;">
            <tr>
                <td>
                    <a href="{action_url}" class="button">
                        {action_text}
                    </a>
                </td>
            </tr>
        </table>
        """

    content = f"""
        <h1 class="heading">{notification_title}</h1>

        <p class="text">Hi <strong>{recipient_name}</strong>,</p>

        <p class="text">
            {notification_message}
        </p>

        {action_button_html}

        <div class="divider"></div>

        <p class="text" style="font-size: 14px; color: #718096;">
            You're receiving this notification because you're a member of {app_name}.
            To manage your notification preferences, visit your {app_description} account settings.
        </p>
    """

    html_body = get_base_template(
        title=subject,
        preview_text=preview,
        content_html=content,
        app_name=app_name,
        app_description=app_description,
    )

    return subject, html_body


def render_password_changed_email(
    recipient_name: str
) -> tuple[str, str]:
    """
    Render password changed notification email.

    Args:
        recipient_name: Name of the recipient

    Returns:
        Tuple of (subject, html_body)
    """
    app_name = settings.APP_NAME
    app_description = settings.APP_DESCRIPTION
    subject = f"Your {app_name} Password Has Been Changed"
    preview = f"Hi {recipient_name}, your {app_name} password was successfully changed."

    content = f"""
        <h1 class="heading">Password Changed Successfully ✅</h1>

        <p class="text">Hi <strong>{recipient_name}</strong>,</p>

        <p class="text">
            This is a confirmation that your {app_name} account password was successfully changed.
        </p>

        <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; margin: 24px 0; border-radius: 4px;">
            <p class="text" style="margin: 0; color: #166534;">
                ✓ Your account is now secured with your new password.
            </p>
        </div>

        <p class="text">
            <strong>Didn't make this change?</strong> If you didn't request this password change or believe your account
            has been compromised, please contact our support team immediately or visit your account security settings.
        </p>

        <div class="divider"></div>

        <p class="text" style="font-size: 14px; color: #718096;">
            This is an automated security notification from {app_name}. Manage your {app_description} preferences anytime.
        </p>
    """

    html_body = get_base_template(
        title=subject,
        preview_text=preview,
        content_html=content,
        app_name=app_name,
        app_description=app_description,
    )

    return subject, html_body
