"""Application seeders."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.auth import Role
from app.seeders.base import BaseSeed

logger = logging.getLogger(__name__)


class AppSeeder(BaseSeed):
    """Seeder for creating default application data."""
    
    name = "app"
    description = "Creates default application roles"
    
    ROLES = [
        {"name": "admin", "description": "Administrator with full system access"},
        {"name": "user", "description": "Regular user with basic access"},
        {"name": "viewer", "description": "Read-only access to documents"},
        {"name": "moderator", "description": "Content moderation and user management"},
    ]
    
    async def run(self, session: AsyncSession, **kwargs) -> dict:
        """Create default roles if they don't exist."""
        try:
            created_count = 0
            
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
                created_count += 1
            
            if created_count > 0:
                await session.commit()
                logger.info(f"✓ Created {created_count} roles")
                return {"success": True, "message": f"Created {created_count} roles"}
            
            return {"success": True, "message": "All roles already exist"}
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to seed application data: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
