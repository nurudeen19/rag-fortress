"""
FileUpload schemas for request/response validation.
Used for frontend form submissions and API responses.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, validator


class SecurityLevelEnum(str, Enum):
    """Security classification levels."""
    GENERAL = "GENERAL"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL = "CONFIDENTIAL"
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL"


class FileUploadCreate(BaseModel):
    """Schema for creating file upload (from frontend form)."""
    
    file_name: str = Field(..., min_length=1, description="Original filename")
    file_type: str = Field(..., min_length=1, description="File extension (pdf, txt, csv, etc)")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    
    uploaded_by_id: int = Field(..., gt=0, description="User ID of uploader")
    
    # File metadata
    file_purpose: Optional[str] = Field(None, description="Why this file is being uploaded")
    field_selection: Optional[List[str]] = Field(
        None,
        description="Specific fields to extract from structured data"
    )
    
    # Department/organization
    department_id: Optional[int] = Field(None, description="Department ID if applicable")
    
    # Security
    security_level: SecurityLevelEnum = Field(
        default=SecurityLevelEnum.GENERAL,
        description="Security classification"
    )
    is_department_only: bool = Field(
        default=False,
        description="If True, only department members can access"
    )
    
    @validator('file_type')
    def validate_file_type(cls, v):
        """Validate file type is a supported format."""
        supported = {'pdf', 'txt', 'md', 'csv', 'json', 'xlsx', 'xls', 'docx', 'doc'}
        if v.lower() not in supported:
            raise ValueError(f"Unsupported file type: {v}. Supported: {supported}")
        return v.lower()
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size is reasonable."""
        max_size = 100 * 1024 * 1024  # 100MB
        if v > max_size:
            raise ValueError(f"File too large: {v} bytes (max: {max_size})")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "company_policy.pdf",
                "file_type": "pdf",
                "file_size": 2048576,
                "uploaded_by_id": 1,
                "file_purpose": "Company handbook for Q4",
                "field_selection": None,
                "department_id": 3,
                "security_level": "RESTRICTED",
                "is_department_only": True,
            }
        }


class FileUploadResponse(BaseModel):
    """Response schema for file upload."""
    
    id: int
    upload_token: str
    file_name: str
    file_type: str
    file_size: int
    
    status: str
    security_level: str
    is_department_only: bool
    department_id: Optional[int]
    
    uploaded_by_id: Optional[int] = None
    file_purpose: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    uploader_info: Optional[dict] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class FileUploadDetailResponse(FileUploadResponse):
    """Detailed response with additional fields."""
    
    is_processed: bool
    processing_error: Optional[str]
    retry_count: int
    
    chunks_created: Optional[int]
    processing_time_ms: Optional[int]


class FileUploadApproveRequest(BaseModel):
    """Request to approve file upload."""
    
    approved_by_id: int = Field(..., gt=0, description="User ID of approver")
    reason: Optional[str] = Field(None, description="Approval reason/notes")


class FileUploadRejectRequest(BaseModel):
    """Request to reject file upload."""
    
    rejected_by_id: int = Field(..., gt=0, description="User ID of rejector")
    reason: str = Field(..., min_length=1, description="Rejection reason")


class FileUploadListResponse(BaseModel):
    """Response for listing file uploads."""
    
    total: int = Field(..., description="Total number of files")
    items: List[FileUploadResponse]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class FileUploadListWithCountsResponse(BaseModel):
    """Response for listing files with status counts."""
    
    counts: dict = Field(..., description="Count of files per status")
    total: int = Field(..., description="Total number of files in current filter")
    limit: int = Field(..., description="Pagination limit")
    offset: int = Field(..., description="Pagination offset")
    items: List[FileUploadResponse]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class FileUploadStatsResponse(BaseModel):
    """Response with file upload statistics."""
    
    total_files: int
    pending_approval: int
    approved: int
    processed: int
    failed: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_files": 150,
                "pending_approval": 5,
                "approved": 45,
                "processed": 95,
                "failed": 5,
            }
        }
