"""
User account service for creating, activating, and managing user accounts.
Handles user registration, account lifecycle, and profile management.
"""

from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.user_permission import PermissionLevel
from app.core import get_logger
from app.services.user.password_service import PasswordService
from app.utils.user_clearance_cache import get_user_clearance_cache


logger = get_logger(__name__)


class UserAccountService:
    """Service for user account management."""
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self.password_service = PasswordService(session)
    
    async def create_user(
        self,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
        department_id: Optional[int] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            email: Unique email address
            first_name: First name
            last_name: Last name
            password: Plain text password
            department_id: Optional department assignment
        
        Returns:
            Tuple of (created_user, error_message)
        """
        try:
            # Validate password strength
            is_valid, error = self.password_service.validate_password_strength(password)
            if not is_valid:
                return None, error
            
            # Check username doesn't exist
            result = await self.session.execute(
                select(User).where(User.username == username).limit(1)
            )
            if result.scalar_one_or_none():
                return None, "Username already exists"
            
            # Check email doesn't exist
            result = await self.session.execute(
                select(User).where(User.email == email).limit(1)
            )
            if result.scalar_one_or_none():
                return None, "Email already exists"
            
            # Create user
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=self.password_service.hash_password(password),
                department_id=department_id,
                is_active=True,
                is_verified=False,  # Requires email verification
                is_suspended=False,
            )
            
            self.session.add(user)
            await self.session.flush()
            
            return user, None
        
        except Exception as e:
            logger.error(f"Create user error: {e}")
            return None, "Failed to create user account"
    
    async def activate_user_account(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Activate a user account (set is_active=True).
        
        Args:
            user_id: User ID to activate
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return False, "User not found"
            
            if user.is_active:
                return True, None  # Already active
            
            user.is_active = True
            await self.session.flush()
            
            logger.info(f"User account activated: '{user.username}'")
            return True, None
        
        except Exception as e:
            logger.error(f"Activate user error: {e}")
            return False, "Failed to activate account"
    
    async def deactivate_user_account(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Deactivate a user account (set is_active=False).
        
        Args:
            user_id: User ID to deactivate
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return False, "User not found"
            
            if not user.is_active:
                return True, None  # Already inactive
            
            user.is_active = False
            await self.session.flush()
            
            logger.info(f"User account deactivated: '{user.username}'")
            return True, None
        
        except Exception as e:
            logger.error(f"Deactivate user error: {e}")
            return False, "Failed to deactivate account"
    
    async def suspend_user_account(
        self,
        user_id: int,
        reason: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """
        Suspend a user account (prevents login).
        
        Args:
            user_id: User ID to suspend
            reason: Reason for suspension
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            from sqlalchemy import select
            
            # Fetch user with explicit query
            result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            if user.is_suspended:
                return True, None  # Already suspended
            
            user.suspend_account(reason)
            await self.session.commit()
            
            logger.warning(f"User account suspended: '{user.username}' - Reason: {reason}")
            return True, None
        
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Suspend user error: {e}")
            return False, "Failed to suspend account"
    
    async def unsuspend_user_account(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Unsuspend a user account (restore login ability).
        
        Args:
            user_id: User ID to unsuspend
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            from sqlalchemy import select
            
            # Fetch user with explicit query
            result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            if not user.is_suspended:
                return True, None  # Not suspended
            
            user.unsuspend_account()
            await self.session.commit()
            
            logger.info(f"User account unsuspended: '{user.username}'")
            return True, None
        
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Unsuspend user error: {e}")
            return False, "Failed to unsuspend account"
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            return await self.session.get(User, user_id)
        except Exception as e:
            logger.error(f"Get user error: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
        
        Returns:
            User object if found, None otherwise
        """
        try:
            result = await self.session.execute(
                select(User).where(User.email == email).limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Get user by email error: {e}")
            raise
    
    async def list_users(
        self,
        active_only: bool = True,
        department_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[User]:
        """
        List users with optional filtering.
        
        Args:
            active_only: Only return active users
            department_id: Filter by department
            limit: Result limit
            offset: Result offset
        
        Returns:
            List of User objects
        """
        try:
            from sqlalchemy.orm import selectinload
            query = select(User).options(selectinload(User.roles))
            
            if active_only:
                query = query.where(User.is_active.is_(True))
            
            if department_id:
                query = query.where(User.department_id == department_id)
            
            query = query.offset(offset).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
        
        except Exception as e:
            logger.error(f"List users error: {e}")
            raise
    
    async def update_user_profile(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        job_title: Optional[str] = None,
        location: Optional[str] = None,
        avatar_url: Optional[str] = None,
        about: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Update user profile information.
        
        Args:
            user_id: User ID to update
            first_name: New first name
            last_name: New last name
            phone_number: New phone number
            job_title: New job title
            location: New location
            avatar_url: New avatar URL
            about: About/bio text
        
        Returns:
            Tuple of (updated_user, error_message)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return None, "User not found"
            
            # Update main user fields
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            
            # Get or create profile
            profile = user.profile
            if not profile:
                profile = UserProfile(user_id=user_id)
                self.session.add(profile)
            
            # Update profile fields
            if phone_number is not None:
                profile.phone_number = phone_number
            if job_title is not None:
                profile.job_title = job_title
            if location is not None:
                profile.location = location
            if avatar_url is not None:
                profile.avatar_url = avatar_url
            if about is not None:
                profile.about = about
            
            await self.session.flush()
            
            logger.info(f"User profile updated: '{user.username}'")
            return user, None
        
        except Exception as e:
            logger.error(f"Update user profile error: {e}")
            return None, "Failed to update profile"
    
    async def delete_user(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Soft delete user (mark as inactive and suspended).
        
        Args:
            user_id: User ID to delete
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return False, "User not found"
            
            # Soft delete: deactivate and suspend
            user.is_active = False
            user.suspend_account("Account deleted by user")
            await self.session.flush()
            
            logger.info(f"User deleted (soft): '{user.username}'")
            return True, None
        
        except Exception as e:
            logger.error(f"Delete user error: {e}")
            return False, "Failed to delete account"
    
    async def get_user_clearance_info(self, user_id: int) -> Optional[dict]:
        """
        Get user's clearance information (security level and department).
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with 'clearance', 'department_id', 'department_security_level' or None if not found
        """
        try:            
            
            clearance_cache = get_user_clearance_cache(self.session)
            clearance = await clearance_cache.get_clearance(user_id)
            
            if not clearance:
                logger.warning(f"User clearance not found for user_id={user_id}")
                return None
            
            # Convert security level strings to PermissionLevel enums
            dept_security_level = None
            if clearance.get("department_security_level"):
                dept_security_level = PermissionLevel[clearance["department_security_level"]]
            
            return {
                "clearance": PermissionLevel[clearance["security_level"]],
                "department_security_level": dept_security_level,
                "department_id": clearance["department_id"]
            }
        
        except Exception as e:
            logger.error(f"Failed to get user clearance info: {e}")
            return None
