#!/usr/bin/env python
"""
SQLite Migration Test Script

Tests that migrations work correctly with SQLite database.
This ensures the system can handle SQLite without any code changes.

Usage:
    python test_sqlite_migration.py [--clean]

Options:
    --clean     Remove test database before running
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

import argparse
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config


def setup_test_env():
    """Set up test environment variables for SQLite."""
    os.environ["DATABASE_PROVIDER"] = "sqlite"
    os.environ["SQLITE_PATH"] = "./test_rag_fortress.db"
    os.environ["ENVIRONMENT"] = "development"
    
    # Disable other optional services for testing
    os.environ["CACHE_ENABLED"] = "false"
    os.environ["EMAIL_ENABLED"] = "false"
    
    print("✓ Environment configured for SQLite testing")
    print(f"  Database: {os.environ['SQLITE_PATH']}")


def clean_test_database():
    """Remove test database if it exists."""
    db_path = Path(os.environ.get("SQLITE_PATH", "./test_rag_fortress.db"))
    if db_path.exists():
        db_path.unlink()
        print(f"✓ Removed existing test database: {db_path}")


def run_migrations():
    """Run Alembic migrations."""
    print("\n" + "="*60)
    print("RUNNING MIGRATIONS")
    print("="*60)
    
    # Create alembic config
    alembic_cfg = Config("alembic.ini")
    
    # Get current database URL from settings
    from app.config.database_settings import DatabaseSettings
    db_settings = DatabaseSettings()
    db_url = db_settings._get_sync_database_url()
    
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    print(f"Database URL: {db_url}")
    
    try:
        # Run upgrade to head
        command.upgrade(alembic_cfg, "head")
        print("\n✓ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_schema():
    """Verify database schema was created correctly."""
    print("\n" + "="*60)
    print("VERIFYING SCHEMA")
    print("="*60)
    
    from app.config.database_settings import DatabaseSettings
    db_settings = DatabaseSettings()
    db_url = db_settings._get_sync_database_url()
    
    engine = create_engine(db_url)
    inspector = inspect(engine)
    
    # Expected tables
    expected_tables = [
        'users',
        'roles',
        'permissions',
        'user_roles',
        'role_permissions',
        'departments',
        'user_permissions',
        'permission_overrides',
        'user_invitations',
        'file_uploads',
        'conversations',
        'messages',
        'user_profiles',
        'application_settings',
        'activity_logs',
    ]
    
    existing_tables = inspector.get_table_names()
    print(f"\nFound {len(existing_tables)} tables:")
    for table in sorted(existing_tables):
        print(f"  - {table}")
    
    # Check for missing tables
    missing_tables = set(expected_tables) - set(existing_tables)
    if missing_tables:
        print(f"\n⚠ Missing tables: {missing_tables}")
        return False
    
    # Verify permission_overrides has new columns
    print("\n" + "-"*60)
    print("Checking permission_overrides table columns:")
    print("-"*60)
    
    columns = inspector.get_columns('permission_overrides')
    column_names = {col['name'] for col in columns}
    
    expected_new_columns = {
        'status',
        'approver_id',
        'approval_notes',
        'decided_at',
        'trigger_query',
        'trigger_file_id',
        'auto_escalated',
        'escalated_at'
    }
    
    for col_name in sorted(column_names):
        is_new = '(NEW)' if col_name in expected_new_columns else ''
        print(f"  - {col_name} {is_new}")
    
    missing_columns = expected_new_columns - column_names
    if missing_columns:
        print(f"\n✗ Missing columns: {missing_columns}")
        return False
    
    print("\n✓ All expected columns present")
    
    # Check indexes
    print("\n" + "-"*60)
    print("Checking permission_overrides indexes:")
    print("-"*60)
    
    indexes = inspector.get_indexes('permission_overrides')
    print(f"Found {len(indexes)} indexes:")
    for idx in indexes:
        print(f"  - {idx['name']}: {idx['column_names']}")
    
    engine.dispose()
    print("\n✓ Schema verification passed")
    return True


async def run_seeders():
    """Run database seeders."""
    print("\n" + "="*60)
    print("RUNNING SEEDERS")
    print("="*60)
    
    try:
        from app.core.database import DatabaseManager
        from app.config.settings import DatabaseSettings
        from app.seeders.roles_permissions import RolesPermissionsSeeder
        
        # Create database settings
        db_settings = DatabaseSettings()
        
        # Initialize database
        db_manager = DatabaseManager(db_settings)
        await db_manager.create_async_engine()
        
        # Get session factory
        session_factory = db_manager.get_session_factory()
        
        # Run seeder
        async with session_factory() as session:
            print("\n1. Seeding roles and permissions...")
            seeder = RolesPermissionsSeeder()
            await seeder.run(session)
            await session.commit()
            print("   ✓ Roles and permissions seeded")
        
        await db_manager.close_connection()
        
        print("\n✓ All seeders completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Seeder failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_data():
    """Verify seeded data exists."""
    print("\n" + "="*60)
    print("VERIFYING SEEDED DATA")
    print("="*60)
    
    from app.config.database_settings import DatabaseSettings
    db_settings = DatabaseSettings()
    db_url = db_settings._get_sync_database_url()
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check roles
        result = session.execute(text("SELECT COUNT(*) as count FROM roles"))
        roles_count = result.scalar()
        print(f"Roles: {roles_count}")
        
        if roles_count == 0:
            print("✗ No roles found")
            return False
        
        # Check permissions
        result = session.execute(text("SELECT COUNT(*) as count FROM permissions"))
        perms_count = result.scalar()
        print(f"Permissions: {perms_count}")
        
        if perms_count == 0:
            print("✗ No permissions found")
            return False
        
        # Check role_permissions (optional - basic seeder doesn't create these)
        result = session.execute(text("SELECT COUNT(*) as count FROM role_permissions"))
        role_perms_count = result.scalar()
        print(f"Role-Permission mappings: {role_perms_count} (optional)")
        
        print("\n✓ Data verification passed")
        return True
        
    except Exception as e:
        print(f"\n✗ Data verification failed: {e}")
        return False
    finally:
        session.close()
        engine.dispose()


async def test_permission_override_operations():
    """Test creating permission override requests."""
    print("\n" + "="*60)
    print("TESTING PERMISSION OVERRIDE OPERATIONS")
    print("="*60)
    
    try:
        from app.core.database import DatabaseManager
        from app.config.settings import DatabaseSettings
        from app.models.user import User
        from app.models.permission_override import PermissionOverride, OverrideStatus, OverrideType
        from app.models.user_permission import UserPermission, PermissionLevel
        from datetime import datetime, timezone, timedelta
        
        # Initialize database
        db_settings = DatabaseSettings()
        db_manager = DatabaseManager(db_settings)
        await db_manager.create_async_engine()
        session_factory = db_manager.get_session_factory()
        
        async with session_factory() as session:
            # Create a test user
            print("\n1. Creating test user...")
            test_user = User(
                username="testuser",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                password_hash="test_hash"
            )
            session.add(test_user)
            await session.flush()
            
            # Create user permission
            user_perm = UserPermission(
                user_id=test_user.id,
                org_level_permission=PermissionLevel.GENERAL.value
            )
            session.add(user_perm)
            await session.flush()
            print(f"   ✓ User created with ID: {test_user.id}")
            
            # Create a permission override request
            print("\n2. Creating permission override request...")
            override = PermissionOverride(
                user_id=test_user.id,
                override_type=OverrideType.ORG_WIDE.value,
                override_permission_level=PermissionLevel.CONFIDENTIAL.value,
                reason="Testing override request system",
                valid_from=datetime.now(timezone.utc),
                valid_until=datetime.now(timezone.utc) + timedelta(days=1),
                created_by_id=test_user.id,
                status=OverrideStatus.PENDING.value,
                is_active=False,
                trigger_query="test query for restricted content",
                auto_escalated=False
            )
            session.add(override)
            await session.commit()
            print(f"   ✓ Override request created with ID: {override.id}")
            
            # Verify the override was created
            print("\n3. Verifying override request...")
            from sqlalchemy import select
            result = await session.execute(
                select(PermissionOverride).where(PermissionOverride.id == override.id)
            )
            loaded_override = result.scalar_one()
            
            assert loaded_override.status == OverrideStatus.PENDING.value
            assert loaded_override.trigger_query == "test query for restricted content"
            assert loaded_override.auto_escalated == False
            print("   ✓ Override request verified")
            
            # Test approval workflow
            print("\n4. Testing approval workflow...")
            loaded_override.status = OverrideStatus.APPROVED.value
            loaded_override.is_active = True
            loaded_override.approver_id = test_user.id
            loaded_override.approval_notes = "Approved for testing"
            loaded_override.decided_at = datetime.now(timezone.utc)
            await session.commit()
            print("   ✓ Override approved successfully")
            
            # Test auto-escalation flag
            print("\n5. Testing auto-escalation...")
            loaded_override.auto_escalated = True
            loaded_override.escalated_at = datetime.now(timezone.utc)
            await session.commit()
            print("   ✓ Auto-escalation flag updated")
        
        await db_manager.close_connection()
        
        print("\n✓ All permission override operations completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Permission override test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description='Test SQLite migrations and seeders')
    parser.add_argument('--clean', action='store_true', help='Remove test database before running')
    args = parser.parse_args()
    
    print("="*60)
    print("SQLite Migration Test Suite")
    print("="*60)
    
    # Setup
    setup_test_env()
    
    if args.clean:
        clean_test_database()
    
    # Run tests
    success = True
    
    # 1. Run migrations
    if not run_migrations():
        print("\n✗ MIGRATION TEST FAILED")
        return 1
    
    # 2. Verify schema
    if not verify_schema():
        print("\n✗ SCHEMA VERIFICATION FAILED")
        return 1
    
    # 3. Run seeders
    if not asyncio.run(run_seeders()):
        print("\n✗ SEEDER TEST FAILED")
        return 1
    
    # 4. Verify data
    if not verify_data():
        print("\n✗ DATA VERIFICATION FAILED")
        return 1
    
    # 5. Test permission override operations
    if not asyncio.run(test_permission_override_operations()):
        print("\n✗ PERMISSION OVERRIDE TEST FAILED")
        return 1
    
    # Success
    print("\n" + "="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60)
    print("\nSQLite is fully compatible with the migration system.")
    print(f"Test database: {os.environ['SQLITE_PATH']}")
    print("\nYou can now safely use SQLite as your database provider.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
