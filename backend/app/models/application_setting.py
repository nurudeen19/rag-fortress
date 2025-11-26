"""
Application settings model for storing configuration in the database.

This model stores application-level settings that can be modified at runtime
and persisted to the database.
"""
from sqlalchemy import Column, String, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ApplicationSetting(Base):
    """Application settings stored in the database."""
    
    __tablename__ = "application_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Setting key (e.g., "max_document_size", "ingestion_batch_size")
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Setting value as string (nullable - users provide values via UI)
    value: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Data type of the setting (string, integer, boolean, json)
    data_type: Mapped[str] = mapped_column(String(50), default="string", nullable=False)
    
    # Human-readable description
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Whether this setting can be modified through the API
    is_mutable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Whether this setting contains sensitive data (API keys, passwords) - will be encrypted
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Category for grouping related settings
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    
    def __repr__(self) -> str:
        return f"<ApplicationSetting(key='{self.key}', value='{self.value}', data_type='{self.data_type}')>"
