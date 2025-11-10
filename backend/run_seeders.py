#!/usr/bin/env python
"""Database seeder runner script."""

import asyncio
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import DatabaseManager
from app.config.database_settings import DatabaseSettings
from app.config.app_settings import AppSettings
from app.seeders import SEEDERS
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def run_seeders(seeder_names: list = None) -> int:
    """
    Run database seeders.
    
    Args:
        seeder_names: List of seeder names to run. If None, run all.
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        if seeder_names is None:
            seeder_names = list(SEEDERS.keys())
        
        # Warn about data removal
        logger.warning("=" * 70)
        logger.warning("⚠️  WARNING: Running seeders may overwrite or clear existing data")
        logger.warning("=" * 70)
        
        # Get configuration
        db_settings = DatabaseSettings()
        app_settings = AppSettings()
        
        logger.info(f"Database: {db_settings.get_database_url()}")
        logger.info(f"Seeders to run: {', '.join(seeder_names)}")
        
        # Setup database
        db_manager = DatabaseManager(db_settings)
        await db_manager.create_async_engine()
        session_factory = db_manager.get_session_factory()
        
        # Create tables
        logger.info("Creating database tables...")
        await db_manager.create_all_tables()
        logger.info("✓ Database tables created")
        
        # Run seeders
        logger.info("=" * 70)
        logger.info("Running seeders...")
        logger.info("=" * 70)
        
        results = {}
        async with session_factory() as session:
            for seeder_name in seeder_names:
                if seeder_name not in SEEDERS:
                    logger.warning(f"Seeder '{seeder_name}' not found")
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
                results[seeder_name] = result
                
                if result.get("success"):
                    logger.info(f"✓ {result.get('message')}")
                else:
                    logger.warning(f"⚠ {result.get('message')}")
        
        # Display summary
        logger.info("=" * 70)
        logger.info("SEEDING COMPLETE")
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
        description="Seed the database with initial data"
    )
    parser.add_argument(
        "seeders",
        nargs="*",
        help="Specific seeders to run (e.g., admin app). If empty, runs all."
    )
    
    args = parser.parse_args()
    seeder_names = args.seeders if args.seeders else None
    
    exit_code = asyncio.run(run_seeders(seeder_names))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
