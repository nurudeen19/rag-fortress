"""
Department management routes.

Endpoints:
- GET    /api/v1/admin/departments - List all departments
- POST   /api/v1/admin/departments - Create department
- GET    /api/v1/admin/departments/{id} - Get department
- PUT    /api/v1/admin/departments/{id} - Update department
- DELETE /api/v1/admin/departments/{id} - Delete department
- POST   /api/v1/admin/departments/{id}/manager - Set manager
- DELETE /api/v1/admin/departments/{id}/manager - Remove manager
- POST   /api/v1/admin/departments/{id}/users/{user_id} - Assign user
- DELETE /api/v1/admin/departments/{id}/users/{user_id} - Remove user
- GET    /api/v1/admin/departments/{id}/users - Get department users
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.core import get_logger
from app.schemas.department import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    SetManagerRequest,
    DepartmentResponse,
    DepartmentsListResponse,
)
from app.handlers.departments import (
    handle_create_department,
    handle_get_department,
    handle_list_departments,
    handle_update_department,
    handle_delete_department,
    handle_set_manager,
    handle_remove_manager,
    handle_assign_user,
    handle_remove_user,
    handle_get_department_users,
)


router = APIRouter(prefix="/departments", tags=["departments"])
logger = get_logger(__name__)


@router.get("", response_model=DepartmentsListResponse)
async def list_departments(
    active_only: bool = Query(True, description="Only return active departments"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """List all departments (admin only)."""
    # TODO: Add permission check
    result = await handle_list_departments(
        active_only=active_only,
        skip=skip,
        limit=limit,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to list departments")
        )
    
    return DepartmentsListResponse(
        departments=result["departments"],
        total=result.get("total", 0)
    )


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    request: DepartmentCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Create a new department (admin only)."""
    # TODO: Add permission check
    result = await handle_create_department(
        name=request.name,
        code=request.code,
        description=request.description,
        manager_id=request.manager_id,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to create department")
        )
    
    dept = result["department"]
    return DepartmentResponse(
        id=dept["id"],
        name=dept["name"],
        code=dept["code"],
        description=dept["description"],
        manager=dept.get("manager"),
        manager_id=dept["manager_id"],
        is_active=dept["is_active"],
        created_at=dept["created_at"],
        updated_at=dept["updated_at"],
    )


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get department by ID (admin only)."""
    # TODO: Add permission check
    result = await handle_get_department(
        department_id=department_id,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Department not found")
        )
    
    dept = result["department"]
    return DepartmentResponse(
        id=dept["id"],
        name=dept["name"],
        code=dept["code"],
        description=dept["description"],
        manager=dept.get("manager"),
        manager_id=dept["manager_id"],
        is_active=dept["is_active"],
        created_at=dept["created_at"],
        updated_at=dept["updated_at"],
    )


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    request: DepartmentUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Update department (admin only)."""
    # TODO: Add permission check
    result = await handle_update_department(
        department_id=department_id,
        name=request.name,
        code=request.code,
        description=request.description,
        is_active=request.is_active,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to update department")
        )
    
    dept = result["department"]
    return DepartmentResponse(
        id=dept["id"],
        name=dept["name"],
        code=dept["code"],
        description=dept["description"],
        manager=dept.get("manager"),
        manager_id=dept["manager_id"],
        is_active=dept["is_active"],
        created_at=dept["created_at"],
        updated_at=dept["updated_at"],
    )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete department (admin only)."""
    # TODO: Add permission check
    result = await handle_delete_department(
        department_id=department_id,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to delete department")
        )


@router.post("/{department_id}/manager", response_model=DepartmentResponse)
async def set_manager(
    department_id: int,
    request: SetManagerRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Set manager for department (admin only)."""
    # TODO: Add permission check
    result = await handle_set_manager(
        department_id=department_id,
        manager_id=request.manager_id,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to set manager")
        )
    
    dept = result["department"]
    return DepartmentResponse(
        id=dept["id"],
        name=dept["name"],
        code=dept["code"],
        description=dept["description"],
        manager=dept.get("manager"),
        manager_id=dept["manager_id"],
        is_active=dept["is_active"],
        created_at=dept["created_at"],
        updated_at=dept["updated_at"],
    )


@router.delete("/{department_id}/manager", response_model=DepartmentResponse)
async def remove_manager(
    department_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Remove manager from department (admin only)."""
    # TODO: Add permission check
    result = await handle_remove_manager(
        department_id=department_id,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to remove manager")
        )
    
    dept = result["department"]
    return DepartmentResponse(
        id=dept["id"],
        name=dept["name"],
        code=dept["code"],
        description=dept["description"],
        manager=dept.get("manager"),
        manager_id=dept["manager_id"],
        is_active=dept["is_active"],
        created_at=dept["created_at"],
        updated_at=dept["updated_at"],
    )


@router.post("/{department_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def assign_user_to_department(
    department_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Assign user to department (admin only)."""
    # TODO: Add permission check
    result = await handle_assign_user(
        user_id=user_id,
        department_id=department_id,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to assign user")
        )


@router.delete("/{department_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_department(
    department_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Remove user from department (admin only)."""
    # TODO: Add permission check
    result = await handle_remove_user(
        user_id=user_id,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to remove user")
        )


@router.get("/{department_id}/users")
async def get_department_users(
    department_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get all users in a department (admin only)."""
    # TODO: Add permission check
    result = await handle_get_department_users(
        department_id=department_id,
        skip=skip,
        limit=limit,
        session=session
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to retrieve department users")
        )
    
    return {
        "users": result["users"],
        "total": result.get("total", 0)
    }
