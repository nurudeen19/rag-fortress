"""
Pydantic schemas for error report API endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.error_report import ErrorReportStatus, ErrorReportCategory


class ErrorReportCreateRequest(BaseModel):
    """Request to create a new error report."""
    
    title: str = Field(..., min_length=5, max_length=255, description="Brief title of the error")
    description: str = Field(..., min_length=10, max_length=5000, description="Detailed description of what happened")
    category: ErrorReportCategory = Field(default=ErrorReportCategory.OTHER, description="Category of the error")
    conversation_id: Optional[str] = Field(None, description="ID of conversation where error occurred (optional)")


class ErrorReportResponse(BaseModel):
    """Response when error report is created/retrieved."""
    
    id: int
    user_id: int
    title: str
    description: str
    category: ErrorReportCategory
    status: ErrorReportStatus
    image_filename: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ErrorReportListResponse(BaseModel):
    """List of error reports for user."""
    
    reports: list[ErrorReportResponse]
    total: int
    
    model_config = ConfigDict(from_attributes=True)


class ErrorReportDetailResponse(BaseModel):
    """Detailed error report for admin view."""
    
    id: int
    user_id: int
    user_name: Optional[str]  # User's name/email for context
    title: str
    description: str
    category: ErrorReportCategory
    status: ErrorReportStatus
    conversation_id: Optional[str]
    image_filename: Optional[str]
    user_agent: Optional[str]
    admin_notes: Optional[str]
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class ErrorReportAdminUpdateRequest(BaseModel):
    """Admin request to update error report status and notes."""
    
    status: Optional[ErrorReportStatus] = Field(None, description="New status for the report")
    admin_notes: Optional[str] = Field(None, max_length=5000, description="Admin's investigation notes")
    assigned_to: Optional[int] = Field(None, description="User ID to assign to")


class ErrorReportListAdminResponse(BaseModel):
    """List of all error reports for admin."""
    
    reports: list[ErrorReportDetailResponse]
    total: int
    open_count: int
    investigating_count: int
    resolved_count: int
    
    model_config = ConfigDict(from_attributes=True)
