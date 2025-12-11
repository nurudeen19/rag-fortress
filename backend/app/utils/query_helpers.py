"""
Query helpers for common eager loading patterns.

This module provides reusable query options for eager loading relationships
to avoid lazy loading issues in async contexts and improve query performance.
"""

from sqlalchemy.orm import joinedload, selectinload
from typing import Any

from app.models.conversation import Conversation
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.models.file_upload import FileUpload



def with_user_relations(query: Any, include_profile: bool = True, include_department: bool = True, include_roles: bool = True) -> Any:
    """
    Add eager loading for User relationships.
    
    This helper ensures User objects are loaded with their related data
    to avoid lazy loading issues in async contexts.
    
    Args:
        query: SQLAlchemy query object
        include_profile: Load user_profile relationship
        include_department: Load department relationship
        include_roles: Load roles relationship
        
    Returns:
        Query with eager loading options applied
        
    Example:
        # Load users with all relationships
        query = select(User).where(User.is_active.is_(True))
        query = with_user_relations(query)
        result = await session.execute(query)
        users = result.scalars().all()
        
        # Load users with only department (no profile or roles)
        query = select(User)
        query = with_user_relations(query, include_profile=False, include_roles=False)
    """
    
    if include_profile:
        query = query.options(joinedload(User.profile))
    
    if include_department:
        query = query.options(joinedload(User.department))
    
    if include_roles:
        query = query.options(selectinload(User.roles))
    
    return query


def with_full_user_context(query: Any) -> Any:
    """
    Add complete eager loading for User with all common relationships.
    
    Loads: profile, department, roles, permission, and permission_overrides.
    Use this when you need complete user context (e.g., for user details pages).
    
    Args:
        query: SQLAlchemy query object
        
    Returns:
        Query with full user context eager loading
        
    Example:
        query = select(User).where(User.id == user_id)
        query = with_full_user_context(query)
        result = await session.execute(query)
        user = result.scalar_one()
    """
    
    return query.options(
        joinedload(User.profile),
        joinedload(User.department),
        selectinload(User.roles),
        joinedload(User.user_permission),
        selectinload(User.permission_overrides)
    )


def with_activity_log_relations(query: Any) -> Any:
    """
    Add eager loading for ActivityLog relationships.
    
    Loads user with their profile and department to avoid lazy loading
    when accessing user_name and user_department properties.
    
    Args:
        query: SQLAlchemy query object
        
    Returns:
        Query with ActivityLog eager loading options
        
    Example:
        query = select(ActivityLog).where(ActivityLog.severity == 'critical')
        query = with_activity_log_relations(query)
        result = await session.execute(query)
        logs = result.unique().scalars().all()
    """
    
    return query.options(
        # joinedload(ActivityLog.user).joinedload(User.profile),
        joinedload(ActivityLog.user).joinedload(User.department)
    )


def with_file_upload_relations(query: Any) -> Any:
    """
    Add eager loading for FileUpload relationships.
    
    Loads user, department, and uploaded_by user with their profiles.
    
    Args:
        query: SQLAlchemy query object
        
    Returns:
        Query with FileUpload eager loading options
        
    Example:
        query = select(FileUpload).where(FileUpload.status == 'pending')
        query = with_file_upload_relations(query)
        result = await session.execute(query)
        uploads = result.scalars().all()
    """
    
    return query.options(
        joinedload(FileUpload.user).joinedload(User.profile),
        joinedload(FileUpload.user).joinedload(User.department),
        joinedload(FileUpload.department)
    )


def with_conversation_relations(query: Any) -> Any:
    """
    Add eager loading for Conversation relationships.
    
    Loads user with profile for conversation context.
    
    Args:
        query: SQLAlchemy query object
        
    Returns:
        Query with Conversation eager loading options
        
    Example:
        query = select(Conversation).where(Conversation.user_id == user_id)
        query = with_conversation_relations(query)
        result = await session.execute(query)
        conversations = result.scalars().all()
    """
    
    return query.options(
        joinedload(Conversation.user).joinedload(User.profile)
    )
