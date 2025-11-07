"""
Base model configuration for SQLAlchemy ORM.

This module provides the declarative base and utilities for all SQLAlchemy models.
"""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime
from datetime import datetime


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    
    # Add common timestamp columns to all models
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
