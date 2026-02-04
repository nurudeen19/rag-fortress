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

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from datetime import datetime, timezone

from app.core.database import get_session
from app.core.security import get_current_user
from app.config.settings import settings
from app.utils.demo_mode import prevent_in_demo_mode
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
    SignupWithInviteRequest,
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
    handle_signup_with_invite,
    handle_verify_invitation_token,
)


logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ============================================================================
# LOGIN & REGISTRATION
# ============================================================================

@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(
    request: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session)
):
    """
    Login with username/email and password.
    
    Sets httpOnly cookies for access and refresh tokens (secure, XSS-safe).
    Also returns tokens in response body for backwards compatibility.
    """
    result = await handle_login(request, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Invalid credentials")
        )
    
    # Set httpOnly cookies for secure token storage
    # These are NOT accessible via JavaScript (XSS protection)
    # Calculate max_age in seconds from token expiration settings
    access_token_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_token_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    
    response.set_cookie(
        key="access_token",
        value=result["token"],
        httponly=True,
        secure=settings.COOKIE_SECURE,  # False for HTTP dev, True for HTTPS prod
        samesite=settings.COOKIE_SAMESITE,  # Configurable: lax, strict, or none
        max_age=access_token_max_age,
    )
    
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,  # Configurable: lax, strict, or none
        max_age=refresh_token_max_age,
    )
    
    return LoginResponse(
        token=result["token"],
        token_type="bearer",
        expires_at=result["expires_at"],
        user=result["user"],
    )


@router.post("/refresh", response_model=LoginResponse, status_code=200)
async def refresh_access_token(
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """
    Refresh access token using refresh token from httpOnly cookie.
    
    Returns new access token and updates cookies.
    """
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    from app.core.security import create_access_token, create_refresh_token
    from sqlalchemy import select
    
    try:
        # Verify refresh token
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = int(payload.get("sub"))
        
        # Get user from database
        result_db = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result_db.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new tokens
        new_access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token(user.id)
        
        # Calculate expiry
        from datetime import timedelta
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_at = datetime.now(timezone.utc) + expires_delta
        
        # Update httpOnly cookies
        # Calculate max_age in seconds from token expiration settings
        access_token_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        refresh_token_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite=settings.COOKIE_SAMESITE,  # Configurable: lax, strict, or none
            max_age=access_token_max_age,
        )
        
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite=settings.COOKIE_SAMESITE,  # Configurable: lax, strict, or none
            max_age=refresh_token_max_age,
        )
        
        # Build user response
        user_response = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "department_id": user.department_id,
        }
        
        return LoginResponse(
            token=new_access_token,
            token_type="bearer",
            expires_at=expires_at.isoformat(),
            user=user_response,
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
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
        full_name=user.get("full_name", f"{user['first_name']} {user['last_name']}".strip()),
        department_id=user.get("department_id"),
        is_active=user["is_active"],
        is_verified=user["is_verified"],
        is_suspended=user.get("is_suspended", False),
        suspension_reason=user.get("suspension_reason"),
        suspended_at=user.get("suspended_at"),
    )


@router.post("/signup", response_model=LoginResponse, status_code=201)
async def signup_with_invite(
    request: SignupWithInviteRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Complete user signup using invitation token.
    
    Invitation tokens are generated when an admin invites a user.
    This endpoint allows the invited user to:
    1. Set their username and password
    2. Complete their profile (first_name, last_name)
    3. Activate their account
    
    Returns:
        JWT token for immediate login after successful signup
    
    Raises:
        400 Bad Request: Invalid/expired token or validation errors
    """
    result = await handle_signup_with_invite(request, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to complete signup")
        )
    
    user = result["user"]
    return LoginResponse(
        token=result["token"],
        token_type="bearer",
        expires_at=result["expires_at"],
        user={
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "full_name": user["full_name"],
            "is_active": user["is_active"],
            "is_verified": user["is_verified"],
            "is_suspended": user["is_suspended"],
            "roles": user.get("roles", []),
        }
    )


@router.get("/signup/verify-invite", response_model=dict)
async def verify_invitation_token(
    token: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Verify invitation token and return invitation details.
    
    Called by frontend when user lands on signup page to:
    1. Verify token is valid and not expired
    2. Pre-fill email address from invitation
    3. Display role information
    
    Returns:
        Dict with email and role information, or error
    
    Raises:
        400 Bad Request: Invalid/expired token
    """
    result = await handle_verify_invitation_token(token, session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to verify invitation token")
        )
    
    return {
        "success": True,
        "email": result["email"],
        "role_name": result["role_name"],
        "expires_at": result.get("expires_at")
    }


@router.post("/logout", response_model=SuccessResponse, status_code=200)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Logout current user.
    
    Clears httpOnly cookies containing access and refresh tokens.
    """
    result = await handle_logout(session)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to logout")
        )
    
    # Clear httpOnly cookies
    response.delete_cookie(key="access_token", samesite=settings.COOKIE_SAMESITE)
    response.delete_cookie(key="refresh_token", samesite=settings.COOKIE_SAMESITE)
    
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


@router.get("/password-reset/verify", response_model=SuccessResponse)
async def verify_password_reset_token(
    token: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Verify password reset token is valid.
    
    Called by frontend when user lands on reset page to verify token before showing form.
    """
    from app.services.user import PasswordService
    
    try:
        password_service = PasswordService(session)
        is_valid = await password_service.is_reset_token_valid(token)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token is invalid or expired"
            )
        
        return SuccessResponse(message="Token is valid")
    
    except Exception as e:
        logger.error(f"Error verifying reset token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to verify token"
        )


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
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get current user profile with extended profile information."""
    result = await handle_get_profile(current_user, session)
    
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
        full_name=user.get("full_name", f"{user['first_name']} {user['last_name']}".strip()),
        department=user.get("department"),
        department_id=user.get("department_id"),
        is_active=user["is_active"],
        is_verified=user["is_verified"],
        is_suspended=user.get("is_suspended", False),
        suspension_reason=user.get("suspension_reason"),
        suspended_at=user.get("suspended_at"),
        roles=user.get("roles", []),
        phone_number=user.get("phone_number"),
        location=user.get("location"),
        job_title=user.get("job_title"),
        about=user.get("about"),
        avatar_url=user.get("avatar_url"),
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
        full_name=user.get("full_name", f"{user['first_name']} {user['last_name']}".strip()),
        department=user.get("department"),
        department_id=user.get("department_id"),
        is_active=user["is_active"],
        is_verified=user["is_verified"],
        is_suspended=user.get("is_suspended", False),
        suspension_reason=user.get("suspension_reason"),
        suspended_at=user.get("suspended_at"),
        roles=user.get("roles", []),
        phone_number=user.get("phone_number"),
        location=user.get("location"),
        job_title=user.get("job_title"),
        about=user.get("about"),
        avatar_url=user.get("avatar_url"),
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
@prevent_in_demo_mode("Delete account")
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

