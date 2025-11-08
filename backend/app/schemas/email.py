"""
Email schemas for request/response validation.

Defines Pydantic models for email endpoints to ensure
type-safe validation and clear API contracts.
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class EmailRequest(BaseModel):
    """Generic email request schema."""
    
    recipient_email: EmailStr = Field(..., description="Email address of recipient")
    recipient_name: str = Field(..., description="Full name of recipient")
    subject: str = Field(..., description="Email subject line")
    title: str = Field(..., description="Email title/heading")
    message: str = Field(..., description="Email body message")
    action_url: Optional[str] = Field(None, description="Optional URL for call-to-action")
    action_text: Optional[str] = Field(None, description="Optional text for call-to-action button")
    
    class Config:
        schema_extra = {
            "example": {
                "recipient_email": "user@example.com",
                "recipient_name": "John Doe",
                "subject": "Welcome to RAG Fortress",
                "title": "Welcome!",
                "message": "We're excited to have you on board.",
                "action_url": "https://example.com/dashboard",
                "action_text": "Go to Dashboard"
            }
        }


class AccountActivationRequest(BaseModel):
    """Account activation email request."""
    
    recipient_email: EmailStr = Field(..., description="Email address to verify")
    recipient_name: str = Field(..., description="Full name of user")
    activation_token: str = Field(..., description="Token for email verification")
    
    class Config:
        schema_extra = {
            "example": {
                "recipient_email": "newuser@example.com",
                "recipient_name": "Jane Smith",
                "activation_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class PasswordResetRequest(BaseModel):
    """Password reset email request."""
    
    recipient_email: EmailStr = Field(..., description="Email address for password reset")
    recipient_name: str = Field(..., description="Full name of user")
    reset_token: str = Field(..., description="Token for password reset")
    
    class Config:
        schema_extra = {
            "example": {
                "recipient_email": "user@example.com",
                "recipient_name": "John Doe",
                "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class InvitationRequest(BaseModel):
    """User invitation email request."""
    
    recipient_email: EmailStr = Field(..., description="Email address to invite")
    recipient_name: str = Field(..., description="Full name of invitee")
    inviter_name: str = Field(..., description="Name of person sending invitation")
    organization_name: str = Field(..., description="Name of organization/team")
    invitation_token: str = Field(..., description="Token for accepting invitation")
    custom_message: Optional[str] = Field(None, description="Optional custom message from inviter")
    
    class Config:
        schema_extra = {
            "example": {
                "recipient_email": "colleague@example.com",
                "recipient_name": "Alice Johnson",
                "inviter_name": "Bob Smith",
                "organization_name": "Acme Corp",
                "invitation_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "custom_message": "Please join our team to collaborate on documents!"
            }
        }


class NotificationRequest(BaseModel):
    """Single notification email request."""
    
    recipient_email: EmailStr = Field(..., description="Email address of recipient")
    recipient_name: str = Field(..., description="Full name of recipient")
    notification_title: str = Field(..., description="Title of the notification")
    notification_message: str = Field(..., description="Notification message content")
    action_url: Optional[str] = Field(None, description="Optional URL for call-to-action")
    action_text: Optional[str] = Field(None, description="Optional text for call-to-action button")
    
    class Config:
        schema_extra = {
            "example": {
                "recipient_email": "user@example.com",
                "recipient_name": "John Doe",
                "notification_title": "Document Processed",
                "notification_message": "Your document has been successfully processed.",
                "action_url": "https://example.com/documents/123",
                "action_text": "View Document"
            }
        }


class BulkNotificationRequest(BaseModel):
    """Bulk notification email request."""
    
    recipients: List[EmailStr] = Field(
        ...,
        description="List of recipient email addresses"
    )
    notification_title: str = Field(..., description="Title of the notification")
    notification_message: str = Field(..., description="Notification message content")
    action_url: Optional[str] = Field(None, description="Optional URL for call-to-action")
    action_text: Optional[str] = Field(None, description="Optional text for call-to-action button")
    
    class Config:
        schema_extra = {
            "example": {
                "recipients": [
                    "user1@example.com",
                    "user2@example.com"
                ],
                "notification_title": "System Maintenance Notice",
                "notification_message": "We're performing maintenance on our servers.",
                "action_url": "https://status.example.com",
                "action_text": "Check Status"
            }
        }


class EmailResponse(BaseModel):
    """Response for email sending requests."""
    
    success: bool = Field(..., description="Whether email was sent successfully")
    message: str = Field(..., description="Status message")
    recipient: Optional[str] = Field(None, description="Recipient email address")
    timestamp: str = Field(..., description="ISO format timestamp of request")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Email sent successfully",
                "recipient": "user@example.com",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class BulkEmailResponse(BaseModel):
    """Response for bulk email sending requests."""
    
    success: bool = Field(..., description="Whether operation completed")
    total: int = Field(..., description="Total recipients in request")
    sent: int = Field(..., description="Number of emails successfully sent")
    failed: int = Field(..., description="Number of emails that failed")
    results: dict = Field(..., description="Mapping of email addresses to send status")
    timestamp: str = Field(..., description="ISO format timestamp of request")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "total": 2,
                "sent": 2,
                "failed": 0,
                "results": {
                    "user1@example.com": True,
                    "user2@example.com": True
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
