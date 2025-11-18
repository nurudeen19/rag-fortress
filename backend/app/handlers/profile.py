"""
User profile request handlers.

Handlers manage HTTP requests for:
- Retrieving user profile information
- Updating user profile information
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.user import UserProfileService

logger = logging.getLogger(__name__)


async def handle_get_current_user_profile(
    current_user: User,
    session: AsyncSession
) -> dict:
    """
    Handle get current user's profile request.
    
    Args:
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Dict with user profile data or error
    """
    try:
        service = UserProfileService(session)
        profile, error = await service.get_user_profile(current_user.id)
        
        if error:
            logger.warning(f"Failed to retrieve profile for user {current_user.id}: {error}")
            return {"success": False, "error": "Could not retrieve profile. Please try again."}
        
        logger.info(f"Retrieved profile for user {current_user.username}")
        return {
            "success": True,
            "profile": profile
        }
    except Exception as e:
        logger.error(f"Error retrieving profile for user {current_user.id}: {str(e)}", exc_info=True)
        return {"success": False, "error": "An unexpected error occurred. Please try again."}


async def handle_update_current_user_profile(
    current_user: User,
    update_data: dict,
    session: AsyncSession
) -> dict:
    """
    Handle update current user's profile request.
    
    Args:
        current_user: Current authenticated user
        update_data: Data to update
        session: Database session
        
    Returns:
        Dict with success status or error
    """
    try:
        service = UserProfileService(session)
        
        # Validate that we only update allowed fields
        allowed_fields = {
            "first_name", "last_name", "phone_number", "location",
            "job_title", "about", "avatar_url"
        }
        
        # Filter to only allowed fields
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_data:
            logger.warning(f"User {current_user.id} attempted profile update with no valid fields")
            return {"success": False, "error": "No valid fields to update"}
        
        success, error = await service.update_user_profile(current_user.id, filtered_data)
        
        if error:
            logger.warning(f"Failed to update profile for user {current_user.id}: {error}")
            return {"success": False, "error": error}
        
        # Retrieve updated profile
        profile, _ = await service.get_user_profile(current_user.id)
        
        logger.info(f"Updated profile for user {current_user.username}")
        return {
            "success": True,
            "message": "Profile updated successfully",
            "profile": profile
        }
    except Exception as e:
        logger.error(f"Error updating profile for user {current_user.id}: {str(e)}", exc_info=True)
        return {"success": False, "error": "An unexpected error occurred. Please try again."}
