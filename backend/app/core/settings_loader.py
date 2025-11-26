"""
Settings loader for application startup.

Loads settings from database grouped by category for caching.
"""

from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import ApplicationSetting
from app.utils.encryption import decrypt_value
from app.core import get_logger

logger = get_logger(__name__)


async def load_settings_by_category(session: AsyncSession) -> Dict[str, Dict[str, str]]:
    """
    Load all settings from database grouped by category.
    
    Decrypts sensitive values (API keys, passwords) on load.
    
    Args:
        session: Database session
    
    Returns:
        Dict of {category: {key: value}}
        Example: {"llm": {"openai_api_key": "sk-...", "llm_model": "gpt-4"}}
    """
    try:
        result = await session.execute(select(ApplicationSetting))
        settings = result.scalars().all()
        
        # Group by category
        grouped = {}
        for setting in settings:
            if not setting.category:
                continue
            
            if setting.category not in grouped:
                grouped[setting.category] = {}
            
            # Decrypt if sensitive and has value
            value = setting.value
            if value and setting.is_sensitive:
                value = decrypt_value(value)
            
            grouped[setting.category][setting.key] = value
        
        logger.info(f"Loaded {len(settings)} settings across {len(grouped)} categories")
        return grouped
        
    except Exception as e:
        logger.warning(f"Failed to load settings from database: {e}")
        return {}
