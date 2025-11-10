"""Admin account seeder."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

from app.models.user import User
from app.models.auth import Role
from app.seeders.base import BaseSeed

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AdminSeeder(BaseSeed):
    """Seeder for creating default admin account."""
    
    name = "admin"
    description = "Creates default admin account"
    
    async def run(self, session: AsyncSession, **kwargs) -> dict:
        """Create admin account if it doesn't exist."""
        try:
            username = kwargs.get("username", "admin")
            email = kwargs.get("email", "admin@ragfortress.local")
            password = kwargs.get("password", "admin@RAGFortress123")
            first_name = kwargs.get("first_name", "Admin")
            last_name = kwargs.get("last_name", "User")
            
            # Check if admin exists
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            if result.scalars().first():
                logger.info(f"Admin account '{username}' already exists")
                return {"success": False, "message": "Admin account already exists"}
            
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
                first_name=first_name,
                last_name=last_name,
                password_hash=pwd_context.hash(password),
                is_active=True,
                is_verified=True,
                is_suspended=False
            )
            admin_user.roles.append(admin_role)
            
            session.add(admin_user)
            await session.commit()
            
            logger.info(f"✓ Admin account '{username}' created")
            return {"success": True, "message": f"Admin account '{username}' created"}
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create admin account: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
