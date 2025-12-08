"""
Demo Mode Protection Utility

Provides decorator to prevent destructive actions when DEMO_MODE=true.
Simple, centralized protection for public demo deployments.
"""

from functools import wraps
from fastapi import HTTPException, status
from app.config.settings import settings


def prevent_in_demo_mode(action_description: str = "This action"):
    """
    Decorator to prevent destructive actions in demo mode.
    
    Usage:
        @prevent_in_demo_mode("Delete user")
        async def delete_user(...):
            ...
    
    Args:
        action_description: Human-readable description of the blocked action
        
    Returns:
        Decorator function that blocks execution in demo mode
        
    Raises:
        HTTPException: 403 Forbidden if action attempted in demo mode
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if settings.app_settings.DEMO_MODE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{action_description} is disabled in demo mode. This is a read-only demonstration environment."
                )
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if settings.app_settings.DEMO_MODE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{action_description} is disabled in demo mode. This is a read-only demonstration environment."
                )
            return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def is_demo_mode() -> bool:
    """
    Check if application is running in demo mode.
    
    Returns:
        bool: True if DEMO_MODE is enabled
    """
    return settings.app_settings.DEMO_MODE
