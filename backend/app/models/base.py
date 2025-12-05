"""
Base model configuration for SQLAlchemy ORM.

This module provides the declarative base and utilities for all SQLAlchemy models.
"""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    
    # Add common timestamp columns to all models
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
