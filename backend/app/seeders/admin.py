"""Admin account seeder."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.auth import Role
from app.models.user_permission import PermissionLevel, UserPermission
from app.seeders.base import BaseSeed
from app.config.settings import settings

logger = logging.getLogger(__name__)


class AdminSeeder(BaseSeed):
    """Seeder for creating default admin account."""
    
    name = "admin"
    description = "Creates default admin account"
    required_tables = ["users", "roles"]  # Required tables
    
    def _hash_password(self, password: str) -> str:
        """Hash password using argon2 (must match security.py configuration)."""
        from passlib.context import CryptContext
        
        # Use argon2 to match security.py configuration
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Failed to hash password with argon2: {e}")
            raise
    
    async def run(self, session: AsyncSession, **kwargs) -> dict:
        """Create admin account if it doesn't exist."""
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
            
            username = kwargs.get("username", settings.ADMIN_USERNAME)
            email = kwargs.get("email", settings.ADMIN_EMAIL)
            password = kwargs.get("password", settings.ADMIN_PASSWORD)
            first_name = kwargs.get("first_name", settings.ADMIN_FIRSTNAME)
            last_name = kwargs.get("last_name", settings.ADMIN_LASTNAME)
            
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
            
            # Hash password using available method
            password_hash = self._hash_password(password)
            
            # Create admin user
            admin_user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=password_hash,
                is_active=True,
                is_verified=True,
                is_suspended=False
            )
            admin_user.roles.append(admin_role)
            permission = UserPermission(
                user=admin_user,
                org_level_permission=PermissionLevel.HIGHLY_CONFIDENTIAL.value,
                is_active=True
            )
            session.add(permission)
            
            session.add(admin_user)
            await session.commit()
            
            logger.info(f"✓ Admin account '{username}' created")
            return {"success": True, "message": f"Admin account '{username}' created"}
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create admin account: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
