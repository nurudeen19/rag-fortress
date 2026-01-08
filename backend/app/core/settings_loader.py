"""
Settings loader for application startup.

Loads settings from database grouped by category for caching.
"""

from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import ApplicationSetting
from app.core import get_logger

logger = get_logger(__name__)


async def load_settings_by_category(session: AsyncSession) -> Dict[str, Dict[str, dict]]:
    """
    Load all settings from database grouped by category.
    
    SECURITY: Keeps sensitive values encrypted. Decryption happens only when accessed.
    
    Args:
        session: Database session
    
    Returns:
        Dict of {category: {key: {"value": str, "is_sensitive": bool, "is_mutable": bool}}}
        Example: {"llm": {"openai_api_key": {"value": "encrypted...", "is_sensitive": True, "is_mutable": True}}}
    """
    try:
        result = await session.execute(select(ApplicationSetting))
        settings = result.scalars().all()
        
        # Group by category with metadata
        grouped = {}
        for setting in settings:
            if not setting.category:
                continue
            
            if setting.category not in grouped:
                grouped[setting.category] = {}
            
            # Store encrypted value with is_sensitive flag
            # Decryption will happen lazily when accessed
            grouped[setting.category][setting.key] = {
                "value": setting.value,
                "is_sensitive": setting.is_sensitive,
                "is_mutable": setting.is_mutable,
            }
        
        logger.info(f"Loaded {len(settings)} settings across {len(grouped)} categories")
        return grouped
        
    except Exception as e:
        logger.warning(f"Failed to load settings from database: {e}")
        return {}
