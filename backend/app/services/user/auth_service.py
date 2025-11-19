"""
Authentication service for handling login, logout, and token management.
Manages user sessions and JWT token lifecycle.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.models.user import User
from app.core import get_logger


logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        # Password hashing context
        self.pwd_context = CryptContext(
            schemes=["argon2"],
            deprecated="auto"
        )
    
    async def login(
        self,
        username_or_email: str,
        password: str
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate user with username/email and password.
        
        Args:
            username_or_email: Username or email address
            password: Plain text password
        
        Returns:
            Tuple of (User, None) if success, (None, error_message) if failure
        """
        try:
            # Find user by username or email with eager loading of roles
            from sqlalchemy.orm import selectinload
            result = await self.session.execute(
                select(User)
                .where(
                    (User.username == username_or_email) |
                    (User.email == username_or_email)
                )
                .options(selectinload(User.roles))
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Login failed: user not found '{username_or_email}'")
                return None, "Invalid credentials"
            
            # Check if account is suspended or inactive FIRST (before password verification)
            # This prevents attackers from knowing if an account exists
            if user.is_suspended:
                reason = f" ({user.suspension_reason})" if user.suspension_reason else ""
                logger.warning(f"Login failed: account suspended for user '{user.username}'{reason}")
                return None, f"Account is locked{reason}"
            
            if not user.is_active:
                logger.warning(f"Login failed: account inactive for user '{user.username}'")
                return None, "Account is locked"
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                logger.warning(f"Login failed: invalid password for user '{user.username}'")
                return None, "Invalid credentials"
            
            # Check if account is verified
            if not user.is_verified:
                logger.warning(f"Login attempted: unverified account '{user.username}'")
                return None, "Account not verified. Please check your email."
            
            logger.info(f"Successful login: '{user.username}'")
            return user, None
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            return None, "Login failed. Please try again."
    
    async def logout(self, user_id: int) -> bool:
        """
        Logout user. Currently a no-op since we use stateless JWT tokens.
        Can be extended for session/token blacklisting.
        
        Args:
            user_id: User ID to logout
        
        Returns:
            True if logout successful
        """
        try:
            logger.info(f"User logged out: ID {user_id}")
            # In a stateless JWT system, logout is handled client-side (token deletion)
            # Could implement token blacklisting here if needed
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash a plain text password."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify plain text password against hash."""
        return self.pwd_context.verify(plain_password, password_hash)
    
    async def verify_email(self, user_id: int) -> Optional[User]:
        """
        Mark user email as verified.
        
        Args:
            user_id: User ID to verify
        
        Returns:
            Updated user or None if not found
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return None
            
            if user.is_verified:
                logger.warning(f"Email already verified for user ID {user_id}")
                return user
            
            user.is_verified = True
            await self.session.flush()
            
            logger.info(f"Email verified for user: '{user.username}'")
            return user
        
        except Exception as e:
            logger.error(f"Email verification error: {e}")
            raise
    
    async def check_user_exists(self, username: str = None, email: str = None) -> bool:
        """
        Check if user exists by username or email.
        
        Args:
            username: Username to check
            email: Email to check
        
        Returns:
            True if user exists, False otherwise
        """
        try:
            if username:
                result = await self.session.execute(
                    select(User).where(User.username == username).limit(1)
                )
                if result.scalar_one_or_none():
                    return True
            
            if email:
                result = await self.session.execute(
                    select(User).where(User.email == email).limit(1)
                )
                if result.scalar_one_or_none():
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Check user exists error: {e}")
            raise
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            return await self.session.get(User, user_id)
        except Exception as e:
            logger.error(f"Get user error: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Get user by email error: {e}")
            raise
