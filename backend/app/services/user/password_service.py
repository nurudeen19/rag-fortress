"""
Password service for handling password changes, resets, and validation.
Provides secure password management with validation rules.
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.core import get_logger


logger = get_logger(__name__)


class PasswordService:
    """Service for password management and security."""
    
    # Password validation rules
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    RESET_TOKEN_EXPIRY_HOURS = 24
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self.pwd_context = CryptContext(
            schemes=["argon2"],
            deprecated="auto"
        )
    
    def validate_password_strength(self, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password meets security requirements.
        
        Args:
            password: Plain text password to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        if len(password) < self.MIN_LENGTH:
            return False, f"Password must be at least {self.MIN_LENGTH} characters"
        
        if len(password) > self.MAX_LENGTH:
            return False, f"Password must be at most {self.MAX_LENGTH} characters"
        
        # Check for uppercase
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for lowercase
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for digit
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        # Check for special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character"
        
        return True, None
    
    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user password (requires current password verification).
        
        Args:
            user_id: User ID
            current_password: Current plain text password
            new_password: New plain text password
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not self.pwd_context.verify(current_password, user.password_hash):
                logger.warning(f"Change password failed: invalid current password for user {user_id}")
                return False, "Current password is incorrect"
            
            # Validate new password
            is_valid, error = self.validate_password_strength(new_password)
            if not is_valid:
                return False, error
            
            # Prevent using same password
            if self.pwd_context.verify(new_password, user.password_hash):
                return False, "New password must be different from current password"
            
            # Update password
            user.password_hash = self.pwd_context.hash(new_password)
            await self.session.flush()
            
            logger.info(f"Password changed for user: {user.username}")
            return True, None
        
        except Exception as e:
            logger.error(f"Change password error: {e}")
            return False, "Failed to change password"
    
    async def request_password_reset(self, email: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate password reset token for user.
        
        Args:
            email: User email address
        
        Returns:
            Tuple of (reset_token, error_message)
        """
        try:
            user = None
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal whether email exists for security
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return None, None
            
            # Generate reset token
            token = secrets.token_urlsafe(32)
            
            # Store token and expiry (in real app, use separate table or cache)
            # For now, we return the token to be sent via email
            logger.info(f"Password reset token generated for user: {user.username}")
            return token, None
        
        except Exception as e:
            logger.error(f"Request password reset error: {e}")
            return None, "Failed to request password reset"
    
    async def reset_password(
        self,
        user_id: int,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Reset password for a user (after token verification).
        
        Note: Token verification should be done before calling this method.
        
        Args:
            user_id: User ID
            new_password: New plain text password
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return False, "User not found"
            
            # Validate new password
            is_valid, error = self.validate_password_strength(new_password)
            if not is_valid:
                return False, error
            
            # Update password
            user.password_hash = self.pwd_context.hash(new_password)
            user.is_verified = True  # Mark as verified during reset
            await self.session.flush()
            
            logger.info(f"Password reset for user: {user.username}")
            return True, None
        
        except Exception as e:
            logger.error(f"Reset password error: {e}")
            return False, "Failed to reset password"
    
    def hash_password(self, password: str) -> str:
        """Hash a plain text password."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify plain text password against hash."""
        return self.pwd_context.verify(plain_password, password_hash)
    
    async def create_reset_token(self, user_id: int) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a password reset token for a user.
        
        Creates a new token record in the database with email and expiry.
        
        Args:
            user_id: User ID
        
        Returns:
            Tuple of (token, error_message)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return None, "User not found"
            
            # Generate secure token
            token = secrets.token_urlsafe(32)
            
            # Calculate expiry (24 hours from now)
            expiry = datetime.now(timezone.utc) + timedelta(hours=self.RESET_TOKEN_EXPIRY_HOURS)
            
            # Create token record in database
            reset_token = PasswordResetToken(
                user_id=user_id,
                email=user.email,
                token=token,
                expires_at=expiry,
                is_used=False
            )
            
            self.session.add(reset_token)
            await self.session.flush()
            
            logger.info(f"Reset token created for user {user_id} (email: {user.email})")
            return token, None
        
        except Exception as e:
            logger.error(f"Create reset token error: {e}")
            return None, "Failed to create reset token"
    
    async def verify_reset_token(
        self,
        token: str,
        email: str
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Verify a password reset token from the database.
        
        Checks:
        - Token exists in database
        - Token matches the provided email
        - Token has not expired
        - Token has not been used
        
        On success, marks token as used.
        
        Args:
            token: Reset token
            email: User email to verify against token
        
        Returns:
            Tuple of (user_id, error_message)
        """
        try:
            # Query for valid token
            result = await self.session.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.token == token,
                    PasswordResetToken.email == email
                )
            )
            reset_token = result.scalar_one_or_none()
            
            if not reset_token:
                logger.warning(f"Invalid reset token attempted (email: {email})")
                return None, "Invalid reset token"
            
            # Check if already used
            if reset_token.is_used:
                logger.warning(f"Reset token already used (email: {email})")
                return None, "Reset token has already been used"
            
            # Check if expired
            now = datetime.now(timezone.utc)
            
            # Make both naive for comparison if needed
            expires_at = reset_token.expires_at
            if expires_at.tzinfo is not None and now.tzinfo is not None:
                # Both aware - compare directly
                if now > expires_at:
                    logger.warning(f"Reset token expired (email: {email})")
                    return None, "Reset token has expired"
            else:
                # At least one is naive - make both naive
                now_naive = now.replace(tzinfo=None)
                expires_at_naive = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
                if now_naive > expires_at_naive:
                    logger.warning(f"Reset token expired (email: {email})")
                    return None, "Reset token has expired"
            
            # Mark as used
            reset_token.is_used = True
            reset_token.used_at = now
            await self.session.flush()
            
            logger.info(f"Reset token verified and consumed for user {reset_token.user_id}")
            return reset_token.user_id, None
        
        except Exception as e:
            logger.error(f"Verify reset token error: {e}")
            return None, "Failed to verify reset token"
    
    async def is_reset_token_valid(self, token: str) -> bool:
        """
        Check if a password reset token is valid without consuming it.
        
        Used by frontend to verify token before showing password reset form.
        
        Args:
            token: Reset token
        
        Returns:
            True if token is valid and not expired/used
        """
        try:
            # Query for token
            result = await self.session.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.token == token
                )
            )
            reset_token = result.scalar_one_or_none()
            
            if not reset_token:
                logger.debug(f"Invalid reset token: token not found")
                return False
            
            # Check if already used
            if reset_token.is_used:
                logger.debug(f"Reset token already used (user: {reset_token.user_id})")
                return False
            
            # Check if expired (handle both naive and aware datetimes)
            now = datetime.now(timezone.utc)
            expires_at = reset_token.expires_at
            
            # Make both naive for comparison if needed
            if expires_at.tzinfo is not None and now.tzinfo is not None:
                # Both aware - compare directly
                if now > expires_at:
                    logger.debug(f"Reset token expired (user: {reset_token.user_id})")
                    return False
            else:
                # At least one is naive - make both naive
                now_naive = now.replace(tzinfo=None)
                expires_at_naive = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
                if now_naive > expires_at_naive:
                    logger.debug(f"Reset token expired (user: {reset_token.user_id})")
                    return False
            
            logger.debug(f"Reset token is valid (user: {reset_token.user_id})")
            return True
        
        except Exception as e:
            logger.error(f"Error checking reset token validity: {e}")
            return False
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Delete expired password reset tokens from database.
        
        This can be run periodically (e.g., daily) to clean up old tokens.
        
        Returns:
            Number of tokens deleted
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Query expired tokens
            result = await self.session.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.expires_at < now
                )
            )
            expired_tokens = result.scalars().all()
            count = len(expired_tokens)
            
            # Delete them
            for token in expired_tokens:
                await self.session.delete(token)
            
            await self.session.flush()
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired password reset tokens")
            
            return count
        
        except Exception as e:
            logger.error(f"Cleanup expired tokens error: {e}")
            return 0
