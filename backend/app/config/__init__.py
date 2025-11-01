"""
Configuration module for RAG Fortress.

This module provides a modular configuration system with specialized settings
for different aspects of the application:
- AppSettings: General application configuration
- LLMSettings: LLM provider configuration
- EmbeddingSettings: Embedding provider configuration  
- VectorDBSettings: Vector database configuration
- DatabaseSettings: SQL database configuration (PostgreSQL, MySQL, SQLite)
- Settings: Main settings class that combines all modules
"""

from .settings import Settings, settings
from .app_settings import AppSettings
from .llm_settings import LLMSettings
from .embedding_settings import EmbeddingSettings
from .vectordb_settings import VectorDBSettings
from .database_settings import DatabaseSettings

__all__ = [
    "Settings",
    "settings",
    "AppSettings",
    "LLMSettings",
    "EmbeddingSettings",
    "VectorDBSettings",
    "DatabaseSettings",
]
