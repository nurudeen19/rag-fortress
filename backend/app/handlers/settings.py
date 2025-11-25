"""Settings handlers - business logic orchestration for settings operations."""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger
from app.services.settings_service import SettingsService


logger = get_logger(__name__)


async def handle_get_all_settings(
    session: AsyncSession,
    category: Optional[str] = None
) -> List[Dict]:
    """
    Get all application settings.
    
    Args:
        session: Database session
        category: Optional category filter
        
    Returns:
        List of setting dicts
    """
    try:
        service = SettingsService(session)
        settings = await service.get_all(category=category)
        
        return [
            {
                "id": s.id,
                "key": s.key,
                "value": s.value,
                "data_type": s.data_type,
                "description": s.description,
                "category": s.category,
                "is_mutable": s.is_mutable,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in settings
        ]
        
    except Exception as e:
        logger.error(f"Handle get all settings failed: {e}", exc_info=True)
        raise


async def handle_get_setting(
    key: str,
    session: AsyncSession
) -> Optional[Dict]:
    """
    Get single setting by key.
    
    Args:
        key: Setting key
        session: Database session
        
    Returns:
        Setting dict or None
    """
    try:
        service = SettingsService(session)
        setting = await service.get_by_key(key)
        
        if not setting:
            return None
        
        return {
            "id": setting.id,
            "key": setting.key,
            "value": setting.value,
            "data_type": setting.data_type,
            "description": setting.description,
            "category": setting.category,
            "is_mutable": setting.is_mutable,
            "created_at": setting.created_at.isoformat() if setting.created_at else None,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None
        }
        
    except Exception as e:
        logger.error(f"Handle get setting '{key}' failed: {e}", exc_info=True)
        raise


async def handle_update_setting(
    key: str,
    value: str,
    session: AsyncSession
) -> Dict:
    """
    Update setting value.
    
    Args:
        key: Setting key
        value: New value
        session: Database session
        
    Returns:
        Updated setting dict
    """
    try:
        service = SettingsService(session)
        setting = await service.update(key, value)
        
        return {
            "id": setting.id,
            "key": setting.key,
            "value": setting.value,
            "data_type": setting.data_type,
            "description": setting.description,
            "category": setting.category,
            "is_mutable": setting.is_mutable,
            "created_at": setting.created_at.isoformat() if setting.created_at else None,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None
        }
        
    except Exception as e:
        logger.error(f"Handle update setting '{key}' failed: {e}", exc_info=True)
        raise


async def handle_update_settings_bulk(
    updates: List[Dict[str, str]],
    session: AsyncSession
) -> Dict:
    """
    Update multiple settings in bulk.
    
    Args:
        updates: List of {key, value} dicts
        session: Database session
        
    Returns:
        Result dict with success/error counts
    """
    try:
        service = SettingsService(session)
        result = await service.update_bulk(updates)
        
        return result
        
    except Exception as e:
        logger.error(f"Handle bulk update settings failed: {e}", exc_info=True)
        raise


async def handle_get_categories(session: AsyncSession) -> List[str]:
    """
    Get all setting categories.
    
    Args:
        session: Database session
        
    Returns:
        List of category names
    """
    try:
        service = SettingsService(session)
        categories = await service.get_categories()
        
        return categories
        
    except Exception as e:
        logger.error(f"Handle get categories failed: {e}", exc_info=True)
        raise

