"""
Database seeders for initializing default data.

Seeders are modular, idempotent operations that can be run programmatically.
They follow the same pattern as migrations - call seed_all() to run all seeders.

Example:
    from app.core.seeders import DatabaseSeeder
    from app.core.database import DatabaseManager
    
    db_manager = DatabaseManager(db_settings)
    await db_manager.create_async_engine()
    session_factory = db_manager.get_session_factory()
    
    async with session_factory() as session:
        await DatabaseSeeder.seed_all(session)
"""

import logging
from typing import Optional
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

from app.models.user import User
from app.models.auth import Role

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using argon2."""
    return pwd_context.hash(password)


class BaseSeed(ABC):
    """Base class for all seeders."""
    
    @abstractmethod
    async def run(self, session: AsyncSession) -> dict:
        """
        Run the seeder.
        
        Returns:
            Dict with seeding results including 'success' key.
        """


class AdminAccountSeeder(BaseSeed):
    """Seeder for creating default admin account."""
    
    async def run(
        self,
        session: AsyncSession,
        username: str,
        email: str,
        password: str
    ) -> dict:
        """
        Create admin account if it doesn't exist.
        
        Idempotent operation - only creates if account doesn't exist.
        
        Args:
            session: AsyncSession for database operations
            username: Admin username
            email: Admin email
            password: Admin password (plaintext - will be hashed)
            
        Returns:
            Dict with 'created' (bool) and 'message' keys
        """
        try:
            # Check if admin exists
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            existing = result.scalars().first()
            
            if existing:
                logger.info(f"Admin account '{username}' already exists")
                return {"created": False, "message": "Admin account already exists"}
            
            # Ensure admin role exists
            stmt = select(Role).where(Role.name == "admin")
            result = await session.execute(stmt)
            admin_role = result.scalars().first()
            
            if not admin_role:
                admin_role = Role(
                    name="admin",
                    description="Administrator with full system access",
                    is_system=True
                )
                session.add(admin_role)
                await session.flush()
            
            # Create admin user
            admin_user = User(
                username=username,
                email=email,
                first_name="Admin",
                last_name="Account",
                password_hash=hash_password(password),
                is_active=True,
                is_verified=True,
                is_suspended=False
            )
            admin_user.roles.append(admin_role)
            
            session.add(admin_user)
            await session.commit()
            
            logger.info(f"✓ Admin account '{username}' created successfully")
            return {"created": True, "message": f"Admin account '{username}' created"}
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create admin account: {str(e)}", exc_info=True)
            return {"created": False, "message": str(e), "error": str(e)}


class SystemRolesSeeder(BaseSeed):
    """Seeder for creating default system roles."""
    
    SYSTEM_ROLES = [
        {"name": "admin", "description": "Administrator with full system access"},
        {"name": "user", "description": "Regular user with basic access"},
        {"name": "viewer", "description": "Read-only access to documents"},
        {"name": "moderator", "description": "Content moderation and user management"},
    ]
    
    async def run(self, session: AsyncSession) -> dict:
        """
        Create system roles if they don't exist.
        
        Idempotent operation - only creates roles that don't exist.
        
        Args:
            session: AsyncSession for database operations
            
        Returns:
            Dict with 'created_count' and 'total_count' keys
        """
        try:
            created_count = 0
            
            for role_data in self.SYSTEM_ROLES:
                stmt = select(Role).where(Role.name == role_data["name"])
                result = await session.execute(stmt)
                existing = result.scalars().first()
                
                if existing:
                    logger.debug(f"Role '{role_data['name']}' already exists")
                    continue
                
                role = Role(
                    name=role_data["name"],
                    description=role_data.get("description", ""),
                    is_system=True
                )
                session.add(role)
                created_count += 1
            
            if created_count > 0:
                await session.commit()
                logger.info(f"✓ Created {created_count} system roles")
            
            return {
                "created_count": created_count,
                "total_count": len(self.SYSTEM_ROLES),
                "message": f"Created {created_count} of {len(self.SYSTEM_ROLES)} roles"
            }
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to seed system roles: {str(e)}", exc_info=True)
            return {
                "created_count": 0,
                "total_count": len(self.SYSTEM_ROLES),
                "message": str(e),
                "error": str(e)
            }


class DatabaseSeeder:
    """Seeder orchestrator - runs all seeders."""
    
    @staticmethod
    async def seed_all(
        session: AsyncSession,
        admin_username: Optional[str] = None,
        admin_email: Optional[str] = None,
        admin_password: Optional[str] = None,
    ) -> dict:
        """
        Run all seeders in order.
        
        Args:
            session: AsyncSession for database operations
            admin_username: Admin account username
            admin_email: Admin account email
            admin_password: Admin account password
            
        Returns:
            Dict with results from all seeders
        """
        logger.info("Starting database seeding...")
        
        try:
            results = {}
            
            # Run system roles seeder
            logger.debug("Running system roles seeder...")
            roles_seeder = SystemRolesSeeder()
            results["system_roles"] = await roles_seeder.run(session)
            
            # Run admin account seeder if credentials provided
            if admin_username and admin_email and admin_password:
                logger.debug("Running admin account seeder...")
                admin_seeder = AdminAccountSeeder()
                results["admin_account"] = await admin_seeder.run(
                    session,
                    username=admin_username,
                    email=admin_email,
                    password=admin_password
                )
            else:
                results["admin_account"] = {
                    "created": False,
                    "message": "Admin credentials not provided - skipping admin account creation"
                }
            
            logger.info("✓ Database seeding completed")
            return results
            
        except Exception as e:
            logger.error(f"Seeding failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
