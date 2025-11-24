"""
Activity Log Pydantic schemas for request/response validation.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SeverityEnum(str, Enum):
    """Activity log severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ClearanceLevelEnum(str, Enum):
    """Security clearance levels."""
    GENERAL = "GENERAL"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL = "CONFIDENTIAL"
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL"


class ActivityLogResponse(BaseModel):
    """Activity log entry response schema."""
    
    id: int
    user_id: int
    user_name: str
    user_department: Optional[str] = None
    incident_type: str
    severity: SeverityEnum
    description: str
    details: Optional[str] = None
    user_clearance_level: Optional[ClearanceLevelEnum] = None
    required_clearance_level: Optional[ClearanceLevelEnum] = None
    access_granted: Optional[bool] = None
    user_query: Optional[str] = None
    threat_type: Optional[str] = None
    conversation_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ActivityLogsListResponse(BaseModel):
    """Paginated activity logs response."""
    
    success: bool = True
    logs: List[ActivityLogResponse]
    total: int = Field(..., description="Total count of logs matching filters")
    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Current pagination offset")
    has_more: bool = Field(..., description="Whether more results are available")
    
    class Config:
        from_attributes = True


class IncidentTypeInfo(BaseModel):
    """Incident type information."""
    
    value: str
    name: str
    description: str


class IncidentTypesResponse(BaseModel):
    """Available incident types response."""
    
    success: bool = True
    incident_types: List[IncidentTypeInfo]
