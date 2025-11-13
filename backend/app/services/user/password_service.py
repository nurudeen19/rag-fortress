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
from app.core import get_logger


logger = get_logger(__name__)


class PasswordResetTokenStatus(str, Enum):
    """Status of password reset token."""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    ALREADY_USED = "already_used"


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
        email: str,
        reset_token: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Reset password using reset token (typically from email).
        
        Note: In production, verify token expiry and validity via token store/cache.
        This is a simplified implementation.
        
        Args:
            email: User email address
            reset_token: Password reset token from email
            new_password: New plain text password
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = None
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            # Validate new password
            is_valid, error = self.validate_password_strength(new_password)
            if not is_valid:
                return False, error
            
            # In production: verify token validity and expiry from token store
            # For now, assuming token validation is done by caller
            
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
