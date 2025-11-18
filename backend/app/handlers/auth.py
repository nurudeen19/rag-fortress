"""
Authentication request handlers.

Handlers manage business logic for:
- User login and registration
- Password management
- Account management
- Token generation and validation
"""

import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.core.security import create_access_token, hash_password
from app.config.settings import settings
from app.schemas.user import (
    LoginRequest,
    UserCreateRequest,
    PasswordChangeRequest,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema,
    UserProfileUpdateRequest,
    SignupWithInviteRequest,
)
from app.services.user import (
    AuthService,
    PasswordService,
    UserAccountService,
)
from app.core.startup import get_startup_controller
from app.models.job import JobType

logger = logging.getLogger(__name__)


async def handle_login(
    request: LoginRequest,
    session: AsyncSession
) -> dict:
    """
    Handle user login request.
    
    Args:
        request: Login credentials
        session: Database session
        
    Returns:
        Dict with token and user data, or error
    """
    try:
        logger.info(f"Login attempt for {request.username_or_email}")
        
        auth_service = AuthService(session)
        
        # Authenticate user
        user, error = await auth_service.login(
            username_or_email=request.username_or_email,
            password=request.password
        )
        
        if error or not user:
            logger.warning(f"Login failed for {request.username_or_email}: {error}")
            return {
                "success": False,
                "error": error or "Invalid credentials",
                "token": None,
                "user": None
            }
        
        # Generate JWT token
        token = create_access_token(user.id)
        
        # Calculate token expiry timestamp
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_at = datetime.now(timezone.utc) + expires_delta
        
        # Format roles
        roles = [
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_system": role.is_system,
            }
            for role in (user.roles or [])
        ]
        
        logger.info(f"User {user.username} logged in successfully")
        
        return {
            "success": True,
            "token": token,
            "expires_at": expires_at.isoformat(),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": f"{user.first_name} {user.last_name}".strip(),
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "roles": roles,
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling login request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "token": None,
            "user": None
        }


async def handle_register(
    request: UserCreateRequest,
    session: AsyncSession
) -> dict:
    """
    Handle user registration request.
    
    Args:
        request: User registration data
        session: Database session
        
    Returns:
        Dict with new user data, or error
    """
    try:
        logger.info(f"Registration attempt for {request.email}")
        
        user_service = UserAccountService(session)
        
        # Check if user already exists
        existing = await user_service.check_user_exists(
            username=request.username,
            email=request.email
        )
        
        if existing:
            logger.warning(f"Registration failed: User exists {request.email}")
            return {
                "success": False,
                "error": "User already exists with this email or username",
                "user": None
            }
        
        # Create new user
        user, error = await user_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name
        )
        
        if error or not user:
            logger.warning(f"User creation failed for {request.email}: {error}")
            return {
                "success": False,
                "error": error or "Failed to create user",
                "user": None
            }
        
        logger.info(f"User {user.username} registered successfully")
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling registration request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "user": None
        }


async def handle_logout(session: AsyncSession) -> dict:
    """
    Handle user logout request.
    
    Note: JWT tokens are stateless, logout is handled client-side.
    This is placeholder for future session management if needed.
    
    Args:
        session: Database session
        
    Returns:
        Dict with success status
    """
    try:
        logger.info("User logout requested")
        
        return {
            "success": True,
            "message": "Logged out successfully. Please remove token from client."
        }
        
    except Exception as e:
        logger.error(f"Error handling logout request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def handle_get_profile(user) -> dict:
    """
    Handle get user profile request.
    
    Args:
        user: Current authenticated user
        
    Returns:
        Dict with user profile data
    """
    try:
        logger.info(f"Getting profile for user {user.id}")
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": f"{user.first_name} {user.last_name}".strip(),
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_suspended": user.is_suspended,
                "department_id": user.department_id,
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling get profile request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "user": None
        }


async def handle_update_profile(
    request: UserProfileUpdateRequest,
    user,
    session: AsyncSession
) -> dict:
    """
    Handle update user profile request.
    
    Args:
        request: Profile update data
        user: Current authenticated user
        session: Database session
        
    Returns:
        Dict with updated user data, or error
    """
    try:
        logger.info(f"Updating profile for user {user.id}")
        
        user_service = UserAccountService(session)
        
        # Update user profile
        updated_user, error = await user_service.update_user_profile(
            user_id=user.id,
            first_name=request.first_name,
            last_name=request.last_name,
            department_id=request.department_id
        )
        
        if error or not updated_user:
            logger.warning(f"Profile update failed for user {user.id}: {error}")
            return {
                "success": False,
                "error": error or "Failed to update profile",
                "user": None
            }
        
        logger.info(f"Profile updated for user {user.id}")
        
        return {
            "success": True,
            "user": {
                "id": updated_user.id,
                "username": updated_user.username,
                "email": updated_user.email,
                "first_name": updated_user.first_name,
                "last_name": updated_user.last_name,
                "full_name": f"{updated_user.first_name} {updated_user.last_name}".strip(),
                "is_active": updated_user.is_active,
                "department_id": updated_user.department_id,
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling profile update request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "user": None
        }


async def handle_change_password(
    request: PasswordChangeRequest,
    user,
    session: AsyncSession
) -> dict:
    """
    Handle change password request.
    
    Args:
        request: Current and new password
        user: Current authenticated user
        session: Database session
        
    Returns:
        Dict with success status, or error
    """
    try:
        logger.info(f"Password change requested for user {user.id}")
        
        password_service = PasswordService(session)
        
        # Change password
        success, error = await password_service.change_password(
            user_id=user.id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        if not success:
            logger.warning(f"Password change failed for user {user.id}: {error}")
            return {
                "success": False,
                "error": error or "Failed to change password"
            }
        
        logger.info(f"Password changed for user {user.id}")
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error handling password change request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def handle_delete_account(
    user,
    session: AsyncSession
) -> dict:
    """
    Handle account deletion request (soft delete).
    
    Args:
        user: Current authenticated user
        session: Database session
        
    Returns:
        Dict with success status, or error
    """
    try:
        logger.info(f"Account deletion requested for user {user.id}")
        
        user_service = UserAccountService(session)
        
        # Delete account (soft delete)
        success, error = await user_service.deactivate_user_account(user.id)
        
        if not success:
            logger.warning(f"Account deletion failed for user {user.id}: {error}")
            return {
                "success": False,
                "error": error or "Failed to delete account"
            }
        
        logger.info(f"Account deleted for user {user.id}")
        
        return {
            "success": True,
            "message": "Account deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error handling account deletion request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def handle_password_reset_request(
    request: PasswordResetRequestSchema,
    session: AsyncSession
) -> dict:
    """
    Handle password reset request (queue reset email job).
    
    Args:
        request: Email address for password reset
        session: Database session
        
    Returns:
        Dict with success status and message
    """
    try:
        logger.info(f"Password reset requested for {request.email}")
        
        user_service = UserAccountService(session)
        password_service = PasswordService(session)
        
        # Check if user exists
        user = await user_service.get_user_by_email(request.email)
        
        if not user:
            # Don't reveal if email exists (security best practice)
            logger.info(f"Password reset requested for non-existent email: {request.email}")
            return {
                "success": True,
                "message": "If email exists, password reset link will be sent"
            }
        
        # Delete any existing unused tokens for this user to prevent accumulation
        await password_service.delete_unused_reset_tokens(user.id)
        
        # Generate reset token
        reset_token, error = await password_service.create_reset_token(user.id)
        
        if error:
            logger.warning(f"Failed to create reset token for {request.email}: {error}")
            return {
                "success": False,
                "error": "Failed to generate reset token. Please try again later."
            }
        
        # Commit token to database
        await session.commit()
        
        # Queue password reset email job
        try:
            startup_controller = get_startup_controller()
            job_integration = startup_controller.job_integration
            
            if job_integration is None:
                raise Exception("Job integration not initialized")
            
            recipient_name = f"{user.first_name} {user.last_name}".strip() or user.username
            
            # Create and schedule the email job
            await job_integration.create_and_schedule(
                job_type=JobType.PASSWORD_RESET_EMAIL,
                reference_id=user.id,
                reference_type="user",
                handler=job_integration._handle_password_reset_email,
                payload={
                    "recipient_email": request.email,
                    "recipient_name": recipient_name,
                    "reset_token": reset_token,
                    "reset_link_template": request.reset_link_template
                },
                max_retries=3
            )
            
            logger.info(f"Password reset email job queued for {request.email}")
            
            return {
                "success": True,
                "message": "Password reset link will be sent to your email"
            }
        
        except Exception as e:
            logger.error(f"Failed to queue password reset email job for {request.email}: {e}", exc_info=True)
            return {
                "success": False,
                "error": "Failed to send reset email. Please try again later."
            }
        
    except Exception as e:
        logger.error(f"Error handling password reset request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected error occurred. Please try again later."
        }


async def handle_password_reset_confirm(
    request: PasswordResetConfirmSchema,
    session: AsyncSession
) -> dict:
    """
    Handle password reset confirmation (verify token and reset password).
    
    Args:
        request: Email (optional if we can get from token), reset token, and new password
        session: Database session
        
    Returns:
        Dict with success status, or error
    """
    try:
        user_service = UserAccountService(session)
        password_service = PasswordService(session)
        
        # First, look up the token to get the email and user_id
        from sqlalchemy import select
        from app.models.password_reset_token import PasswordResetToken
        
        result = await session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token == request.reset_token
            )
        )
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            logger.warning(f"Invalid reset token: token not found")
            return {
                "success": False,
                "error": "Invalid reset token"
            }
        
        email = token_record.email
        logger.info(f"Password reset confirmation for {email}")
        
        # Verify reset token with the email from token record
        user_id, error = await password_service.verify_reset_token(
            token=request.reset_token,
            email=email
        )
        
        if error or not user_id:
            logger.warning(f"Invalid reset token for {email}: {error}")
            return {
                "success": False,
                "error": error or "Invalid or expired reset token"
            }
        
        # Reset password
        success, error = await password_service.reset_password(
            user_id=user_id,
            new_password=request.new_password
        )
        
        if not success:
            logger.warning(f"Password reset failed for user {user_id}: {error}")
            return {
                "success": False,
                "error": error or "Failed to reset password"
            }
        
        # Commit the password change to database
        await session.commit()
        
        logger.info(f"Password reset successful for user {user_id}")
        
        # Queue password changed notification email
        try:
            startup_controller = get_startup_controller()
            job_integration = startup_controller.job_integration
            
            if job_integration is None:
                raise Exception("Job integration not initialized")
            
            # Get user info for email
            user = await user_service.get_user_by_id(user_id)
            if user:
                recipient_name = f"{user.first_name} {user.last_name}".strip() or user.username
                
                # Create and schedule the password changed email job
                await job_integration.create_and_schedule(
                    job_type=JobType.PASSWORD_CHANGED_EMAIL,
                    reference_id=user_id,
                    reference_type="user",
                    handler=job_integration._handle_password_changed_email,
                    payload={
                        "recipient_email": email,
                        "recipient_name": recipient_name
                    },
                    max_retries=3
                )
                
                logger.info(f"Password changed notification email queued for {email}")
        
        except Exception as e:
            logger.warning(f"Failed to queue password changed notification for {email}: {e}")
            # Don't fail the password reset if email notification fails
        
        return {
            "success": True,
            "message": "Password reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Error handling password reset confirmation: {str(e)}", exc_info=True)
        await session.rollback()
        return {
            "success": False,
            "error": str(e)
        }


async def handle_verify_invitation_token(
    token: str,
    session: AsyncSession
) -> dict:
    """
    Verify invitation token and return invitation details.
    
    Called by frontend when user lands on signup page to:
    1. Verify token is valid and not expired
    2. Pre-fill email address from invitation
    3. Display role information
    
    Args:
        token: Invitation token from URL query parameter
        session: Database session
        
    Returns:
        Dict with email, role_name, and expiry, or error
    """
    try:
        from app.models.user_invitation import UserInvitation
        from sqlalchemy import select
        
        logger.info(f"Verifying invitation token")
        
        # Query invitation record
        result = await session.execute(
            select(UserInvitation).where(
                UserInvitation.token == token
            )
        )
        invitation = result.scalar_one_or_none()
        
        if not invitation:
            logger.warning(f"Invalid invitation token provided")
            return {
                "success": False,
                "error": "Invalid invitation token"
            }
        
        # Check if invitation is valid
        if not invitation.is_valid():
            if invitation.status != "pending":
                logger.warning(f"Invitation already used (status: {invitation.status})")
                return {
                    "success": False,
                    "error": "Invitation has already been used"
                }
            else:
                logger.warning(f"Invitation token expired")
                return {
                    "success": False,
                    "error": "Invitation has expired"
                }
        
        # Get role name from invitation (stored as string)
        role_name = invitation.assigned_role or "User"
        
        logger.info(f"Invitation token verified for email {invitation.email}")
        
        return {
            "success": True,
            "email": invitation.email,
            "role_name": role_name,
            "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None
        }
        
    except Exception as e:
        logger.error(f"Error verifying invitation token: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def handle_signup_with_invite(
    request: SignupWithInviteRequest,
    session: AsyncSession
) -> dict:
    """
    Handle user signup using invitation token.
    
    Process:
    1. Verify invitation token
    2. Find temporary user by email from token
    3. Update user with provided data
    4. Activate user account
    5. Return login token
    
    Args:
        request: Signup data with invitation token
        session: Database session
        
    Returns:
        Dict with token and user data, or error
    """
    try:
        logger.info(f"Signup attempt with invitation token for username: {request.username}")
        
        password_service = PasswordService(session)
        user_account_service = UserAccountService(session)
        auth_service = AuthService(session)
        
        # Verify invitation token and extract email
        from app.models.user_invitation import UserInvitation
        from app.models.auth import Role
        from sqlalchemy import select
        
        result = await session.execute(
            select(UserInvitation).where(
                UserInvitation.token == request.invite_token
            )
        )
        invitation = result.scalar_one_or_none()
        
        if not invitation:
            logger.warning(f"Invalid invitation token provided for signup")
            return {
                "success": False,
                "error": "Invalid invitation token",
                "token": None,
                "user": None
            }
        
        # Check if invitation is valid
        if not invitation.is_valid():
            if invitation.status != "pending":
                logger.warning(f"Invitation already used (status: {invitation.status})")
                return {
                    "success": False,
                    "error": "Invitation has already been used",
                    "token": None,
                    "user": None
                }
            else:
                logger.warning(f"Invitation token expired")
                return {
                    "success": False,
                    "error": "Invitation has expired",
                    "token": None,
                    "user": None
                }
        
        # Email from invitation must match request
        if invitation.email != request.email.lower():
            logger.warning(f"Email mismatch for invitation token: {invitation.email} vs {request.email}")
            return {
                "success": False,
                "error": "Email does not match invitation",
                "token": None,
                "user": None
            }
        
        # Verify assigned role exists
        assigned_role = invitation.assigned_role
        role_to_assign = None
        if assigned_role:
            result = await session.execute(
                select(Role).where(Role.name == assigned_role)
            )
            role_to_assign = result.scalar_one_or_none()
            
            if not role_to_assign:
                logger.error(f"Role {assigned_role} not found for invitation")
                return {
                    "success": False,
                    "error": f"Role {assigned_role} is no longer available",
                    "token": None,
                    "user": None
                }
        
        # Now create the new user account
        new_user, create_error = await user_account_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name
        )
        
        if not new_user:
            logger.warning(f"Failed to create user account during signup: {create_error}")
            return {
                "success": False,
                "error": create_error or "Failed to create user account",
                "token": None,
                "user": None
            }
        
        # Assign role to new user if one was specified
        if role_to_assign:
            from app.services.user import RolePermissionService
            role_service = RolePermissionService(session)
            role_assigned, role_error = await role_service.assign_role_to_user(
                user_id=new_user.id,
                role_id=role_to_assign.id
            )
            
            if not role_assigned:
                logger.warning(f"Failed to assign role to user: {role_error}")
                # Don't fail the signup if role assignment fails - continue anyway
        
        # Mark invitation as accepted and verify user (user verified through invitation)
        now = datetime.now(timezone.utc)
        invitation.status = "accepted"
        invitation.accepted_at = now
        
        # Set user as verified since they completed invitation signup
        new_user.is_verified = True
        
        await session.flush()
        await session.commit()
        
        logger.info(f"User {new_user.username} completed signup with invitation")
        
        # Load user roles explicitly from database (avoid lazy loading in async context)
        from sqlalchemy import select
        roles_result = await session.execute(
            select(Role).join(Role.users).where(Role.users.any(User.id == new_user.id))
        )
        user_roles = roles_result.scalars().all()
        
        # Generate JWT token for immediate login
        token = create_access_token(new_user.id)
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_at = datetime.now(timezone.utc) + expires_delta
        
        # Format roles
        roles = [
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_system": role.is_system,
            }
            for role in user_roles
        ]
        
        return {
            "success": True,
            "token": token,
            "expires_at": expires_at.isoformat(),
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "full_name": f"{new_user.first_name} {new_user.last_name}".strip(),
                "is_active": new_user.is_active,
                "is_verified": new_user.is_verified,
                "is_suspended": new_user.is_suspended,
                "roles": roles,
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling signup with invitation: {str(e)}", exc_info=True)
        await session.rollback()
        
        # Don't expose detailed error messages to frontend - use generic message
        # Log the real error for debugging, but return safe message to client
        error_message = "Failed to complete signup. Please try again or contact support."
        
        return {
            "success": False,
            "error": error_message,
            "token": None,
            "user": None
        }

