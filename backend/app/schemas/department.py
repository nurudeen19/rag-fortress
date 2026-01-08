"""Department management schemas for request/response validation."""

from typing import Optional, List
from pydantic import BaseModel, Field


class UserShortResponse(BaseModel):
    """Short user info for manager display."""
    
    id: int
    username: str
    email: str
    full_name: str


class DepartmentResponse(BaseModel):
    """Response schema for department data."""
    
    id: int
    name: str
    code: str
    description: Optional[str] = None
    manager: Optional[UserShortResponse] = None
    manager_id: Optional[int] = None
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DepartmentsListResponse(BaseModel):
    """Response schema for departments list."""
    
    departments: List[DepartmentResponse] = Field(default_factory=list)
    total: int


class DepartmentCreateRequest(BaseModel):
    """Schema for creating a department."""
    
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    manager_id: Optional[int] = Field(None, gt=0)


class DepartmentUpdateRequest(BaseModel):
    """Schema for updating a department."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class SetManagerRequest(BaseModel):
    """Schema for setting a department manager."""
    
    manager_id: int = Field(..., gt=0)


class AssignUserRequest(BaseModel):
    """Schema for assigning user to department."""
    
    user_id: int = Field(..., gt=0)


class DepartmentUserResponse(BaseModel):
    """Response schema for user in department."""
    
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
