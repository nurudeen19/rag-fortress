"""Application settings API schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field


class SettingResponse(BaseModel):
    """Setting response schema."""
    id: int
    key: str
    value: str
    data_type: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_mutable: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SettingUpdateRequest(BaseModel):
    """Setting update request schema."""
    value: str = Field(..., description="New setting value")


class SettingBulkUpdateItem(BaseModel):
    """Single item in bulk update request."""
    key: str = Field(..., description="Setting key")
    value: str = Field(..., description="New setting value")


class SettingBulkUpdateRequest(BaseModel):
    """Bulk setting update request schema."""
    updates: List[SettingBulkUpdateItem] = Field(..., description="List of settings to update")


class SettingBulkUpdateResponse(BaseModel):
    """Bulk update response schema."""
    success_count: int
    error_count: int
    errors: List[dict] = []

