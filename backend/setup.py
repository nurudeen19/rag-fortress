#!/usr/bin/env python
"""
Setup script for RAG Fortress application.

Usage:
    python setup.py --all                    # Run full setup (all seeders)
    python setup.py --only-seeder admin,roles_permissions  # Run only specified seeders
    python setup.py --skip-seeder departments  # Run all seeders except specified
    python setup.py --verify                 # Verify setup is complete
    python setup.py --clear-db               # Clear database (for recovery/restart)
    python setup.py --list-seeders           # Show available seeders

Available Seeders:
    admin, roles_permissions, departments, application_settings, jobs, 
    knowledge_base, conversations, activity_logs

NOTE: Must specify --all, --only-seeder, or --skip-seeder to run seeders.
      No default seeders run without explicit options.
"""

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
    "application_settings",
    "jobs",
    "knowledge_base",
    "conversations",
    "activity_logs",
]


def show_help() -> None:
    """Display help information for all available options."""
    help_text = """
RAG Fortress Setup - Configuration Options

USAGE:
    python setup.py [OPTIONS]

OPTIONS:
    (no arguments)              Show help (must specify seeder options)

    --help                      Show this help message

    --list-seeders              Display available seeders

    --all                       Run full setup: migrations + all seeders + verification
                                Example: python setup.py --all

    --verify                    Verify setup is complete
                                Checks if database has tables (indicates migrations ran)

    --clear-db                  Clear all database tables
                                DANGEROUS: Requires 'yes' confirmation
                                Use this to reset and start fresh

    --only-seeder NAMES         Run only specified seeders
                                NAMES: comma-separated list, e.g., admin,roles_permissions
                                Example: python setup.py --only-seeder admin,roles_permissions

    --skip-seeder NAMES         Run all seeders except specified
                                NAMES: comma-separated list, e.g., departments,jobs
                                Example: python setup.py --skip-seeder departments,jobs

PRIORITY ORDER (CLI only):
    --all, --only-seeder, and --skip-seeder are mutually exclusive.
    One of these must be specified to run seeders.

AVAILABLE SEEDERS:
    • admin                 Create admin user account (critical)
    • roles_permissions     Create roles and permissions (critical)
    • departments           Create department records (optional)
    • application_settings  Create application settings (optional)
    • jobs                  Create initial job records (optional)
    • knowledge_base        Create knowledge base records (optional)
    • conversations         Create sample conversations (optional)
    • activity_logs         Create sample activity logs (optional)

DEPENDENCIES:
    • admin requires roles_permissions (automatically included if needed)
    • Other seeders have no dependencies

EXAMPLES:
    # Run all seeders
    python setup.py --all

    # View available seeders
    python setup.py --list-seeders

    # Production setup (minimal, only critical seeders)
    python setup.py --only-seeder admin,roles_permissions

    # Development without optional data
    python setup.py --skip-seeder conversations,activity_logs

    # Test specific seeders
    python setup.py --only-seeder admin,roles_permissions

    # Reset database
    python setup.py --clear-db

    # Verify setup is complete
    python setup.py --verify
"""
    print(help_text)


def get_all_seeders() -> list:
    """Get list of all available seeders.
    
    Returns list of all seeder names.
    """
    return list(SEEDERS.keys())


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
    """Display available seeders."""
    all_seeders = get_all_seeders()
    
    logger.info("Available seeders:")
    for i, seeder_name in enumerate(all_seeders, 1):
        logger.info(f"  {i}. {seeder_name}")
    
    logger.info(f"\nTotal: {len(all_seeders)} seeders available")
    logger.info("\nUsage: python setup.py --all  (or --only-seeder / --skip-seeder)")


async def cleanup_postgres_enums() -> None:
    """Clean up PostgreSQL ENUM types that may conflict with migrations.
    
    This handles the case where ENUM types already exist from previous migrations,
    which can cause "type already exists" errors.
    """
    db_settings = DatabaseSettings()
    
    # Only for PostgreSQL
    if db_settings.DATABASE_PROVIDER.lower() != 'postgresql':
        return
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=db_settings.DB_HOST,
            port=db_settings._get_port(),
            user=db_settings.DB_USER,
            password=db_settings.DB_PASSWORD,
            database=db_settings.DB_NAME
        )
        cursor = conn.cursor()
        
        # Drop ENUM types if they exist
        cursor.execute('DROP TYPE IF EXISTS errorreportcategory CASCADE;')
        cursor.execute('DROP TYPE IF EXISTS errorreportstatus CASCADE;')
        cursor.execute('DROP TYPE IF EXISTS filestatus CASCADE;')
        conn.commit()
        cursor.close()
        conn.close()
        
    except ImportError:
        logger.warning("psycopg2 not available - skipping ENUM cleanup")
    except Exception as e:
        logger.debug(f"ENUM cleanup (non-critical): {e}")


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
            conn = await session.connection()
            dialect = conn.dialect.name
            
            def get_tables(sync_session):
                inspector = sql_inspect(db_manager.async_engine.sync_engine)
                return inspector.get_table_names()
            
            tables = await session.run_sync(get_tables)
            
            # Drop tables with appropriate syntax for each dialect
            # Note: CASCADE handles foreign key dependencies automatically
            # This approach works with managed databases (Neon, Supabase) that
            # don't allow session_replication_role on pooled connections
            if dialect == 'mysql':
                # Disable FK checks for MySQL
                await session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                for table in tables:
                    await session.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
                await session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            elif dialect == 'postgresql':
                # Use CASCADE to handle dependencies
                for table in tables:
                    await session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            else:  # SQLite
                for table in tables:
                    await session.execute(text(f"DROP TABLE IF EXISTS {table}"))
            
            await session.commit()
        
        await db_manager.close_connection()
        
        logger.info(f"✓ Cleared {len(tables)} tables")
        logger.info("Run 'python setup.py' to set up again")
        return True
    
    except Exception as e:
        logger.error(f"✗ Clear database error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main(args):
    """Main setup flow."""
    if "--help" in args or "-h" in args:
        show_help()
        return 0
    
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
    if "--all" in args:
        seeders_to_run = get_all_seeders()
    elif only_seeders is not None:
        seeders_to_run = only_seeders
    elif skip_seeders is not None:
        all_seeders = get_all_seeders()
        seeders_to_run = [s for s in all_seeders if s not in skip_seeders]
    else:
        # No seeder option specified
        show_help()
        logger.error("\n❌ Must specify --all, --only-seeder, or --skip-seeder to run seeders")
        logger.info(f"Available seeders: {', '.join(get_all_seeders())}")
        return 1
    
    # Full setup: migrate -> seed
    logger.info("Setting up RAG Fortress...\n")
    
    # Clean up PostgreSQL ENUM types before migrations (prevents "type already exists" errors)
    await cleanup_postgres_enums()
    
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
    logger.info("Next: python startup.py\n")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(exit_code)
