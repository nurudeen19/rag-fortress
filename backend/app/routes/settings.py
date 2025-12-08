"""Application settings API routes."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import require_role
from app.models.user import User
from app.utils.demo_mode import prevent_in_demo_mode
from app.schemas.settings import (
    SettingResponse,
    SettingCreateRequest,
    SettingUpdateRequest,
    SettingBulkUpdateRequest,
    SettingBulkUpdateResponse
)
from app.handlers.settings import (
    handle_get_all_settings,
    handle_get_setting,
    handle_create_setting,
    handle_update_setting,
    handle_update_settings_bulk,
    handle_get_categories
)


router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("/", response_model=List[SettingResponse])
async def get_all_settings(
    category: Optional[str] = Query(None, description="Filter by category"),
    admin_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all application settings.
    
    Optionally filter by category.
    
    **Requires:** Admin role
    
    **Returns:**
    - List of all settings with their current values
    """
    settings = await handle_get_all_settings(session, category=category)
    return settings


@router.get("/categories", response_model=List[str])
async def get_categories(
    admin_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all setting categories.
    
    **Requires:** Admin role
    
    **Returns:**
    - List of unique category names
    """
    categories = await handle_get_categories(session)
    return categories


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    admin_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific setting by key.
    
    **Requires:** Admin role
    
    **Returns:**
    - Setting details including value, type, and description
    """
    setting = await handle_get_setting(key, session)
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )
    
    return setting


@router.put("/{key}", response_model=SettingResponse)
@prevent_in_demo_mode("Update setting")
async def update_setting(
    key: str,
    request: SettingUpdateRequest,
    admin_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    Update a setting value.
    
    Only mutable settings can be updated.
    Value must match the setting's data type.
    
    **Requires:** Admin role
    
    **Returns:**
    - Updated setting details
    """
    try:
        setting = await handle_update_setting(key, request.value, session)
        return setting
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update setting: {str(e)}"
        )


@router.post("/", response_model=SettingResponse)
@prevent_in_demo_mode("Create setting")
async def create_setting(
    request: SettingCreateRequest,
    admin_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new setting.
    
    Sensitive settings (API keys, passwords, secrets) are automatically encrypted.
    Creates the setting and invalidates cache.
    
    **Requires:** Admin role
    
    **Returns:**
    - Created setting details
    """
    try:
        setting = await handle_create_setting(request, session)
        return setting
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create setting: {str(e)}"
        )


@router.put("/", response_model=SettingBulkUpdateResponse)
@prevent_in_demo_mode("Bulk update settings")
async def update_settings_bulk(
    request: SettingBulkUpdateRequest,
    admin_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session)
):
    """
    Update multiple settings in a single request.
    
    Continues processing even if individual updates fail.
    Returns summary of successes and errors.
    
    **Requires:** Admin role
    
    **Returns:**
    - success_count: Number of successfully updated settings
    - error_count: Number of failed updates
    - errors: List of errors with details
    """
    updates = [{"key": item.key, "value": item.value} for item in request.updates]
    result = await handle_update_settings_bulk(updates, session)
    return result

