"""
Department management service for CRUD operations and department-related actions.

Handles:
- Creating, reading, updating, deleting departments
- Setting and removing department managers
- Assigning and removing users from departments
"""

from typing import Optional, Tuple, Dict, List, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.models.user import User
from app.core import get_logger


logger = get_logger(__name__)


class DepartmentService:
    """Service for managing departments."""
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
    
    async def create_department(
        self,
        name: str,
        code: str,
        description: Optional[str] = None,
        manager_id: Optional[int] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Create a new department.
        
        Args:
            name: Department name
            code: Department unique code
            description: Department description
            manager_id: ID of user to set as manager (optional)
        
        Returns:
            Tuple of (department_data, error_message)
        """
        try:
            # Check if code already exists
            result = await self.session.execute(
                select(Department).where(Department.code == code)
            )
            if result.scalar_one_or_none():
                logger.warning(f"Department with code {code} already exists")
                return None, f"Department code '{code}' already exists"
            
            # Validate manager exists if provided
            manager = None
            if manager_id:
                manager_result = await self.session.execute(
                    select(User).where(User.id == manager_id)
                )
                manager = manager_result.scalar_one_or_none()
                if not manager:
                    logger.warning(f"Manager with ID {manager_id} not found")
                    return None, f"Manager with ID {manager_id} not found"
            
            # Create department
            department = Department(
                name=name,
                code=code,
                description=description,
                manager_id=manager_id
            )
            self.session.add(department)
            await self.session.flush()
            await self.session.commit()
            
            logger.info(f"Created department: {department.name} (code: {code})")
            
            return await self._format_department(department), None
            
        except Exception as e:
            logger.error(f"Error creating department: {str(e)}", exc_info=True)
            await self.session.rollback()
            return None, "Failed to create department"
    
    async def get_department(self, department_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get department by ID.
        
        Args:
            department_id: ID of the department
        
        Returns:
            Tuple of (department_data, error_message)
        """
        try:
            
            result = await self.session.execute(
                select(Department)
                .options(selectinload(Department.manager))
                .where(Department.id == department_id)
            )
            department = result.scalar_one_or_none()
            
            if not department:
                logger.warning(f"Department with ID {department_id} not found")
                return None, "Department not found"
            
            return await self._format_department(department), None
            
        except Exception as e:
            logger.error(f"Error retrieving department {department_id}: {str(e)}", exc_info=True)
            return None, "Failed to retrieve department"
    
    async def list_departments(
        self,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List all departments.
        
        Args:
            active_only: Only return active departments
            skip: Number of departments to skip
            limit: Maximum number of departments to return
        
        Returns:
            Tuple of (departments_list, error_message)
        """
        try:
            from sqlalchemy.orm import selectinload
            query = select(Department).options(selectinload(Department.manager))
            
            if active_only:
                query = query.where(Department.is_active.is_(True))
            
            query = query.offset(skip).limit(limit)
            
            result = await self.session.execute(query)
            departments = result.scalars().all()
            
            formatted = []
            for dept in departments:
                dept_data = await self._format_department(dept)
                formatted.append(dept_data)
            
            logger.info(f"Retrieved {len(departments)} departments")
            return formatted, None
            
        except Exception as e:
            logger.error(f"Error listing departments: {str(e)}", exc_info=True)
            return [], "Failed to retrieve departments"
    
    async def update_department(
        self,
        department_id: int,
        **kwargs
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Update department information.
        
        Updatable fields: name, code, description, is_active
        Manager is updated via set_manager method.
        
        Args:
            department_id: ID of the department
            **kwargs: Fields to update
        
        Returns:
            Tuple of (department_data, error_message)
        """
        try:
            from sqlalchemy.orm import selectinload
            result = await self.session.execute(
                select(Department)
                .options(selectinload(Department.manager))
                .where(Department.id == department_id)
            )
            department = result.scalar_one_or_none()
            
            if not department:
                logger.warning(f"Department with ID {department_id} not found")
                return None, "Department not found"
            
            # Allowed updatable fields
            updatable_fields = {"name", "code", "description", "is_active"}
            
            updates = {}
            for field in updatable_fields:
                if field in kwargs and kwargs[field] is not None:
                    value = kwargs[field]
                    # Validate non-empty strings
                    if isinstance(value, str):
                        value = value.strip()
                        if not value:
                            return None, f"{field.replace('_', ' ').title()} cannot be empty"
                    updates[field] = value
            
            if not updates:
                logger.warning(f"Department {department_id} update with no valid fields")
                return None, "No valid fields to update"
            
            for field, value in updates.items():
                setattr(department, field, value)
            
            await self.session.commit()
            logger.info(f"Updated department {department_id}: {list(updates.keys())}")
            
            return await self._format_department(department), None
            
        except Exception as e:
            logger.error(f"Error updating department {department_id}: {str(e)}", exc_info=True)
            await self.session.rollback()
            return None, "Failed to update department"
    
    async def delete_department(self, department_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a department (soft delete via is_active flag).
        
        Also removes manager assignment.
        
        Args:
            department_id: ID of the department
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            result = await self.session.execute(
                select(Department).where(Department.id == department_id)
            )
            department = result.scalar_one_or_none()
            
            if not department:
                logger.warning(f"Department with ID {department_id} not found")
                return False, "Department not found"
            
            # Check if users are assigned to this department
            users_result = await self.session.execute(
                select(User).where(User.department_id == department_id)
            )
            users = users_result.scalars().all()
            
            if users:
                logger.warning(f"Cannot delete department {department_id}: {len(users)} users assigned")
                return False, f"Cannot delete: {len(users)} users assigned to this department. Remove them first."
            
            # Soft delete
            department.is_active = False
            await self.session.commit()
            
            logger.info(f"Deleted department {department_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error deleting department {department_id}: {str(e)}", exc_info=True)
            await self.session.rollback()
            return False, "Failed to delete department"
    
    async def set_manager(
        self,
        department_id: int,
        manager_id: int
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Set or update the manager for a department.
        
        Args:
            department_id: ID of the department
            manager_id: ID of the user to set as manager
        
        Returns:
            Tuple of (department_data, error_message)
        """
        try:
            # Get department
            dept_result = await self.session.execute(
                select(Department).where(Department.id == department_id)
            )
            department = dept_result.scalar_one_or_none()
            
            if not department:
                logger.warning(f"Department with ID {department_id} not found")
                return None, "Department not found"
            
            # Get user to set as manager
            user_result = await self.session.execute(
                select(User).where(User.id == manager_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User with ID {manager_id} not found")
                return None, "User not found"
            
            # Set manager
            old_manager_id = department.manager_id
            department.manager_id = manager_id
            await self.session.commit()
            
            logger.info(f"Set manager for department {department_id}: {old_manager_id} -> {manager_id}")
            
            return await self._format_department(department), None
            
        except Exception as e:
            logger.error(f"Error setting manager for department {department_id}: {str(e)}", exc_info=True)
            await self.session.rollback()
            return None, "Failed to set manager"
    
    async def remove_manager(
        self,
        department_id: int
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Remove the manager from a department.
        
        Args:
            department_id: ID of the department
        
        Returns:
            Tuple of (department_data, error_message)
        """
        try:
            from sqlalchemy.orm import selectinload
            result = await self.session.execute(
                select(Department)
                .options(selectinload(Department.manager))
                .where(Department.id == department_id)
            )
            department = result.scalar_one_or_none()
            
            if not department:
                logger.warning(f"Department with ID {department_id} not found")
                return None, "Department not found"
            
            if not department.manager_id:
                logger.info(f"Department {department_id} has no manager to remove")
                return None, "Department has no manager"
            
            old_manager_id = department.manager_id
            department.manager_id = None
            await self.session.commit()
            
            logger.info(f"Removed manager from department {department_id}: {old_manager_id}")
            
            return await self._format_department(department), None
            
        except Exception as e:
            logger.error(f"Error removing manager from department {department_id}: {str(e)}", exc_info=True)
            await self.session.rollback()
            return None, "Failed to remove manager"
    
    async def assign_user_to_department(
        self,
        user_id: int,
        department_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Assign a user to a department.
        
        Args:
            user_id: ID of the user
            department_id: ID of the department
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get user
            user_result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                return False, "User not found"
            
            # Get department
            dept_result = await self.session.execute(
                select(Department).where(Department.id == department_id)
            )
            department = dept_result.scalar_one_or_none()
            
            if not department:
                logger.warning(f"Department with ID {department_id} not found")
                return False, "Department not found"
            
            old_dept_id = user.department_id
            user.department_id = department_id
            await self.session.commit()
            
            logger.info(f"Assigned user {user_id} to department {department_id} (was: {old_dept_id})")
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error assigning user {user_id} to department {department_id}: {str(e)}", exc_info=True)
            await self.session.rollback()
            return False, "Failed to assign user to department"
    
    async def remove_user_from_department(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Remove a user from their department (set department_id to None).
        
        Args:
            user_id: ID of the user
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            user_result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                return False, "User not found"
            
            if not user.department_id:
                logger.info(f"User {user_id} is not assigned to any department")
                return False, "User is not assigned to any department"
            
            old_dept_id = user.department_id
            user.department_id = None
            await self.session.commit()
            
            logger.info(f"Removed user {user_id} from department {old_dept_id}")
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error removing user {user_id} from department: {str(e)}", exc_info=True)
            await self.session.rollback()
            return False, "Failed to remove user from department"
    
    async def get_department_users(
        self,
        department_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get all users assigned to a department.
        
        Args:
            department_id: ID of the department
            skip: Number of users to skip
            limit: Maximum number of users to return
        
        Returns:
            Tuple of (users_list, error_message)
        """
        try:
            # Verify department exists
            dept_result = await self.session.execute(
                select(Department).where(Department.id == department_id)
            )
            if not dept_result.scalar_one_or_none():
                logger.warning(f"Department with ID {department_id} not found")
                return [], "Department not found"
            
            # Get users
            result = await self.session.execute(
                select(User)
                .where(User.department_id == department_id)
                .offset(skip)
                .limit(limit)
            )
            users = result.scalars().all()
            
            formatted = []
            for user in users:
                formatted.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                })
            
            logger.info(f"Retrieved {len(users)} users from department {department_id}")
            return formatted, None
            
        except Exception as e:
            logger.error(f"Error retrieving users for department {department_id}: {str(e)}", exc_info=True)
            return [], "Failed to retrieve department users"
    
    async def _format_department(self, department: Department) -> Dict[str, Any]:
        """
        Format department object for API response.
        
        Args:
            department: Department model instance
        
        Returns:
            Formatted department data
        """
        manager_info = None
        if department.manager_id and department.manager:
            manager_info = {
                "id": department.manager.id,
                "username": department.manager.username,
                "email": department.manager.email,
                "full_name": department.manager.full_name,
            }
        
        return {
            "id": department.id,
            "name": department.name,
            "code": department.code,
            "description": department.description,
            "manager": manager_info,
            "manager_id": department.manager_id,
            "is_active": department.is_active,
            "created_at": department.created_at.isoformat() if department.created_at else None,
            "updated_at": department.updated_at.isoformat() if department.updated_at else None,
        }
