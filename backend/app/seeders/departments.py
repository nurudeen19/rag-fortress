"""Departments seeder."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.department import Department
from app.seeders.base import BaseSeed

logger = logging.getLogger(__name__)


class DepartmentsSeeder(BaseSeed):
    """Seeder for creating default departments."""
    
    name = "departments"
    description = "Creates system departments"
    required_tables = ["departments"]  # Required table
    
    DEPARTMENTS = [
        {
            "name": "Human Resources",
            "code": "HR",
            "description": "Handles recruitment, onboarding, benefits, and employee relations",
            "manager_id": None  # Will be set after users are seeded if needed
        },
        {
            "name": "Engineering",
            "code": "ENG",
            "description": "Develops and maintains the platform, infrastructure, and technical systems",
            "manager_id": None
        },
        {
            "name": "Sales",
            "code": "SALES",
            "description": "Manages customer acquisition, pipeline, and revenue generation",
            "manager_id": None
        },
        {
            "name": "Finance",
            "code": "FIN",
            "description": "Handles accounting, budgeting, financial planning, and compliance",
            "manager_id": None
        },
    ]
    
    async def run(self, session: AsyncSession, **kwargs) -> dict:
        """Create departments if they don't exist."""
        try:
            # Validate required tables exist
            tables_exist, missing_tables = await self.validate_tables_exist(session)
            if not tables_exist:
                error_msg = (
                    f"Required table(s) missing: {', '.join(missing_tables)}. "
                    "Please run migrations first: python migrate.py"
                )
                logger.error(error_msg)
                return {"success": False, "message": error_msg}
            
            created_departments = 0
            
            # Create departments
            for dept_data in self.DEPARTMENTS:
                stmt = select(Department).where(Department.code == dept_data["code"])
                result = await session.execute(stmt)
                if result.scalars().first():
                    logger.debug(f"Department '{dept_data['name']}' already exists")
                    continue
                
                department = Department(
                    name=dept_data["name"],
                    code=dept_data["code"],
                    description=dept_data["description"],
                    manager_id=dept_data.get("manager_id"),
                    is_active=True
                )
                session.add(department)
                created_departments += 1
            
            if created_departments > 0:
                await session.commit()
                message = f"Created {created_departments} departments"
                logger.info(f"✓ {message}")
                return {"success": True, "message": message}
            
            return {"success": True, "message": "All departments already exist"}
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to seed departments: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
