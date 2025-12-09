# Email Notification System Documentation

## Overview

RAG Fortress includes a complete, production-ready email notification system built on the **fastapi-mail** library (859 GitHub stars, used by 5.5k projects). The system provides a flexible builder pattern for sending transactional emails with beautiful HTML templates.

## Supported Email Types

### 1. Account Activation
- **Purpose**: Verify user email address during account creation
- **Token Expiry**: 24 hours
- **Features**: 
  - Verification link with embedded token
  - Responsive HTML template
  - Clear call-to-action button

### 2. Password Reset
- **Purpose**: Allow users to securely reset forgotten passwords
- **Token Expiry**: 1 hour
- **Features**:
  - Secure reset link with token
  - Security notice about link expiry
  - Warning if user didn't request reset

### 3. User Invitation
- **Purpose**: Invite users to join teams or workspaces
- **Token Expiry**: 7 days
- **Features**:
  - Custom message from inviter
  - Accept invitation button
  - About RAG Fortress section

### 4. General Notifications
- **Purpose**: Send any custom notification email
- **Features**:
  - Customizable subject, title, and message
  - Optional call-to-action button
  - Suitable for announcements, updates, etc.

## Architecture

### Email Service Module (`app/services/email_service.py`)

The `EmailBuilder` class implements the builder pattern for email construction and sending:

```python
from app.services.email_service import email_builder

# Send account activation email
await email_builder.send_account_activation(
    recipient_email="user@example.com",
    recipient_name="John Doe",
    activation_token="token_here"
)

# Send password reset
await email_builder.send_password_reset(
    recipient_email="user@example.com",
    recipient_name="John Doe",
    reset_token="token_here"
)

# Send invitation
await email_builder.send_user_invitation(
    recipient_email="invitee@example.com",
    recipient_name="Jane Smith",
    inviter_name="John Doe",
    invite_token="token_here",
    message="Optional custom message"
)

# Send notification
await email_builder.send_notification(
    recipient_email="user@example.com",
    recipient_name="John Doe",
    subject="Important Update",
    title="System Maintenance",
    message="We're performing maintenance...",
    action_url="https://status.example.com",
    action_text="Check Status"
)

# Send bulk notifications
results = await email_builder.send_bulk_notification(
    recipients=[
        {"email": "user1@example.com", "name": "User One"},
        {"email": "user2@example.com", "name": "User Two"}
    ],
    subject="Notification",
    title="Important",
    message="Message content here"
)
```

### Email Schemas (`app/schemas/email.py`)

Pydantic models for request/response validation:

- `EmailRequest` - Generic notification email
- `AccountActivationRequest` - Account activation email
- `PasswordResetRequest` - Password reset email
- `InvitationRequest` - User invitation email
- `BulkNotificationRequest` - Bulk notification email
- `EmailResponse` - Single email response
- `BulkEmailResponse` - Bulk email response

### Email Routes (`app/routes/email.py`)

RESTful endpoints for triggering email sends:

- `POST /api/v1/emails/account-activation` - Send account activation email
- `POST /api/v1/emails/password-reset` - Send password reset email
- `POST /api/v1/emails/invitation` - Send user invitation email
- `POST /api/v1/emails/notification` - Send general notification
- `POST /api/v1/emails/bulk-notification` - Send bulk notifications
- `GET /api/v1/emails/health` - Check email service health

## Configuration

### Environment Variables

Add the following to your `.env` file:

```env
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=RAG Fortress
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# Email Settings
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES=1440
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=60
INVITE_TOKEN_EXPIRE_DAYS=7

# Frontend URLs (for email links)
passed from the frontend as url template which the backend attaches
```

### Configuration File

All email settings are defined in `app/config/email_settings.py` and loaded automatically via Pydantic BaseSettings from environment variables.

```python
from app.config.settings import settings

# Access email configuration
print(settings.SMTP_SERVER)
print(settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
```

### Email Validation

Email configuration is validated at application startup:
- SMTP port must be between 1 and 65535
- SMTP_FROM_EMAIL must be provided if SMTP is configured
- Cannot use both TLS and SSL simultaneously
- Optional (doesn't fail if email not configured)


### Using Background Tasks

```python
from fastapi import BackgroundTasks
from app.services.email_service import send_notification_email

@router.post("/send-notification")
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks
):
    # Add email task to background
    background_tasks.add_task(
        send_notification_email,
        recipient_email=request.email,
        recipient_name=request.name,
        subject="Notification",
        title="New Update",
        message="You have a new update..."
    )
    
    return {"message": "Notification will be sent shortly"}
```

## HTML Email Templates

All emails are rendered using responsive HTML templates with:
- Modern, clean design
- Proper styling for all clients
- Color-coded by email type:
  - Account Activation: Green (#4CAF50)
  - Password Reset: Orange (#FF9800)
  - Invitation: Blue (#2196F3)
  - General Notification: Purple (#673AB7)
- Mobile-responsive layout
- Clear call-to-action buttons

Templates are generated dynamically in the `EmailBuilder` class.

## Testing Email Endpoints

### Using curl

```bash
# Account activation
curl -X POST http://localhost:8000/api/v1/emails/account-activation \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "user@example.com",
    "recipient_name": "John Doe",
    "activation_token": "token123"
  }'

# Password reset
curl -X POST http://localhost:8000/api/v1/emails/password-reset \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "user@example.com",
    "recipient_name": "John Doe",
    "reset_token": "token456"
  }'

# General notification
curl -X POST http://localhost:8000/api/v1/emails/notification \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_email": "user@example.com",
    "recipient_name": "John Doe",
    "subject": "Important Update",
    "title": "New Features Available",
    "message": "We have released exciting new features!",
    "action_url": "https://example.com/features",
    "action_text": "View Features"
  }'

# Check email service health
curl http://localhost:8000/api/v1/emails/health
```

### Using FastAPI Swagger UI

1. Navigate to `http://localhost:8000/docs`
2. Find the `/api/v1/emails` endpoints
3. Click "Try it out" on any endpoint
4. Fill in the request body
5. Click "Execute"

## SMTP Provider Setup

### Gmail (Free)

1. Enable 2-step verification on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character password in `SMTP_PASSWORD`

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

### SendGrid

```env
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG.your-api-key
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

### AWS SES

```env
SMTP_SERVER=email-smtp.region.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-iam-smtp-user
SMTP_PASSWORD=your-iam-smtp-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

### Custom SMTP Server

```env
SMTP_SERVER=your-smtp-server.com
SMTP_PORT=587
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

## Error Handling

The email service handles errors gracefully:

- **Configuration Errors**: Validated at startup, won't cause runtime failures
- **Send Failures**: Logged and returned as `False`, HTTP 500 returned if critical
- **Invalid Recipients**: Caught and logged per-recipient in bulk sends
- **SMTP Timeouts**: Logged and retried (up to fastapi-mail defaults)

```python
# Check for errors
success = await send_account_activation_email(...)
if not success:
    logger.error("Failed to send email")
    # Handle error (retry, queue, notify admin, etc.)
```

## Production Considerations

### Security
- Never commit SMTP credentials to version control
- Use environment variables or secrets manager
- Consider using dedicated email service (SendGrid, AWS SES)
- Use TLS for secure SMTP connections

### Scalability
- For high-volume emails, consider:
  - Background task queues (Celery, RQ)
  - Dedicated email service (SendGrid, Mailgun)
  - Email queue/batch processing
  - Retry logic for failed sends

### Reliability
- Implement retry logic for failed sends
- Log all email activity
- Monitor email delivery rates
- Set up alerts for email failures
- Use bounce/complaint handling

### Testing
- Use test SMTP servers (Mailtrap, MailHog)
- Mock email in unit tests
- Test with real SMTP in staging environment
- Monitor actual delivery in production

## Troubleshooting

### Email Not Sending

1. Check SMTP configuration:
   ```bash
   curl http://localhost:8000/api/v1/emails/health
   ```

2. Verify credentials:
   - Username and password correct
   - App-specific password for Gmail (not regular password)
   - SMTP port matches TLS/SSL setting

3. Check firewall:
   - Ensure outbound SMTP port (587 or 465) is open
   - Check ISP SMTP restrictions

4. Review logs:
   ```bash
   tail -f logs/app.log | grep email
   ```

### Wrong From Address

Ensure `SMTP_FROM_EMAIL` matches your SMTP authentication email or is configured in your email provider.

### High Latency

- Use async/background tasks
- Consider switching to dedicated email service
- Implement caching/batching for bulk emails

### Template Rendering Issues

Templates are inline in `email_service.py`. Check that:
- Recipient name contains no special characters
- URLs are properly formatted
- Token is not None or empty

## Future Enhancements

- [ ] Email template versioning
- [ ] Template preview endpoint
- [ ] A/B testing support
- [ ] Email analytics/tracking
- [ ] Unsubscribe list management
- [ ] Newsletter support
- [ ] Email queue persistence
- [ ] Retry with exponential backoff
- [ ] Email validation (syntax, domain, MX records)
- [ ] Rate limiting per recipient
