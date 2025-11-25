"""
Settings Service - Business logic for application settings operations.
"""

import json
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from app.core import get_logger
from app.models.application_setting import ApplicationSetting


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
            
            logger.info(f"Retrieved {len(settings)} settings" + (f" in category '{category}'" if category else ""))
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
        Get setting value parsed by data type.
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Parsed value or default
        """
        setting = await self.get_by_key(key)
        
        if not setting:
            return default
        
        return self._parse_value(setting.value, setting.data_type)
    
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
            self._validate_value(value, data_type)
            
            setting = ApplicationSetting(
                key=key,
                value=value,
                data_type=data_type,
                description=description,
                category=category,
                is_mutable=is_mutable
            )
            
            self.session.add(setting)
            await self.session.commit()
            await self.session.refresh(setting)
            
            logger.info(f"Created setting '{key}' in category '{category}'")
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
            
            setting.value = value
            await self.session.commit()
            await self.session.refresh(setting)
            
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

