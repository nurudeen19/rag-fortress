"""
Settings cache management for runtime updates.

Handles in-memory caching of settings that can be updated
without restarting the application.
"""
from typing import Dict
from app.core import get_logger

logger = get_logger(__name__)

# In-memory cache for runtime settings
_settings_cache: Dict[str, str] = {}


def load_settings_into_memory(settings_dict: Dict[str, str]) -> None:
    """
    Load settings into in-memory cache.
    
    This allows runtime access to updated settings without
    requiring an application restart.
    
    Args:
        settings_dict: Dictionary of {key: value} settings
    """
    global _settings_cache
    _settings_cache.clear()
    _settings_cache.update(settings_dict)
    logger.debug(f"Loaded {len(settings_dict)} settings into memory cache")


def get_setting_from_memory(key: str, default=None):
    """
    Get a setting from in-memory cache.
    
    Args:
        key: Setting key
        default: Default value if not found
        
    Returns:
        Setting value or default
    """
    return _settings_cache.get(key, default)


def clear_settings_cache() -> None:
    """Clear all settings from memory cache."""
    global _settings_cache
    _settings_cache.clear()
    logger.debug("Cleared settings memory cache")


def get_all_cached_settings() -> Dict[str, str]:
    """
    Get all cached settings.
    
    Returns:
        Dictionary of all cached settings
    """
    return _settings_cache.copy()
