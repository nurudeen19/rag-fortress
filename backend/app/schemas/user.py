"""
User management schemas for request/response validation.
Used for API endpoints and data validation.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, validator, EmailStr


class LoginRequest(BaseModel):
    """Schema for login request."""
    
    username_or_email: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=1, description="Password")


class LoginResponse(BaseModel):
    """Schema for successful login response."""
    
    token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")
    expires_at: str = Field(..., description="Token expiration timestamp (ISO 8601)")
    user: dict = Field(..., description="Full user data including roles")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


class RoleResponse(BaseModel):
    """Response schema for role data."""
    
    id: int
    name: str
    description: Optional[str]
    is_system: bool


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordResetRequestSchema(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr = Field(..., description="Email address")
    reset_link_template: Optional[str] = Field(
        None,
        description="Frontend reset link template with {token} placeholder. "
                    "Example: https://app.example.com/reset-password?token={token}"
    )


class PasswordResetConfirmSchema(BaseModel):
    """Schema for confirming password reset."""
    
    email: Optional[EmailStr] = Field(None, description="Email address (optional, can be extracted from token)")
    reset_token: str = Field(..., description="Password reset token from email link")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserCreateRequest(BaseModel):
    """Schema for creating new user account."""
    
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr = Field(...)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)
    department_id: Optional[int] = None


class UserProfileUpdateRequest(BaseModel):
    """Schema for updating user profile."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    job_title: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    about: Optional[str] = Field(None)


class UserResponse(BaseModel):
    """Response schema for user data."""
    
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    department_id: Optional[int]
    is_active: bool
    is_verified: bool
    is_suspended: bool
    suspension_reason: Optional[str]
    suspended_at: Optional[datetime]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


class UserDetailResponse(UserResponse):
    """Detailed user response including roles."""
    
    roles: List['RoleResponse'] = Field(default_factory=list)


class PermissionResponse(BaseModel):
    """Response schema for permission data."""
    
    id: int
    code: str
    resource: str
    action: str
    description: Optional[str]


class RoleDetailResponse(RoleResponse):
    """Detailed role response including permissions."""
    
    permissions: List[PermissionResponse] = Field(default_factory=list)


class RoleAssignRequest(BaseModel):
    """Schema for assigning role to user."""
    
    role_id: int = Field(..., gt=0)


class RoleRevokeRequest(BaseModel):
    """Schema for revoking role from user."""
    
    role_id: int = Field(..., gt=0)


class RolesAssignRequest(BaseModel):
    """Schema for assigning multiple roles to user."""
    
    role_ids: List[int] = Field(..., min_items=1)


class UserSuspendRequest(BaseModel):
    """Schema for suspending user account."""
    
    reason: Optional[str] = Field(None, description="Reason for suspension")


class UserInviteRequest(BaseModel):
    """Schema for inviting new user."""
    
    email: EmailStr = Field(..., description="Email address to invite")
    role_id: int = Field(..., gt=0, description="Role to assign to the invited user")
    invitation_link_template: Optional[str] = Field(
        None,
        description="Frontend invitation link template with {token} placeholder. "
                    "Example: https://app.example.com/signup?token={token}"
    )


class SignupWithInviteRequest(BaseModel):
    """Schema for signing up with invitation token."""
    
    username: str = Field(..., min_length=3, max_length=255, description="Username")
    email: str = Field(..., description="Email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    password: str = Field(..., min_length=8, description="Password")
    invite_token: str = Field(..., description="Invitation token from email link")
    
    @validator('password')
    def password_strong(cls, v):
        """Validate password strength."""
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, and one digit'
            )
        return v


class PermissionCheckResponse(BaseModel):
    """Response for permission check."""
    
    user_id: int
    permission_code: str
    has_permission: bool


class UserListResponse(BaseModel):
    """Response for user list."""
    
    total: int
    limit: int
    offset: int
    users: List['UserDetailResponse']


class RoleListResponse(BaseModel):
    """Response for role list."""
    
    roles: List['RoleDetailResponse']


class CreateRoleRequest(BaseModel):
    """Schema for creating new role."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_system: bool = Field(default=False)


class CreatePermissionRequest(BaseModel):
    """Schema for creating new permission."""
    
    code: str = Field(..., min_length=1, max_length=255)
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class AssignPermissionToRoleRequest(BaseModel):
    """Schema for assigning permission to role."""
    
    permission_id: int = Field(..., gt=0)


class RevokePermissionFromRoleRequest(BaseModel):
    """Schema for revoking permission from role."""
    
    permission_id: int = Field(..., gt=0)


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    detail: str = Field(...)
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Schema for success responses."""
    
    message: str = Field(...)
    data: Optional[dict] = None


# Update forward references for nested models
UserDetailResponse.update_forward_refs()
