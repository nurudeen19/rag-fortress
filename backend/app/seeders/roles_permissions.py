"""Roles and permissions seeder."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.auth import Role, Permission
from app.seeders.base import BaseSeed

logger = logging.getLogger(__name__)


class RolesPermissionsSeeder(BaseSeed):
    """Seeder for creating default roles and permissions."""
    
    name = "roles_permissions"
    description = "Creates system roles and permissions"
    required_tables = ["roles", "permissions"]  # Required tables
    
    ROLES = [
        {"name": "admin", "description": "Administrator with full access"},
        {"name": "executive", "description": "Executive with strategic access"},
        {"name": "manager", "description": "Manager with team oversight access"},
        {"name": "user", "description": "Regular user with standard access"},
    ]
    
    PERMISSIONS = [
        # User permissions
        {"code": "user:create", "description": "Create new users", "resource": "user", "action": "create"},
        {"code": "user:read", "description": "Read user information", "resource": "user", "action": "read"},
        {"code": "user:update", "description": "Update user information", "resource": "user", "action": "update"},
        {"code": "user:delete", "description": "Delete users", "resource": "user", "action": "delete"},
        # Document permissions
        {"code": "document:create", "description": "Upload and create documents", "resource": "document", "action": "create"},
        {"code": "document:read", "description": "Read and view documents", "resource": "document", "action": "read"},
        {"code": "document:update", "description": "Update document metadata", "resource": "document", "action": "update"},
        {"code": "document:delete", "description": "Delete documents", "resource": "document", "action": "delete"},
        # Settings permissions
        {"code": "settings:read", "description": "Read application settings", "resource": "settings", "action": "read"},
        {"code": "settings:update", "description": "Update application settings", "resource": "settings", "action": "update"},
    ]
    
    async def run(self, session: AsyncSession, **kwargs) -> dict:
        """Create roles and permissions if they don't exist."""
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
            
            created_roles = 0
            created_permissions = 0
            
            # Create roles
            for role_data in self.ROLES:
                stmt = select(Role).where(Role.name == role_data["name"])
                result = await session.execute(stmt)
                if result.scalars().first():
                    logger.debug(f"Role '{role_data['name']}' already exists")
                    continue
                
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                    is_system=True
                )
                session.add(role)
                created_roles += 1
            
            # Create permissions
            for perm_data in self.PERMISSIONS:
                stmt = select(Permission).where(Permission.code == perm_data["code"])
                result = await session.execute(stmt)
                if result.scalars().first():
                    logger.debug(f"Permission '{perm_data['code']}' already exists")
                    continue
                
                permission = Permission(
                    code=perm_data["code"],
                    description=perm_data["description"],
                    resource=perm_data["resource"],
                    action=perm_data["action"]
                )
                session.add(permission)
                created_permissions += 1
            
            if created_roles > 0 or created_permissions > 0:
                await session.commit()
                message = f"Created {created_roles} roles, {created_permissions} permissions"
                logger.info(f"✓ {message}")
                return {"success": True, "message": message}
            
            return {"success": True, "message": "All roles and permissions already exist"}
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to seed roles and permissions: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
