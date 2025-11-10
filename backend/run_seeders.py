#!/usr/bin/env python
"""
Database seeder runner script.

This script seeds the database with initial data:
- System roles (admin, user, viewer, moderator)
- Default admin account (credentials from .env)

Usage:
    python run_seeders.py                    # Run all seeders with .env credentials
    python run_seeders.py --no-admin         # Run only system roles (skip admin)
    python run_seeders.py --help             # Show help message

The admin account credentials are read from environment variables:
    ADMIN_USERNAME
    ADMIN_EMAIL
    ADMIN_PASSWORD

These should be defined in your .env file. Example:
    ADMIN_USERNAME=admin
    ADMIN_EMAIL=admin@ragfortress.local
    ADMIN_PASSWORD=admin@RAGFortress123

This follows the same pattern as database migrations.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.seeders import DatabaseSeeder
from app.core.database import DatabaseManager
from app.config.database_settings import DatabaseSettings
from app.config.app_settings import AppSettings
from app.core.logging import setup_logging


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def run_seeders(seed_admin: bool = True) -> int:
    """
    Run all database seeders.
    
    Args:
        seed_admin: Whether to seed admin account
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("=" * 70)
        logger.info("DATABASE SEEDER")
        logger.info("=" * 70)
        
        # Get configuration
        db_settings = DatabaseSettings()
        app_settings = AppSettings()
        
        logger.info(f"Database: {db_settings.get_db_url()}")
        
        # Create database manager
        db_manager = DatabaseManager(db_settings)
        
        # Create async engine
        logger.info("Creating database engine...")
        db_manager.create_async_engine()
        
        # Get session factory
        session_factory = db_manager.get_session_factory()
        
        # Create tables
        logger.info("Creating database tables...")
        await db_manager.create_all_tables()
        logger.info("✓ Database tables created")
        
        # Prepare seeder kwargs
        seeder_kwargs = {"session": None}
        
        if seed_admin:
            logger.info(f"Admin seeding enabled")
            seeder_kwargs["admin_username"] = app_settings.ADMIN_USERNAME
            seeder_kwargs["admin_email"] = app_settings.ADMIN_EMAIL
            seeder_kwargs["admin_password"] = app_settings.ADMIN_PASSWORD
        else:
            logger.info("Admin seeding disabled")
        
        # Run seeders
        logger.info("=" * 70)
        logger.info("Running seeders...")
        logger.info("=" * 70)
        
        async with session_factory() as session:
            seeder_kwargs["session"] = session
            results = await DatabaseSeeder.seed_all(**seeder_kwargs)
        
        # Display results
        logger.info("=" * 70)
        logger.info("SEEDING RESULTS")
        logger.info("=" * 70)
        
        if "system_roles" in results:
            roles_result = results["system_roles"]
            logger.info(f"System Roles: {roles_result.get('message', 'N/A')}")
        
        if "admin_account" in results:
            admin_result = results["admin_account"]
            if admin_result.get("created"):
                logger.info(f"✓ Admin Account: {admin_result.get('message')}")
                logger.warning(
                    f"⚠ IMPORTANT: Default admin credentials set. "
                    f"Change password immediately!"
                )
            else:
                logger.info(f"Admin Account: {admin_result.get('message')}")
        
        logger.info("=" * 70)
        logger.info("✓ Seeding completed successfully")
        logger.info("=" * 70)
        
        # Cleanup
        await db_manager.close_connection()
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ Seeding failed: {str(e)}", exc_info=True)
        logger.error("=" * 70)
        return 1


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Seed the database with initial data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--no-admin",
        action="store_true",
        help="Skip admin account seeding (only create system roles)"
    )
    
    args = parser.parse_args()
    
    # Run seeders
    exit_code = asyncio.run(run_seeders(seed_admin=not args.no_admin))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
