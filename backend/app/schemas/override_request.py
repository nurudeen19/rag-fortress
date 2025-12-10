"""Schemas for permission override requests."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class OverrideRequestCreate(BaseModel):
    """Request to create a permission override."""
    
    override_type: str = Field(
        ...,
        description="Type of override: 'org_wide' or 'department'"
    )
    requested_permission_level: int = Field(
        ...,
        ge=1,
        le=4,
        description="Requested permission level (1=GENERAL, 2=CONFIDENTIAL, 3=HIGHLY_CONFIDENTIAL, 4=TOP_SECRET)"
    )
    reason: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="Business justification for the request"
    )
    requested_duration_hours: Optional[int] = Field(
        None,
        ge=1,
        le=8760,  # Max 1 year (365 days)
        description="How long access is needed in hours (for preset durations)"
    )
    custom_duration_days: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Custom duration in days for longer-term access (e.g., project duration)"
    )
    department_id: Optional[int] = Field(
        None,
        description="Required for department-level requests"
    )
    trigger_query: Optional[str] = Field(
        None,
        description="Query that triggered this request"
    )
    trigger_file_id: Optional[int] = Field(
        None,
        description="File that couldn't be accessed"
    )
    
    @validator("override_type")
    def validate_override_type(cls, v):
        if v not in ["org_wide", "department"]:
            raise ValueError("override_type must be 'org_wide' or 'department'")
        return v
    
    @validator("requested_duration_hours", "custom_duration_days", pre=True, always=True)
    def validate_duration(cls, v, values):
        """Ensure either requested_duration_hours or custom_duration_days is provided."""
        # Get the other duration field from values
        if "requested_duration_hours" in values and "custom_duration_days" in values:
            has_preset = values.get("requested_duration_hours") is not None
            has_custom = values.get("custom_duration_days") is not None
            if not has_preset and not has_custom:
                raise ValueError("Either requested_duration_hours or custom_duration_days must be provided")
        return v
    
    @validator("department_id")
    def validate_department_for_dept_override(cls, v, values):
        if "override_type" in values and values["override_type"] == "department":
            if not v:
                raise ValueError("department_id is required for department-level requests")
        return v


class OverrideApprovalRequest(BaseModel):
    """Request to approve an override."""
    
    approval_notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional notes from approver"
    )


class OverrideDenialRequest(BaseModel):
    """Request to deny an override."""
    
    denial_reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for denial"
    )


class OverrideRequestResponse(BaseModel):
    """Response with override request details."""
    
    id: int
    user_id: int
    override_type: str
    department_id: Optional[int]
    override_permission_level: int
    reason: str
    valid_from: datetime
    valid_until: datetime
    created_by_id: int
    status: str
    is_active: bool
    approver_id: Optional[int]
    approval_notes: Optional[str]
    decided_at: Optional[datetime]
    trigger_query: Optional[str]
    trigger_file_id: Optional[int]
    auto_escalated: bool
    escalated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Related data
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    approver_name: Optional[str] = None
    department_name: Optional[str] = None
    
    class Config:
        orm_mode = True
        from_attributes = True
    
    @classmethod
    def from_orm(cls, obj):
        """Create response from ORM object with related data."""
        data = {
            "id": obj.id,
            "user_id": obj.user_id,
            "override_type": obj.override_type,
            "department_id": obj.department_id,
            "override_permission_level": obj.override_permission_level,
            "reason": obj.reason,
            "valid_from": obj.valid_from,
            "valid_until": obj.valid_until,
            "created_by_id": obj.created_by_id,
            "status": obj.status,
            "is_active": obj.is_active,
            "approver_id": obj.approver_id,
            "approval_notes": obj.approval_notes,
            "decided_at": obj.decided_at,
            "trigger_query": obj.trigger_query,
            "trigger_file_id": obj.trigger_file_id,
            "auto_escalated": obj.auto_escalated,
            "escalated_at": obj.escalated_at,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        
        # Add related user info if available
        if hasattr(obj, "user") and obj.user:
            data["user_name"] = obj.user.name
            data["user_email"] = obj.user.email
        
        # Add approver info if available
        if hasattr(obj, "approver") and obj.approver:
            data["approver_name"] = obj.approver.name
        
        # Add department info if available
        if hasattr(obj, "department") and obj.department:
            data["department_name"] = obj.department.name
        
        return cls(**data)


class OverrideRequestListResponse(BaseModel):
    """Response with list of override requests."""
    
    requests: List[OverrideRequestResponse]
    total: int


class SuccessResponse(BaseModel):
    """Generic success response."""
    
    success: bool
    message: str
