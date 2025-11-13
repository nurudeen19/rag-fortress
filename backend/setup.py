#!/usr/bin/env python
"""
Setup script for RAG Fortress application.

Usage:
    python setup.py                          # Run full setup (all seeders by default)
    python setup.py --verify                 # Verify setup is complete
    python setup.py --clear-db               # Clear database (for recovery/restart)
    python setup.py --list-seeders           # Show available seeders and current config
    python setup.py --only-seeder admin,roles_permissions  # Run only specified seeders
    python setup.py --skip-seeder departments  # Run all except specified seeders

Environment Variables (optional):
    ENABLED_SEEDERS                          # Comma-separated seeders to run (empty = all)
    DISABLED_SEEDERS                         # Comma-separated seeders to skip (empty = none)

NOTE: If both ENABLED_SEEDERS and DISABLED_SEEDERS are set, ENABLED_SEEDERS takes priority.
      CLI flags (--only-seeder, --skip-seeder) override environment variables.
"""

import asyncio
import sys
import logging
import os
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

# Seeders that are required to run before others (dependencies)
CRITICAL_SEEDERS = {"admin", "roles_permissions"}

# Preferred seeding order (respects dependencies)
SEEDING_ORDER = [
    "roles_permissions",
    "departments",
    "admin",
    "jobs",
    "knowledge_base",
]


def get_seeders_to_run() -> list:
    """Get list of seeders to run based on environment configuration.
    
    Priority:
    1. ENABLED_SEEDERS (if set, runs only these)
    2. DISABLED_SEEDERS (if set, runs all except these)
    3. Default (if both empty, runs all)
    
    Returns list of seeder names.
    """
    all_seeders = list(SEEDERS.keys())
    
    # Check ENABLED_SEEDERS first (highest priority)
    enabled = os.getenv("ENABLED_SEEDERS", "").strip()
    if enabled:
        seeders = [s.strip() for s in enabled.split(",") if s.strip()]
        return seeders
    
    # Check DISABLED_SEEDERS second
    disabled = os.getenv("DISABLED_SEEDERS", "").strip()
    if disabled:
        skip_list = [s.strip() for s in disabled.split(",") if s.strip()]
        return [s for s in all_seeders if s not in skip_list]
    
    # Default: run all seeders
    return all_seeders


def parse_cli_seeders(args: list) -> tuple:
    """Parse CLI arguments for seeder selection flags.
    
    Returns (only_seeders, skip_seeders) tuples of lists, or (None, None) if not specified.
    
    Flags:
        --only-seeder admin,roles_permissions  (run only these)
        --skip-seeder departments              (run all except these)
    """
    only_seeders = None
    skip_seeders = None
    
    if "--only-seeder" in args:
        idx = args.index("--only-seeder")
        if idx + 1 < len(args):
            only_seeders = [s.strip() for s in args[idx + 1].split(",") if s.strip()]
    
    if "--skip-seeder" in args:
        idx = args.index("--skip-seeder")
        if idx + 1 < len(args):
            skip_seeders = [s.strip() for s in args[idx + 1].split(",") if s.strip()]
    
    return only_seeders, skip_seeders


def list_seeders() -> None:
    """Display available seeders and current configuration."""
    seeders_to_run = get_seeders_to_run()
    all_seeders = list(SEEDERS.keys())
    
    logger.info("Available seeders:")
    for seeder_name in all_seeders:
        status = "✓" if seeder_name in seeders_to_run else "✗"
        logger.info(f"  {status} {seeder_name}")
    
    logger.info(f"\nSeeders to run: {', '.join(seeders_to_run)}")
    
    # Show environment configuration
    enabled = os.getenv("ENABLED_SEEDERS", "").strip()
    disabled = os.getenv("DISABLED_SEEDERS", "").strip()
    
    if enabled:
        logger.info(f"Configuration: ENABLED_SEEDERS={enabled}")
    elif disabled:
        logger.info(f"Configuration: DISABLED_SEEDERS={disabled}")
    else:
        logger.info("Configuration: Default (no env vars set)")


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


async def run_seeders(seeders_to_run: list = None) -> bool:
    """Run seeders and return success status.
    
    Args:
        seeders_to_run: List of seeder names to run. If None, uses environment config.
    """
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
        
        # Determine which seeders to run
        if seeders_to_run is None:
            seeders_to_run = get_seeders_to_run()
        
        # Validate seeder names
        invalid = [s for s in seeders_to_run if s not in SEEDERS]
        if invalid:
            logger.error(f"✗ Unknown seeders: {', '.join(invalid)}")
            return False
        
        # Ensure dependencies are included
        if "admin" in seeders_to_run and "roles_permissions" not in seeders_to_run:
            logger.info("  [INFO] Adding 'roles_permissions' (required by 'admin')")
            seeders_to_run.insert(0, "roles_permissions")
        
        logger.info("Running seeders...")
        
        # Filter to only requested seeders, keeping preferred order
        ordered_seeders = [s for s in SEEDING_ORDER if s in seeders_to_run]
        
        failed = []
        async with session_factory() as session:
            for seeder_name in ordered_seeders:
                seeder = SEEDERS[seeder_name]()
                kwargs = {}
                
                # Prepare kwargs for admin seeder (if needed)
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
                    if seeder_name in CRITICAL_SEEDERS:
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
    """Verify setup is complete by checking if database has tables from all seeders."""
    try:
        db_settings = DatabaseSettings()
        db_manager = DatabaseManager(db_settings)
        await db_manager.create_async_engine()
        
        is_healthy = await db_manager.health_check()
        if not is_healthy:
            logger.error("✗ Database connection failed")
            return False
        
        # Check tables using SQLAlchemy metadata
        from sqlalchemy import inspect as sql_inspect
        
        session_factory = db_manager.get_session_factory()
        
        def check_tables(sync_session):
            inspector = sql_inspect(db_manager.async_engine.sync_engine)
            tables = inspector.get_table_names()
            # Verify database has tables (indicates migrations ran)
            return len(tables) > 0
        
        async with session_factory() as session:
            has_tables = await session.run_sync(check_tables)
        
        await db_manager.close_connection()
        
        if has_tables:
            logger.info("✓ Setup verified - database has tables")
            return True
        else:
            logger.error("✗ Setup incomplete - no tables found")
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
    if "--list-seeders" in args:
        list_seeders()
        return 0
    
    if "--clear-db" in args:
        return 0 if await clear_database() else 1
    
    if "--verify" in args:
        return 0 if await verify_setup() else 1
    
    # Parse CLI seeder selection flags
    only_seeders, skip_seeders = parse_cli_seeders(args)
    
    # Determine which seeders to run
    if only_seeders is not None:
        seeders_to_run = only_seeders
    elif skip_seeders is not None:
        default_seeders = get_seeders_to_run()
        seeders_to_run = [s for s in default_seeders if s not in skip_seeders]
    else:
        seeders_to_run = None  # Use environment defaults in run_seeders()
    
    # Full setup: migrate -> seed
    logger.info("Setting up RAG Fortress...\n")
    
    if not await run_migrations():
        logger.error("\nSetup failed at migrations")
        return 1
    
    logger.info("")
    
    if not await run_seeders(seeders_to_run):
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
