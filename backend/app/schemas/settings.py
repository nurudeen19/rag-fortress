"""Application settings API schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field


class SettingResponse(BaseModel):
    """Setting response schema."""
    id: int
    key: str
    value: Optional[str] = None
    data_type: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_mutable: bool
    is_sensitive: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SettingCreateRequest(BaseModel):
    """Setting creation request schema."""
    key: str = Field(..., description="Unique setting key (lowercase_with_underscores)")
    value: str = Field(..., description="Setting value")
    data_type: str = Field("string", description="Data type: string, integer, boolean, json, float")
    description: Optional[str] = Field(None, description="Human-readable description")
    category: Optional[str] = Field(None, description="Category for grouping")
    is_mutable: bool = Field(True, description="Whether setting can be modified")


class SettingUpdateRequest(BaseModel):
    """Setting update request schema."""
    value: Optional[str] = Field(None, description="New setting value (can be null to clear)")


class SettingBulkUpdateItem(BaseModel):
    """Single item in bulk update request."""
    key: str = Field(..., description="Setting key")
    value: Optional[str] = Field(None, description="New setting value (can be null to clear)")


class SettingBulkUpdateRequest(BaseModel):
    """Bulk setting update request schema."""
    updates: List[SettingBulkUpdateItem] = Field(..., description="List of settings to update")


class SettingBulkUpdateResponse(BaseModel):
    """Bulk update response schema."""
    success_count: int
    error_count: int
    errors: List[dict] = []

