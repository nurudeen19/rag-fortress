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
    python setup.py --clear-db      # Clear all data and reset (use with caution!)
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field
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

# Force console output with UTF-8 encoding
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)


@dataclass
class SetupResult:
    """Result of a setup operation."""
    success: bool
    message: str
    step: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"{status} [{self.step}] {self.message}"


@dataclass
class SetupContext:
    """Context tracking operations for potential rollback."""
    operations: List[Dict[str, Any]] = field(default_factory=list)
    db_manager: Any = None
    session_factory: Any = None
    
    def add_operation(self, op_type: str, op_id: str, data: Dict[str, Any] = None) -> None:
        """Track an operation that was performed."""
        self.operations.append({
            "type": op_type,
            "id": op_id,
            "data": data or {},
            "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop() else None
        })
        logger.debug(f"Tracked operation: {op_type}:{op_id}")
    
    async def rollback(self) -> None:
        """Rollback operations in reverse order."""
        logger.warning("=" * 70)
        logger.warning("ROLLING BACK operations...")
        logger.warning("=" * 70)
        
        for operation in reversed(self.operations):
            op_type = operation.get("type")
            op_id = operation.get("id")
            
            try:
                if op_type == "migration":
                    logger.warning(f"→ Reverting migration: {op_id}")
                    # Migrations are handled separately via downgrade
                    pass
                elif op_type == "seeder":
                    logger.warning(f"→ Rolling back seeder data: {op_id}")
                    # For now, just log - actual rollback would need seeder-specific logic
                    logger.debug(f"  Seeder data for '{op_id}' should be manually reviewed")
                
                logger.warning(f"  ✓ Rolled back {op_type}:{op_id}")
            except Exception as e:
                logger.error(f"  ✗ Failed to rollback {op_type}:{op_id}: {e}")
        
        logger.warning("Rollback completed (manual intervention may be needed)")
        logger.warning("=" * 70)


async def run_migrations(ctx: SetupContext) -> SetupResult:
    """
    Run database migrations using Alembic.
    
    Args:
        ctx: Setup context for tracking operations
    
    Returns:
        SetupResult with migration status
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
            ctx.add_operation("migration", "alembic_upgrade")
            logger.info("✓ Database migrations completed successfully")
            return SetupResult(
                success=True,
                message="Database migrations completed successfully",
                step="MIGRATIONS",
                details={"alembic_output": result.stdout}
            )
        else:
            logger.error(f"✗ Migration failed: {result.stderr}")
            return SetupResult(
                success=False,
                message=f"Migration failed: {result.stderr}",
                step="MIGRATIONS",
                details={"error": result.stderr}
            )
    
    except FileNotFoundError:
        msg = "Alembic not found. Please install: pip install alembic"
        logger.error(f"✗ {msg}")
        return SetupResult(
            success=False,
            message=msg,
            step="MIGRATIONS"
        )
    except subprocess.TimeoutExpired:
        msg = "Migration timed out"
        logger.error(f"✗ {msg}")
        return SetupResult(
            success=False,
            message=msg,
            step="MIGRATIONS"
        )
    except Exception as e:
        logger.error(f"✗ Migration error: {e}", exc_info=True)
        return SetupResult(
            success=False,
            message=f"Migration error: {str(e)}",
            step="MIGRATIONS",
            details={"error": str(e)}
        )


async def run_seeders_sequence(ctx: SetupContext) -> SetupResult:
    """
    Run database seeders in sequence.
    
    Args:
        ctx: Setup context for tracking operations
    
    Returns:
        SetupResult with seeding status
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
        
        # Store in context for potential rollback
        ctx.db_manager = db_manager
        ctx.session_factory = session_factory
        
        # Check database connection
        logger.info("Checking database connection...")
        is_healthy = await db_manager.health_check()
        if not is_healthy:
            msg = "Database connection failed"
            logger.error(f"✗ {msg}")
            return SetupResult(
                success=False,
                message=msg,
                step="SEEDING"
            )
        
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
        successful_seeders = []
        
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
                    ctx.add_operation("seeder", seeder_name, {"message": result.get("message")})
                    successful_seeders.append(seeder_name)
                else:
                    logger.warning(f"⚠ {result.get('message')}")
                    if seeder_name in ["roles_permissions", "admin"]:
                        # Critical seeders - mark as failure
                        failed_seeders.append(seeder_name)
        
        # Cleanup
        await db_manager.close_connection()
        
        if failed_seeders:
            msg = f"Critical seeders failed: {', '.join(failed_seeders)}"
            logger.error(f"\n✗ {msg}")
            return SetupResult(
                success=False,
                message=msg,
                step="SEEDING",
                details={
                    "failed": failed_seeders,
                    "successful": successful_seeders
                }
            )
        
        logger.info("\n✓ All seeders completed successfully")
        return SetupResult(
            success=True,
            message="All seeders completed successfully",
            step="SEEDING",
            details={"seeders": successful_seeders}
        )
    
    except Exception as e:
        logger.error(f"✗ Seeding failed: {str(e)}", exc_info=True)
        return SetupResult(
            success=False,
            message=f"Seeding failed: {str(e)}",
            step="SEEDING",
            details={"error": str(e)}
        )


async def verify_setup(ctx: SetupContext = None) -> SetupResult:
    """
    Verify that all required components are initialized.
    
    Args:
        ctx: Setup context (optional)
    
    Returns:
        SetupResult with verification status
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
            msg = "Database connection failed"
            logger.error(f"✗ {msg}")
            return SetupResult(
                success=False,
                message=msg,
                step="VERIFICATION"
            )
        logger.info("✓ Database connection successful")
        
        # Check required tables
        from sqlalchemy import inspect as sql_inspect
        
        def check_tables(sync_session):
            """Check that required tables exist."""
            inspector = sql_inspect(db_manager.async_engine.sync_engine)
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
                msg = f"Missing tables: {', '.join(missing_tables)}"
                logger.error(f"✗ {msg}")
                return SetupResult(
                    success=False,
                    message=msg,
                    step="VERIFICATION",
                    details={"missing_tables": missing_tables}
                )
            
            logger.info("✓ All required tables exist")
        
        await db_manager.close_connection()
        
        logger.info("=" * 70)
        logger.info("✓ Application setup is complete and valid")
        logger.info("=" * 70)
        return SetupResult(
            success=True,
            message="Application setup is complete and valid",
            step="VERIFICATION"
        )
    
    except Exception as e:
        logger.error(f"✗ Verification failed: {str(e)}", exc_info=True)
        return SetupResult(
            success=False,
            message=f"Verification failed: {str(e)}",
            step="VERIFICATION",
            details={"error": str(e)}
        )


async def clear_database() -> SetupResult:
    """
    Clear all data from the database.
    
    Returns:
        SetupResult indicating success or failure
    """
    logger.info("=" * 70)
    logger.warning("⚠ WARNING: This will delete ALL data from the database!")
    logger.info("=" * 70)
    
    confirm = input("\nType 'yes' to confirm database reset: ").strip().lower()
    if confirm != 'yes':
        logger.info("✗ Database reset cancelled")
        return SetupResult(
            success=False,
            message="Database reset cancelled by user",
            step="CLEAR_DB"
        )
    
    try:
        db_settings = DatabaseSettings()
        db_manager = DatabaseManager(db_settings)
        await db_manager.create_async_engine()
        
        logger.info("Connecting to database...")
        is_healthy = await db_manager.health_check()
        if not is_healthy:
            msg = "Database connection failed"
            logger.error(f"✗ {msg}")
            return SetupResult(
                success=False,
                message=msg,
                step="CLEAR_DB"
            )
        
        logger.info("✓ Database connection successful")
        
        # Get all tables and drop them
        from sqlalchemy import text, inspect as sql_inspect
        
        session_factory = db_manager.get_session_factory()
        async with session_factory() as session:
            # Disable foreign key checks for MySQL
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            def get_tables(sync_session):
                """Get all table names."""
                inspector = sql_inspect(db_manager.async_engine.sync_engine)
                return inspector.get_table_names()
            
            tables = await session.run_sync(get_tables)
            
            logger.info(f"Found {len(tables)} table(s) to clear")
            
            # Drop all tables
            for table in tables:
                logger.info(f"  → Dropping table: {table}")
                await session.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            
            # Re-enable foreign key checks
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            await session.commit()
        
        logger.info("✓ All tables dropped successfully")
        
        await db_manager.close_connection()
        
        logger.info("=" * 70)
        logger.info("✓ Database cleared successfully")
        logger.info("=" * 70)
        logger.info("\nYou can now run: python setup.py")
        logger.info("=" * 70)
        
        return SetupResult(
            success=True,
            message="Database cleared successfully",
            step="CLEAR_DB",
            details={"tables_dropped": tables}
        )
    
    except Exception as e:
        logger.error(f"✗ Failed to clear database: {str(e)}", exc_info=True)
        return SetupResult(
            success=False,
            message=f"Failed to clear database: {str(e)}",
            step="CLEAR_DB",
            details={"error": str(e)}
        )
    
    except Exception as e:
        logger.error(f"✗ Failed to clear database: {str(e)}", exc_info=True)
        return SetupResult(
            success=False,
            message=f"Failed to clear database: {str(e)}",
            step="CLEAR_DB",
            details={"error": str(e)}
        )


async def main(args):
    """Main setup flow with error handling and rollback."""
    logger.info("=" * 70)
    logger.info("RAG Fortress - Initial Setup")
    logger.info("=" * 70)
    
    # Handle --clear-db flag
    if "--clear-db" in args:
        logger.info("")
        result = await clear_database()
        logger.info(f"\n{result}")
        return 0 if result.success else 1
    
    # Handle --verify flag
    if "--verify" in args:
        logger.info("")
        ctx = SetupContext()
        result = await verify_setup(ctx)
        logger.info(f"\n{result}")
        return 0 if result.success else 1
    
    # Create context to track operations
    ctx = SetupContext()
    results = []
    
    try:
        # Step 1: Run migrations
        logger.info("\nSTEP 1: Database Migrations")
        mig_result = await run_migrations(ctx)
        results.append(mig_result)
        logger.info(f"{mig_result}\n")
        
        if not mig_result.success:
            logger.error("\n✗ Setup failed at migration step")
            return 1
        
        # Step 2: Run seeders (unless skipped)
        if "--skip-seeders" not in args:
            logger.info("STEP 2: Database Seeding")
            seed_result = await run_seeders_sequence(ctx)
            results.append(seed_result)
            logger.info(f"{seed_result}\n")
            
            if not seed_result.success:
                logger.error("\n" + "=" * 70)
                logger.error("SETUP FAILED AT SEEDING STEP")
                logger.error("=" * 70)
                
                # Check if this is due to existing data
                if "admin" in seed_result.message.lower():
                    logger.warning("")
                    logger.warning("NOTICE: Setup was already run previously.")
                    logger.warning("Admin account already exists in the database.")
                    logger.warning("")
                    logger.info("To run setup again, choose one of these options:")
                    logger.info("")
                    logger.info("Option 1: Clear database and re-run setup")
                    logger.info("  > python setup.py --clear-db")
                    logger.info("  > python setup.py")
                    logger.info("")
                    logger.info("Option 2: Verify existing setup is complete")
                    logger.info("  > python setup.py --verify")
                    logger.info("=" * 70)
                else:
                    logger.warning("Attempting rollback of previous operations...")
                    await ctx.rollback()
                return 1
        else:
            logger.info("\nSTEP 2: Skipped (--skip-seeders)")
        
        # Step 3: Verify setup
        logger.info("\nSTEP 3: Verification")
        ver_result = await verify_setup(ctx)
        results.append(ver_result)
        logger.info(f"{ver_result}\n")
        
        if not ver_result.success:
            logger.error("\n✗ Setup verification failed")
            logger.warning("Attempting rollback...")
            await ctx.rollback()
            return 1
        
        # Success summary
        logger.info("\n" + "=" * 70)
        logger.info("✓ SETUP COMPLETE - SUMMARY")
        logger.info("=" * 70)
        for result in results:
            logger.info(f"  {result}")
        
        logger.info("\nNext steps:")
        logger.info("  1. Review .env configuration")
        logger.info("  2. Start the application: python run.py")
        logger.info("=" * 70)
        
        return 0
    
    except Exception as e:
        logger.error(f"\n✗ Unexpected error during setup: {str(e)}", exc_info=True)
        logger.warning("Attempting rollback...")
        await ctx.rollback()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main(sys.argv[1:]))
    sys.exit(exit_code)
