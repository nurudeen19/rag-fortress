"""
User authentication and account management routes.

Routes delegate request handling to handlers for business logic separation.

Endpoints:
- POST /api/v1/auth/login - Login with credentials
- POST /api/v1/auth/register - Register new account
- POST /api/v1/auth/logout - Logout (token removal)
- GET  /api/v1/auth/me - Get current user profile
- PUT  /api/v1/auth/me - Update current user profile
- POST /api/v1/auth/me/password - Change password
- DELETE /api/v1/auth/me - Delete own account
- POST /api/v1/auth/password-reset - Request password reset
- POST /api/v1/auth/password-reset-confirm - Confirm password reset
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema,
    UserCreateRequest,
    UserResponse,
    UserProfileUpdateRequest,
    SuccessResponse,
)
from app.models.user import User
from app.core import get_logger
from app.handlers.auth import (
    handle_login,
    handle_register,
    handle_logout,
    handle_get_profile,
    handle_update_profile,
    handle_change_password,
    handle_delete_account,
    handle_password_reset_request,
    handle_password_reset_confirm,
)


logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ============================================================================
# LOGIN & REGISTRATION
# ============================================================================

@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Login with username/email and password.
    
    Returns JWT access token on success.
    """
    result = await handle_login(request, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Invalid credentials")
        )
    
    return LoginResponse(
        token=result["token"],
        token_type="bearer",
        user_id=result["user"]["id"],
        username=result["user"]["username"],
        email=result["user"]["email"],
        first_name=result["user"]["first_name"],
        last_name=result["user"]["last_name"],
        is_verified=result["user"]["is_verified"],
        is_active=result["user"]["is_active"],
    )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: UserCreateRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Register new user account.
    
    User must verify email before full access.
    """
    result = await handle_register(request, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to create account")
        )
    
    user = result["user"]
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        is_active=user["is_active"],
        is_verified=user["is_verified"],
    )


@router.post("/logout", response_model=SuccessResponse, status_code=200)
async def logout(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Logout current user.
    
    Note: JWT tokens are stateless. Logout is mainly for audit logging.
    Client should remove token from storage.
    """
    result = await handle_logout(session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to logout")
        )
    
    return SuccessResponse(message=result.get("message", "Logged out successfully"))


# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================

@router.post("/password-reset", response_model=SuccessResponse)
async def request_password_reset(
    request: PasswordResetRequestSchema,
    session: AsyncSession = Depends(get_session)
):
    """
    Request password reset email.
    
    Returns success regardless of whether email exists (security).
    """
    result = await handle_password_reset_request(request, session)
    
    # Always return success to not leak email existence
    return SuccessResponse(message=result.get("message", "If email exists, password reset link will be sent"))


@router.post("/password-reset-confirm", response_model=SuccessResponse)
async def confirm_password_reset(
    request: PasswordResetConfirmSchema,
    session: AsyncSession = Depends(get_session)
):
    """
    Confirm password reset with token from email.
    """
    result = await handle_password_reset_confirm(request, session)
    
    if not result.get("success"):
        logger.warning(f"Password reset failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to reset password")
        )
    
    return SuccessResponse(
        message=result.get("message", "Password reset successful. You can now login with your new password.")
    )


# ============================================================================
# ACCOUNT MANAGEMENT
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile."""
    result = await handle_get_profile(current_user)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "User not found")
        )
    
    user = result["user"]
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        is_active=user["is_active"],
        is_verified=user["is_verified"],
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Update current user profile."""
    result = await handle_update_profile(request, current_user, session)
    
    if not result.get("success"):
        logger.warning(f"Profile update failed: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to update profile")
        )
    
    user = result["user"]
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        is_active=user["is_active"],
        is_verified=user["is_verified"],
    )


@router.post("/me/password", response_model=SuccessResponse)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Change current user password."""
    result = await handle_change_password(request, current_user, session)
    
    if not result.get("success"):
        logger.warning(f"Password change failed for user {current_user.id}: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to change password")
        )
    
    return SuccessResponse(
        message=result.get("message", "Password changed successfully")
    )


@router.delete("/me", response_model=SuccessResponse)
async def delete_account(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete current user account (soft delete)."""
    result = await handle_delete_account(current_user, session)
    
    if not result.get("success"):
        logger.warning(f"Account deletion failed for user {current_user.id}: {result.get('error')}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to delete account")
        )
    
    return SuccessResponse(
        message=result.get("message", "Account deleted successfully")
    )

