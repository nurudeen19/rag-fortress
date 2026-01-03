"""
User profile service for managing user profile information.
Handles retrieval and updating of user profile data.
"""

from typing import Optional, Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.user_profile import UserProfile
from app.core import get_logger


logger = get_logger(__name__)


class UserProfileService:
    """Service for managing user profile information."""
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
    
    async def get_user_profile(self, user_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Retrieve complete user profile information.
        
        Args:
            user_id: ID of the user
        
        Returns:
            Tuple of (profile_data, error_message) where error_message is user-friendly
        """
        try:
            # Get user with related data
            result = await self.session.execute(
                select(User)
                .options(
                    selectinload(User.roles),
                    selectinload(User.department),
                    selectinload(User.profile),
                )
                .where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Profile retrieval attempt for non-existent user {user_id}")
                return None, "User not found"
            
            # Get user profile if exists
            profile_result = await self.session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = profile_result.scalar_one_or_none()
            
            # Get user's roles
            roles = [
                {
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "is_system": role.is_system,
                }
                for role in user.roles
            ]
            
            # Get department info if exists
            department = None
            if user.department:
                department = {
                    "id": user.department.id,
                    "name": user.department.name,
                }
            
            # Format response
            profile_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "department": department,
                "roles": roles,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_suspended": user.is_suspended,
                "suspension_reason": user.suspension_reason,
                # Profile extended fields
                "about": profile.about if profile else None,
                "avatar_url": profile.avatar_url if profile else None,
                "phone_number": profile.phone_number if profile else None,
                "location": profile.location if profile else None,
                "job_title": profile.job_title if profile else None,
            }
            
            return profile_data, None
            
        except Exception as e:
            logger.error(f"Error retrieving profile for user {user_id}: {str(e)}", exc_info=True)
            return None, "Failed to retrieve profile"
    
    async def update_user_profile(
        self,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Update user profile information.
        Only updatable fields: first_name, last_name, phone_number, location, job_title, about, avatar_url
        
        Args:
            user_id: ID of the user to update
            update_data: Dictionary with fields to update
        
        Returns:
            Tuple of (success, error_message) where error_message is user-friendly
        """
        try:
            # Get user
            result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Profile update attempt for non-existent user {user_id}")
                return False, "User not found"
            
            # List of updatable fields on User model
            updatable_user_fields = {"first_name", "last_name"}
            
            # List of updatable fields on UserProfile model
            updatable_profile_fields = {
                "about", "avatar_url", "phone_number", "location", "job_title"
            }
            
            # Update User fields
            user_updates = {}
            for field in updatable_user_fields:
                if field in update_data:
                    value = update_data[field]
                    # Validate non-empty strings
                    if isinstance(value, str):
                        value = value.strip()
                        if not value:
                            logger.warning(f"User {user_id} attempted to set empty {field}")
                            return False, f"{field.replace('_', ' ').title()} cannot be empty"
                    user_updates[field] = value
            
            if user_updates:
                for field, value in user_updates.items():
                    setattr(user, field, value)
                logger.info(f"Updated User fields for {user.username}: {list(user_updates.keys())}")
            
            # Get or create user profile
            profile_result = await self.session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = profile_result.scalar_one_or_none()
            
            if not profile:
                profile = UserProfile(user_id=user_id)
                self.session.add(profile)
                await self.session.flush()
            
            # Update profile fields
            profile_updates = {}
            for field in updatable_profile_fields:
                if field in update_data:
                    value = update_data[field]
                    # Allow None/empty values for profile fields
                    if isinstance(value, str):
                        value = value.strip() if value else None
                    profile_updates[field] = value
            
            if profile_updates:
                for field, value in profile_updates.items():
                    setattr(profile, field, value)
                logger.info(f"Updated UserProfile fields for user {user.username}: {list(profile_updates.keys())}")
            
            # Commit changes
            await self.session.commit()
            logger.info(f"Successfully updated profile for user {user.username}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {str(e)}", exc_info=True)
            await self.session.rollback()
            return False, "Failed to update profile"
    
    async def get_current_user_profile(self, current_user: User) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get the current authenticated user's profile.
        
        Args:
            current_user: Current authenticated user object
        
        Returns:
            Tuple of (profile_data, error_message)
        """
        return await self.get_user_profile(current_user.id)
