"""
Department request handlers for HTTP endpoints.

Handles business logic for department management operations:
- CRUD operations
- Manager assignment
- User assignment
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin.department_service import DepartmentService

logger = logging.getLogger(__name__)


async def handle_create_department(
    name: str,
    code: str,
    description: str = None,
    manager_id: int = None,
    session: AsyncSession = None
) -> dict:
    """
    Handle create department request.
    
    Args:
        name: Department name
        code: Department code
        description: Department description
        manager_id: User ID to set as manager
        session: Database session
        
    Returns:
        Dict with created department or error
    """
    try:
        logger.info(f"Creating department: {name} ({code})")
        
        service = DepartmentService(session)
        department, error = await service.create_department(
            name=name,
            code=code,
            description=description,
            manager_id=manager_id
        )
        
        if error:
            logger.warning(f"Failed to create department: {error}")
            return {
                "success": False,
                "error": error,
                "department": None
            }
        
        return {
            "success": True,
            "department": department
        }
        
    except Exception as e:
        logger.error(f"Error handling create department request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to create department",
            "department": None
        }


async def handle_get_department(
    department_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle get department request.
    
    Args:
        department_id: ID of department
        session: Database session
        
    Returns:
        Dict with department or error
    """
    try:
        logger.info(f"Getting department {department_id}")
        
        service = DepartmentService(session)
        department, error = await service.get_department(department_id)
        
        if error:
            logger.warning(f"Failed to get department: {error}")
            return {
                "success": False,
                "error": error,
                "department": None
            }
        
        return {
            "success": True,
            "department": department
        }
        
    except Exception as e:
        logger.error(f"Error handling get department request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to retrieve department",
            "department": None
        }


async def handle_list_departments(
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = None
) -> dict:
    """
    Handle list departments request.
    
    Args:
        active_only: Only return active departments
        skip: Number to skip
        limit: Max limit
        session: Database session
        
    Returns:
        Dict with departments list or error
    """
    try:
        logger.info(f"Listing departments (active_only={active_only})")
        
        service = DepartmentService(session)
        departments, error = await service.list_departments(
            active_only=active_only,
            skip=skip,
            limit=limit
        )
        
        if error:
            logger.warning(f"Failed to list departments: {error}")
            return {
                "success": False,
                "error": error,
                "departments": []
            }
        
        return {
            "success": True,
            "departments": departments,
            "total": len(departments)
        }
        
    except Exception as e:
        logger.error(f"Error handling list departments request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to list departments",
            "departments": []
        }


async def handle_update_department(
    department_id: int,
    name: str = None,
    code: str = None,
    description: str = None,
    is_active: bool = None,
    session: AsyncSession = None
) -> dict:
    """
    Handle update department request.
    
    Args:
        department_id: ID of department
        name: New name
        code: New code
        description: New description
        is_active: Active status
        session: Database session
        
    Returns:
        Dict with updated department or error
    """
    try:
        logger.info(f"Updating department {department_id}")
        
        service = DepartmentService(session)
        department, error = await service.update_department(
            department_id,
            name=name,
            code=code,
            description=description,
            is_active=is_active
        )
        
        if error:
            logger.warning(f"Failed to update department: {error}")
            return {
                "success": False,
                "error": error,
                "department": None
            }
        
        return {
            "success": True,
            "department": department
        }
        
    except Exception as e:
        logger.error(f"Error handling update department request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to update department",
            "department": None
        }


async def handle_delete_department(
    department_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle delete department request.
    
    Args:
        department_id: ID of department
        session: Database session
        
    Returns:
        Dict with success or error
    """
    try:
        logger.info(f"Deleting department {department_id}")
        
        service = DepartmentService(session)
        success, error = await service.delete_department(department_id)
        
        if not success:
            logger.warning(f"Failed to delete department: {error}")
            return {
                "success": False,
                "error": error
            }
        
        return {
            "success": True,
            "message": "Department deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error handling delete department request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to delete department"
        }


async def handle_set_manager(
    department_id: int,
    manager_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle set department manager request.
    
    Args:
        department_id: ID of department
        manager_id: User ID of manager
        session: Database session
        
    Returns:
        Dict with updated department or error
    """
    try:
        logger.info(f"Setting manager {manager_id} for department {department_id}")
        
        service = DepartmentService(session)
        department, error = await service.set_manager(department_id, manager_id)
        
        if error:
            logger.warning(f"Failed to set manager: {error}")
            return {
                "success": False,
                "error": error,
                "department": None
            }
        
        return {
            "success": True,
            "department": department
        }
        
    except Exception as e:
        logger.error(f"Error handling set manager request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to set manager",
            "department": None
        }


async def handle_remove_manager(
    department_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle remove department manager request.
    
    Args:
        department_id: ID of department
        session: Database session
        
    Returns:
        Dict with updated department or error
    """
    try:
        logger.info(f"Removing manager from department {department_id}")
        
        service = DepartmentService(session)
        department, error = await service.remove_manager(department_id)
        
        if error:
            logger.warning(f"Failed to remove manager: {error}")
            return {
                "success": False,
                "error": error,
                "department": None
            }
        
        return {
            "success": True,
            "department": department
        }
        
    except Exception as e:
        logger.error(f"Error handling remove manager request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to remove manager",
            "department": None
        }


async def handle_assign_user(
    user_id: int,
    department_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle assign user to department request.
    
    Args:
        user_id: ID of user
        department_id: ID of department
        session: Database session
        
    Returns:
        Dict with success or error
    """
    try:
        logger.info(f"Assigning user {user_id} to department {department_id}")
        
        service = DepartmentService(session)
        success, error = await service.assign_user_to_department(user_id, department_id)
        
        if not success:
            logger.warning(f"Failed to assign user: {error}")
            return {
                "success": False,
                "error": error
            }
        
        return {
            "success": True,
            "message": "User assigned to department"
        }
        
    except Exception as e:
        logger.error(f"Error handling assign user request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to assign user to department"
        }


async def handle_remove_user(
    user_id: int,
    session: AsyncSession
) -> dict:
    """
    Handle remove user from department request.
    
    Args:
        user_id: ID of user
        session: Database session
        
    Returns:
        Dict with success or error
    """
    try:
        logger.info(f"Removing user {user_id} from department")
        
        service = DepartmentService(session)
        success, error = await service.remove_user_from_department(user_id)
        
        if not success:
            logger.warning(f"Failed to remove user: {error}")
            return {
                "success": False,
                "error": error
            }
        
        return {
            "success": True,
            "message": "User removed from department"
        }
        
    except Exception as e:
        logger.error(f"Error handling remove user request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to remove user from department"
        }


async def handle_get_department_users(
    department_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = None
) -> dict:
    """
    Handle get department users request.
    
    Args:
        department_id: ID of department
        skip: Number to skip
        limit: Max limit
        session: Database session
        
    Returns:
        Dict with users list or error
    """
    try:
        logger.info(f"Getting users for department {department_id}")
        
        service = DepartmentService(session)
        users, error = await service.get_department_users(
            department_id,
            skip=skip,
            limit=limit
        )
        
        if error:
            logger.warning(f"Failed to get department users: {error}")
            return {
                "success": False,
                "error": error,
                "users": []
            }
        
        return {
            "success": True,
            "users": users,
            "total": len(users)
        }
        
    except Exception as e:
        logger.error(f"Error handling get department users request: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": "Failed to retrieve department users",
            "users": []
        }
