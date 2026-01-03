"""
Settings Service - Business logic for application settings operations.

Handles encryption/decryption of sensitive settings (API keys, passwords).
Updates invalidate memory cache and Redis cache for individual setting keys.
"""

import json
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from app.core import get_logger
from app.models.application_setting import ApplicationSetting
from app.utils.encryption import encrypt_value, decrypt_value

logger = get_logger(__name__)


class SettingsService:
    """Manages CRUD operations for application settings."""
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
    
    async def get_all(self, category: Optional[str] = None) -> List[ApplicationSetting]:
        """
        Get all application settings, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of ApplicationSetting objects
        """
        try:
            stmt = select(ApplicationSetting).order_by(ApplicationSetting.category, ApplicationSetting.key)
            
            if category:
                stmt = stmt.where(ApplicationSetting.category == category)
            
            result = await self.session.execute(stmt)
            settings = result.scalars().all()
            
            return settings
            
        except Exception as e:
            logger.error(f"Failed to get settings: {e}", exc_info=True)
            raise
    
    async def get_by_key(self, key: str) -> Optional[ApplicationSetting]:
        """
        Get setting by key.
        
        Args:
            key: Setting key
            
        Returns:
            ApplicationSetting or None if not found
        """
        try:
            stmt = select(ApplicationSetting).where(ApplicationSetting.key == key)
            result = await self.session.execute(stmt)
            setting = result.scalar_one_or_none()
            
            if setting:
                logger.debug(f"Retrieved setting '{key}'")
            else:
                logger.debug(f"Setting '{key}' not found")
            
            return setting
            
        except Exception as e:
            logger.error(f"Failed to get setting '{key}': {e}", exc_info=True)
            raise
    
    async def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get setting value parsed by data type (decrypts if sensitive).
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Parsed value or default
        """
        setting = await self.get_by_key(key)
        
        if not setting or not setting.value:
            return default
        
        # Decrypt if sensitive
        value = decrypt_value(setting.value) if setting.is_sensitive else setting.value
        return self._parse_value(value, setting.data_type)
    
    async def create(
        self,
        key: str,
        value: str,
        data_type: str = "string",
        description: Optional[str] = None,
        category: Optional[str] = None,
        is_mutable: bool = True
    ) -> ApplicationSetting:
        """
        Create a new setting.
        
        Args:
            key: Unique setting key
            value: Setting value as string
            data_type: Data type (string, integer, boolean, json, float)
            description: Human-readable description
            category: Category for grouping
            is_mutable: Whether setting can be modified via API
            
        Returns:
            Created ApplicationSetting
            
        Raises:
            ValueError: If key already exists or data_type invalid
        """
        try:
            # Validate data type
            valid_types = ["string", "integer", "boolean", "json", "float"]
            if data_type not in valid_types:
                raise ValueError(f"Invalid data_type '{data_type}'. Must be one of: {', '.join(valid_types)}")
            
            # Validate value can be parsed
            if value is not None:
                self._validate_value(value, data_type)
            
            # Encrypt sensitive values (API keys, passwords)
            is_sensitive = self._is_sensitive_key(key)
            stored_value = encrypt_value(value) if (is_sensitive and value) else value
            
            setting = ApplicationSetting(
                key=key,
                value=stored_value,
                data_type=data_type,
                description=description,
                category=category,
                is_mutable=is_mutable,
                is_sensitive=is_sensitive
            )
            
            self.session.add(setting)
            await self.session.commit()
            await self.session.refresh(setting)
            
            # Invalidate cache after creation
            await self._invalidate_cache()
            
            return setting
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Setting '{key}' already exists")
            raise ValueError(f"Setting with key '{key}' already exists")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create setting '{key}': {e}", exc_info=True)
            raise
    
    async def update(self, key: str, value: str) -> ApplicationSetting:
        """
        Update setting value.
        
        Args:
            key: Setting key
            value: New value as string
            
        Returns:
            Updated ApplicationSetting
            
        Raises:
            ValueError: If setting not found, immutable, or value invalid
        """
        try:
            setting = await self.get_by_key(key)
            
            if not setting:
                raise ValueError(f"Setting '{key}' not found")
            
            if not setting.is_mutable:
                raise ValueError(f"Setting '{key}' is immutable and cannot be modified")
            
            # Validate new value matches data type
            self._validate_value(value, setting.data_type)
            
            # Encrypt if sensitive
            stored_value = encrypt_value(value) if setting.is_sensitive else value
            setting.value = stored_value
            await self.session.commit()
            await self.session.refresh(setting)
            
            # Invalidate cache after update
            await self._invalidate_cache(key=key)
            
            logger.info(f"Updated setting '{key}' to value '{value}'")
            return setting
            
        except ValueError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update setting '{key}': {e}", exc_info=True)
            raise
    
    async def update_bulk(self, updates: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Update multiple settings in bulk.
        
        Args:
            updates: List of dicts with 'key' and 'value'
            
        Returns:
            Dict with success count and errors
        """
        success_count = 0
        errors = []
        
        for item in updates:
            key = item.get("key")
            value = item.get("value")
            
            if not key or value is None:
                errors.append({"key": key, "error": "Missing key or value"})
                continue
            
            try:
                await self.update(key, value)
                success_count += 1
            except Exception as e:
                errors.append({"key": key, "error": str(e)})
                logger.warning(f"Failed to update setting '{key}': {e}")
        
        # Invalidate cache after bulk updates (even if some failed)
        if success_count > 0:
            await self._invalidate_cache()
        
        logger.info(f"Bulk update completed: {success_count} success, {len(errors)} errors")
        
        return {
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors
        }
    
    async def delete(self, key: str) -> bool:
        """
        Delete a setting.
        
        Args:
            key: Setting key
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            ValueError: If setting is immutable
        """
        try:
            setting = await self.get_by_key(key)
            
            if not setting:
                logger.warning(f"Setting '{key}' not found for deletion")
                return False
            
            if not setting.is_mutable:
                raise ValueError(f"Setting '{key}' is immutable and cannot be deleted")
            
            await self.session.delete(setting)
            await self.session.commit()
            
            # Invalidate cache after deletion
            await self._invalidate_cache(key=key)
            
            logger.info(f"Deleted setting '{key}'")
            return True
            
        except ValueError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete setting '{key}': {e}", exc_info=True)
            raise
    
    async def get_categories(self) -> List[str]:
        """
        Get list of all unique categories.
        
        Returns:
            List of category names
        """
        try:
            stmt = select(ApplicationSetting.category).distinct().where(
                ApplicationSetting.category.isnot(None)
            )
            result = await self.session.execute(stmt)
            categories = [row[0] for row in result.all()]
            
            logger.debug(f"Retrieved {len(categories)} categories")
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Failed to get categories: {e}", exc_info=True)
            raise
    
    def _parse_value(self, value: str, data_type: str) -> Any:
        """Parse string value to appropriate Python type."""
        try:
            if data_type == "integer":
                return int(value)
            elif data_type == "float":
                return float(value)
            elif data_type == "boolean":
                return value.lower() in ("true", "1", "yes", "on")
            elif data_type == "json":
                return json.loads(value)
            else:  # string
                return value
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse value '{value}' as {data_type}: {e}")
            return value  # Return as-is if parsing fails
    
    def _validate_value(self, value: str, data_type: str) -> None:
        """
        Validate that value can be parsed as the specified data type.
        
        Raises:
            ValueError: If value cannot be parsed
        """
        try:
            if data_type == "integer":
                int(value)
            elif data_type == "float":
                float(value)
            elif data_type == "boolean":
                if value.lower() not in ("true", "false", "1", "0", "yes", "no", "on", "off"):
                    raise ValueError(f"Invalid boolean value: {value}")
            elif data_type == "json":
                json.loads(value)
            # string always valid
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"Value '{value}' is not valid {data_type}: {str(e)}")
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a setting key contains sensitive data (API keys, passwords)."""
        sensitive_keywords = [
            "api_key", "api_token", "password", "secret",
            "private_key", "auth_token", "access_token"
        ]
        return any(keyword in key.lower() for keyword in sensitive_keywords)
    
    async def _invalidate_cache(self, key: Optional[str] = None) -> None:
        """
        Invalidate setting cache after updates.
        
        Updates both:
        1. In-memory cache (used by Pydantic config classes)
        2. Redis cache (persisted across restarts)
        
        Args:
            key: Specific setting key to invalidate, or None to reload all
        """
        try:
            from app.core.settings_cache import load_settings_into_memory
            from app.core.cache import get_cache
            
            # Reload all settings into memory cache
            result = await self.session.execute(select(ApplicationSetting))
            settings = result.scalars().all()
            settings_dict = {setting.key: setting.value for setting in settings}
            load_settings_into_memory(settings_dict)
            
            # Update Redis cache
            cache = get_cache()
            if key:
                # Update specific key
                cache_key = f"app_setting:{key}"
                if key in settings_dict:
                    await cache.set(cache_key, settings_dict[key], ttl=None)
                else:
                    await cache.delete(cache_key)
                logger.debug(f"Invalidated cache for setting '{key}'")
            else:
                # Update all keys
                for k, v in settings_dict.items():
                    cache_key = f"app_setting:{k}"
                    await cache.set(cache_key, v, ttl=None)
                logger.debug("Invalidated all settings cache")
            
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")

