#!/usr/bin/env python
"""
Initial application setup script - for first-time deployment.

Runs migrations and seeders in correct order:
1. Database initialization (create tables)
2. Database migrations (Alembic)
3. Database seeding (populate initial data)
4. Job queue initialization

Usage:
    python setup.py                 # Run all steps
    python setup.py --skip-seeders  # Run migrations only
    python setup.py --verify        # Verify existing setup
"""

import asyncio
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import DatabaseManager
from app.config.database_settings import DatabaseSettings
from app.config.app_settings import AppSettings
from app.seeders import SEEDERS
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def run_migrations() -> bool:
    """
    Run database migrations using Alembic.
    
    Returns:
        True if successful, False otherwise
    """
    import subprocess
    
    logger.info("=" * 70)
    logger.info("Running database migrations...")
    logger.info("=" * 70)
    
    try:
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✓ Database migrations completed successfully")
            return True
        else:
            logger.error(f"✗ Migration failed: {result.stderr}")
            return False
    
    except FileNotFoundError:
        logger.error("✗ Alembic not found. Please install: pip install alembic")
        return False
    except subprocess.TimeoutExpired:
        logger.error("✗ Migration timed out")
        return False
    except Exception as e:
        logger.error(f"✗ Migration error: {e}", exc_info=True)
        return False


async def run_seeders_sequence() -> bool:
    """
    Run database seeders in sequence.
    
    Returns:
        True if all successful, False if any failed
    """
    logger.info("=" * 70)
    logger.info("Seeding database...")
    logger.info("=" * 70)
    
    try:
        # Get configuration
        db_settings = DatabaseSettings()
        app_settings = AppSettings()
        
        logger.info(f"Database: {db_settings.get_database_url()}")
        
        # Setup database
        db_manager = DatabaseManager(db_settings)
        await db_manager.create_async_engine()
        session_factory = db_manager.get_session_factory()
        
        # Check database connection
        logger.info("Checking database connection...")
        is_healthy = await db_manager.health_check()
        if not is_healthy:
            logger.error("✗ Database connection failed")
            return False
        
        logger.info("✓ Database connection successful")
        
        # Seeding order: critical first
        seeding_order = [
            "roles_permissions",  # Must be first (referenced by other seeders)
            "departments",        # Admin seeder may use departments
            "admin",              # Create admin user
            "jobs",               # Create initial jobs queue
            "knowledge_base",     # Initialize knowledge base
        ]
        
        failed_seeders = []
        async with session_factory() as session:
            for seeder_name in seeding_order:
                if seeder_name not in SEEDERS:
                    logger.debug(f"Skipping seeder '{seeder_name}' (not found)")
                    continue
                
                logger.info(f"\nRunning seeder: {seeder_name}")
                seeder_class = SEEDERS[seeder_name]
                seeder = seeder_class()
                
                # Pass config for admin seeder
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
                    logger.info(f"✓ {result.get('message')}")
                else:
                    logger.warning(f"⚠ {result.get('message')}")
                    if seeder_name in ["roles_permissions", "admin"]:
                        # Critical seeders - mark as failure
                        failed_seeders.append(seeder_name)
        
        # Cleanup
        await db_manager.close_connection()
        
        if failed_seeders:
            logger.error(f"\n✗ Critical seeders failed: {', '.join(failed_seeders)}")
            return False
        
        logger.info("\n✓ All seeders completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"✗ Seeding failed: {str(e)}", exc_info=True)
        return False


async def verify_setup() -> bool:
    """
    Verify that all required components are initialized.
    
    Returns:
        True if setup is complete, False otherwise
    """
    logger.info("=" * 70)
    logger.info("Verifying application setup...")
    logger.info("=" * 70)
    
    try:
        db_settings = DatabaseSettings()
        db_manager = DatabaseManager(db_settings)
        await db_manager.create_async_engine()
        session_factory = db_manager.get_session_factory()
        
        # Check database connection
        logger.info("Checking database connection...")
        is_healthy = await db_manager.health_check()
        if not is_healthy:
            logger.error("✗ Database connection failed")
            return False
        logger.info("✓ Database connection successful")
        
        # Check required tables
        from sqlalchemy import inspect as sql_inspect
        
        async def check_tables(sync_session):
            """Check that required tables exist."""
            inspector = sql_inspect(db_manager.engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                "users",
                "roles",
                "permissions",
                "departments",
                "jobs",
                "file_uploads",
            ]
            
            missing = [t for t in required_tables if t not in tables]
            return len(missing) == 0, missing
        
        async with session_factory() as session:
            tables_ok, missing_tables = await session.run_sync(check_tables)
            
            if not tables_ok:
                logger.error(f"✗ Missing tables: {', '.join(missing_tables)}")
                logger.error("Run: python setup.py")
                return False
            
            logger.info("✓ All required tables exist")
        
        await db_manager.close_connection()
        
        logger.info("=" * 70)
        logger.info("✓ Application setup is complete and valid")
        logger.info("=" * 70)
        return True
    
    except Exception as e:
        logger.error(f"✗ Verification failed: {str(e)}", exc_info=True)
        return False


async def main(args):
    """Main setup flow."""
    logger.info("=" * 70)
    logger.info("RAG Fortress - Initial Setup")
    logger.info("=" * 70)
    
    if "--verify" in args:
        # Verify existing setup
        success = await verify_setup()
        return 0 if success else 1
    
    # Step 1: Run migrations
    logger.info("\nSTEP 1: Database Migrations")
    migrations_ok = await run_migrations()
    if not migrations_ok:
        logger.error("\n✗ Setup failed at migration step")
        return 1
    
    # Step 2: Run seeders (unless skipped)
    if "--skip-seeders" not in args:
        logger.info("\nSTEP 2: Database Seeding")
        seeders_ok = await run_seeders_sequence()
        if not seeders_ok:
            logger.error("\n✗ Setup failed at seeding step")
            return 1
    else:
        logger.info("\nSTEP 2: Skipped (--skip-seeders)")
    
    # Step 3: Verify setup
    logger.info("\nSTEP 3: Verification")
    verify_ok = await verify_setup()
    if not verify_ok:
        logger.error("\n✗ Setup verification failed")
        return 1
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ SETUP COMPLETE")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("  1. Review .env configuration")
    logger.info("  2. Start the application: python run.py")
    logger.info("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(exit_code)
