#!/usr/bin/env python
"""
Setup script for RAG Fortress application.

Usage:
    python setup.py              # Run full setup: connect -> migrate -> seed
    python setup.py --verify     # Verify setup is complete
    python setup.py --clear-db   # Clear database (for recovery/restart)
"""

import asyncio
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import DatabaseManager
from app.config.database_settings import DatabaseSettings
from app.config.app_settings import AppSettings
from app.seeders import SEEDERS
from app.core.logging import setup_logging

# Setup logging with console output
setup_logging()
logger = logging.getLogger(__name__)

# Force UTF-8 console output for Windows
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)


async def run_migrations() -> bool:
    """Run database migrations and return success status."""
    import subprocess
    
    logger.info("Running migrations...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✓ Migrations completed")
            return True
        else:
            logger.error(f"✗ Migration failed: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("✗ Alembic not found. Install with: pip install alembic")
        return False
    except Exception as e:
        logger.error(f"✗ Migration error: {e}")
        return False


async def run_seeders() -> bool:
    """Run seeders and return success status."""
    try:
        db_settings = DatabaseSettings()
        app_settings = AppSettings()
        db_manager = DatabaseManager(db_settings)
        
        await db_manager.create_async_engine()
        session_factory = db_manager.get_session_factory()
        
        # Check connection
        is_healthy = await db_manager.health_check()
        if not is_healthy:
            logger.error("✗ Database connection failed")
            return False
        
        logger.info("Running seeders...")
        
        # Seeding order
        seeding_order = [
            "roles_permissions",
            "departments",
            "admin",
            "jobs",
            "knowledge_base",
        ]
        
        failed = []
        async with session_factory() as session:
            for seeder_name in seeding_order:
                if seeder_name not in SEEDERS:
                    continue
                
                seeder = SEEDERS[seeder_name]()
                kwargs = {}
                
                if seeder_name == "admin":
                    kwargs = {
                        "username": app_settings.ADMIN_USERNAME,
                        "email": app_settings.ADMIN_EMAIL,
                        "password": app_settings.ADMIN_PASSWORD,
                        "first_name": getattr(app_settings, "ADMIN_FIRSTNAME", "Admin"),
                        "last_name": getattr(app_settings, "ADMIN_LASTNAME", "User"),
                    }
                
                result = await seeder.run(session, **kwargs)
                
                if result.get("success"):
                    logger.info(f"  ✓ {seeder_name}: {result.get('message')}")
                else:
                    logger.warning(f"  ! {seeder_name}: {result.get('message')}")
                    if seeder_name in ["roles_permissions", "admin"]:
                        failed.append(seeder_name)
        
        await db_manager.close_connection()
        
        if failed:
            logger.error(f"✗ Critical seeders failed: {', '.join(failed)}")
            return False
        
        logger.info("✓ Seeders completed")
        return True
    
    except Exception as e:
        logger.error(f"✗ Seeding error: {e}")
        return False


async def verify_setup() -> bool:
    """Verify setup is complete."""
    try:
        db_settings = DatabaseSettings()
        db_manager = DatabaseManager(db_settings)
        await db_manager.create_async_engine()
        
        is_healthy = await db_manager.health_check()
        if not is_healthy:
            logger.error("✗ Database connection failed")
            return False
        
        # Check tables
        from sqlalchemy import inspect as sql_inspect
        
        session_factory = db_manager.get_session_factory()
        
        def check_tables(sync_session):
            inspector = sql_inspect(db_manager.async_engine.sync_engine)
            tables = inspector.get_table_names()
            required = ["users", "roles", "permissions", "departments", "jobs", "file_uploads"]
            return all(t in tables for t in required)
        
        async with session_factory() as session:
            tables_ok = await session.run_sync(check_tables)
        
        await db_manager.close_connection()
        
        if tables_ok:
            logger.info("✓ Setup verified - all tables exist")
            return True
        else:
            logger.error("✗ Setup incomplete - missing required tables")
            return False
    
    except Exception as e:
        logger.error(f"✗ Verification error: {e}")
        return False


async def clear_database() -> bool:
    """Clear all database tables."""
    confirm = input("\nWARNING: Delete all database tables? Type 'yes' to confirm: ").strip().lower()
    if confirm != 'yes':
        logger.info("Cancelled")
        return False
    
    try:
        db_settings = DatabaseSettings()
        db_manager = DatabaseManager(db_settings)
        await db_manager.create_async_engine()
        
        is_healthy = await db_manager.health_check()
        if not is_healthy:
            logger.error("✗ Database connection failed")
            return False
        
        from sqlalchemy import text, inspect as sql_inspect
        
        session_factory = db_manager.get_session_factory()
        async with session_factory() as session:
            # Disable foreign key checks
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            def get_tables(sync_session):
                inspector = sql_inspect(db_manager.async_engine.sync_engine)
                return inspector.get_table_names()
            
            tables = await session.run_sync(get_tables)
            
            for table in tables:
                await session.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            await session.commit()
        
        await db_manager.close_connection()
        
        logger.info(f"✓ Cleared {len(tables)} tables")
        logger.info("Run 'python setup.py' to set up again")
        return True
    
    except Exception as e:
        logger.error(f"✗ Clear database error: {e}")
        return False


async def main(args):
    """Main setup flow."""
    if "--clear-db" in args:
        return 0 if await clear_database() else 1
    
    if "--verify" in args:
        return 0 if await verify_setup() else 1
    
    # Full setup: migrate -> seed
    logger.info("Setting up RAG Fortress...\n")
    
    if not await run_migrations():
        logger.error("\nSetup failed at migrations")
        return 1
    
    logger.info("")
    
    if not await run_seeders():
        logger.error("\nSetup failed at seeding - data may be partially loaded")
        logger.info("Run 'python setup.py --clear-db' to reset and try again\n")
        return 1
    
    logger.info("")
    
    if not await verify_setup():
        logger.error("\nSetup verification failed")
        return 1
    
    logger.info("\n✓ Setup complete!")
    logger.info("Next: python run.py\n")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(exit_code)
