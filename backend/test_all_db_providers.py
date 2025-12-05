#!/usr/bin/env python
"""
Multi-Database Provider Migration Test Script

Tests that migrations work correctly across SQLite, MySQL, and PostgreSQL.
This ensures true database provider agnosticism.

Usage:
    python test_all_db_providers.py [--providers sqlite mysql postgresql]
    python test_all_db_providers.py --providers sqlite  # Test only SQLite
    python test_all_db_providers.py                     # Test all providers

Requirements:
    - MySQL server running on localhost:3306 with root access
    - PostgreSQL server running on localhost:5432 with postgres user
    - Both servers should allow creating databases named: test_rag_fortress_*
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
import argparse

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config


class DatabaseProviderTest:
    """Test runner for a specific database provider."""
    
    def __init__(self, provider: str, config: Dict[str, str]):
        self.provider = provider
        self.config = config
        self.test_db_name = f"test_rag_fortress_{provider}"
        self.success = False
        self.error_message = None
    
    def setup_environment(self):
        """Configure environment variables for the provider."""
        os.environ["DATABASE_PROVIDER"] = self.provider
        os.environ["ENVIRONMENT"] = "development"
        os.environ["CACHE_ENABLED"] = "false"
        os.environ["EMAIL_ENABLED"] = "false"
        
        # Provider-specific configuration
        for key, value in self.config.items():
            os.environ[key] = value
        
        print(f"✓ Environment configured for {self.provider.upper()}")
        for key, value in self.config.items():
            if "PASSWORD" not in key and "KEY" not in key:
                print(f"  {key}: {value}")
    
    def clean_database(self):
        """Drop and recreate the test database."""
        try:
            if self.provider == "sqlite":
                db_path = Path(self.config["SQLITE_PATH"])
                if db_path.exists():
                    db_path.unlink()
                    print(f"✓ Removed existing SQLite database: {db_path}")
            
            elif self.provider == "mysql":
                # Connect to MySQL server without database
                engine = create_engine(
                    f"mysql+pymysql://{self.config['DB_USER']}:{self.config.get('DB_PASSWORD', '')}@"
                    f"{self.config['DB_HOST']}:{self.config['DB_PORT']}/",
                    isolation_level="AUTOCOMMIT"
                )
                with engine.connect() as conn:
                    # Drop database if exists
                    conn.execute(text(f"DROP DATABASE IF EXISTS {self.test_db_name}"))
                    # Create fresh database
                    conn.execute(text(f"CREATE DATABASE {self.test_db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                print(f"✓ Created clean MySQL database: {self.test_db_name}")
            
            elif self.provider == "postgresql":
                # Connect to PostgreSQL server without database
                engine = create_engine(
                    f"postgresql+psycopg2://{self.config['DB_USER']}:{self.config.get('DB_PASSWORD', '')}@"
                    f"{self.config['DB_HOST']}:{self.config['DB_PORT']}/postgres",
                    isolation_level="AUTOCOMMIT"
                )
                with engine.connect() as conn:
                    # Terminate existing connections
                    conn.execute(text(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{self.test_db_name}'
                        AND pid <> pg_backend_pid()
                    """))
                    # Drop database if exists
                    conn.execute(text(f"DROP DATABASE IF EXISTS {self.test_db_name}"))
                    # Create fresh database
                    conn.execute(text(f"CREATE DATABASE {self.test_db_name}"))
                print(f"✓ Created clean PostgreSQL database: {self.test_db_name}")
            
            return True
        except Exception as e:
            print(f"✗ Failed to clean database: {e}")
            self.error_message = f"Database cleanup failed: {e}"
            return False
    
    def run_migrations(self) -> bool:
        """Run Alembic migrations."""
        try:
            print(f"\nRunning migrations for {self.provider.upper()}...")
            
            # Get database URL from settings
            from app.config.settings import DatabaseSettings
            db_settings = DatabaseSettings()
            db_url = db_settings._get_sync_database_url()
            
            print(f"Database URL: {db_url.split('@')[-1]}")  # Hide credentials
            
            # Configure Alembic
            alembic_cfg = Config(str(backend_path / "alembic.ini"))
            alembic_cfg.set_main_option("script_location", str(backend_path / "migrations"))
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)
            
            # Run migrations
            command.upgrade(alembic_cfg, "head")
            
            print(f"✓ Migrations completed successfully for {self.provider.upper()}")
            return True
            
        except Exception as e:
            print(f"✗ Migration failed for {self.provider.upper()}: {e}")
            self.error_message = f"Migration failed: {e}"
            import traceback
            traceback.print_exc()
            return False
    
    def verify_schema(self) -> bool:
        """Verify database schema was created correctly."""
        try:
            from app.config.settings import DatabaseSettings
            db_settings = DatabaseSettings()
            db_url = db_settings._get_sync_database_url()
            
            engine = create_engine(db_url)
            inspector = inspect(engine)
            
            # Get all tables
            tables = inspector.get_table_names()
            print(f"\n✓ Found {len(tables)} tables in {self.provider.upper()}")
            
            # Verify critical tables exist
            critical_tables = [
                'users', 'roles', 'permissions', 'permission_overrides',
                'file_uploads', 'departments', 'user_invitations'
            ]
            
            missing_tables = [t for t in critical_tables if t not in tables]
            if missing_tables:
                print(f"✗ Missing critical tables: {missing_tables}")
                self.error_message = f"Missing tables: {missing_tables}"
                return False
            
            # Verify permission_overrides has approval workflow columns
            columns = [col['name'] for col in inspector.get_columns('permission_overrides')]
            required_columns = ['status', 'approver_id', 'approval_notes', 'decided_at']
            missing_columns = [c for c in required_columns if c not in columns]
            
            if missing_columns:
                print(f"✗ Missing approval workflow columns: {missing_columns}")
                self.error_message = f"Missing columns: {missing_columns}"
                return False
            
            print(f"✓ Schema verification passed for {self.provider.upper()}")
            return True
            
        except Exception as e:
            print(f"✗ Schema verification failed for {self.provider.upper()}: {e}")
            self.error_message = f"Schema verification failed: {e}"
            return False
    
    def run_seeders_sync(self) -> bool:
        """Run database seeders using synchronous approach."""
        try:
            print(f"\nRunning seeders for {self.provider.upper()}...")
            
            from app.config.settings import DatabaseSettings
            db_settings = DatabaseSettings()
            db_url = db_settings._get_sync_database_url()
            
            engine = create_engine(db_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                # Create roles manually for testing
                roles_data = [
                    {"name": "admin", "description": "Administrator"},
                    {"name": "manager", "description": "Manager"},
                    {"name": "user", "description": "User"},
                ]
                
                # Use CURRENT_TIMESTAMP for timestamps (works on all databases)
                # PostgreSQL requires TRUE/FALSE for booleans, MySQL/SQLite accept 1/0
                bool_true = "TRUE" if self.provider == 'postgresql' else "1"
                
                for role_data in roles_data:
                    result = session.execute(text(f"SELECT COUNT(*) FROM roles WHERE name = '{role_data['name']}'"))
                    if result.scalar() == 0:
                        if self.provider == 'sqlite':
                            session.execute(text(
                                f"INSERT INTO roles (name, description, is_system, created_at, updated_at) "
                                f"VALUES ('{role_data['name']}', '{role_data['description']}', {bool_true}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                            ))
                        else:
                            session.execute(text(
                                f"INSERT INTO roles (name, description, is_system, created_at, updated_at) "
                                f"VALUES ('{role_data['name']}', '{role_data['description']}', {bool_true}, NOW(), NOW())"
                            ))
                
                # Create permissions manually
                perms_data = [
                    {"code": "user:create", "description": "Create users", "resource": "user", "action": "create"},
                    {"code": "user:read", "description": "Read users", "resource": "user", "action": "read"},
                    {"code": "file:upload", "description": "Upload files", "resource": "file", "action": "upload"},
                    {"code": "file:read", "description": "Read files", "resource": "file", "action": "read"},
                    {"code": "settings:update", "description": "Update settings", "resource": "settings", "action": "update"},
                ]
                
                for perm_data in perms_data:
                    result = session.execute(text(f"SELECT COUNT(*) FROM permissions WHERE code = '{perm_data['code']}'"))
                    if result.scalar() == 0:
                        if self.provider == 'sqlite':
                            session.execute(text(
                                f"INSERT INTO permissions (code, description, resource, action, created_at, updated_at) "
                                f"VALUES ('{perm_data['code']}', '{perm_data['description']}', '{perm_data['resource']}', '{perm_data['action']}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                            ))
                        else:
                            session.execute(text(
                                f"INSERT INTO permissions (code, description, resource, action, created_at, updated_at) "
                                f"VALUES ('{perm_data['code']}', '{perm_data['description']}', '{perm_data['resource']}', '{perm_data['action']}', NOW(), NOW())"
                            ))
                
                session.commit()
                session.close()
                
                print(f"✓ Seeders completed for {self.provider.upper()}")
                return True
                
            except Exception as e:
                session.rollback()
                session.close()
                raise
            
        except Exception as e:
            print(f"✗ Seeder failed for {self.provider.upper()}: {e}")
            self.error_message = f"Seeder failed: {e}"
            import traceback
            traceback.print_exc()
            return False
    
    def verify_data(self) -> bool:
        """Verify seeded data exists."""
        try:
            from app.config.settings import DatabaseSettings
            db_settings = DatabaseSettings()
            db_url = db_settings._get_sync_database_url()
            
            engine = create_engine(db_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Check roles
            result = session.execute(text("SELECT COUNT(*) as count FROM roles"))
            roles_count = result.scalar()
            
            # Check permissions
            result = session.execute(text("SELECT COUNT(*) as count FROM permissions"))
            perms_count = result.scalar()
            
            session.close()
            
            if roles_count < 3:  # Should have at least admin, manager, user
                print(f"✗ Insufficient roles: {roles_count}")
                self.error_message = f"Only {roles_count} roles found"
                return False
            
            if perms_count < 5:  # Should have multiple permissions
                print(f"✗ Insufficient permissions: {perms_count}")
                self.error_message = f"Only {perms_count} permissions found"
                return False
            
            print(f"✓ Data verification passed for {self.provider.upper()}")
            print(f"  Roles: {roles_count}, Permissions: {perms_count}")
            return True
            
        except Exception as e:
            print(f"✗ Data verification failed for {self.provider.upper()}: {e}")
            self.error_message = f"Data verification failed: {e}"
            return False
    
    def run_all_tests(self) -> bool:
        """Run complete test suite for this provider."""
        print("\n" + "="*80)
        print(f"TESTING {self.provider.upper()}")
        print("="*80)
        
        try:
            # Setup environment
            self.setup_environment()
            
            # Clean database
            if not self.clean_database():
                return False
            
            # Run migrations
            if not self.run_migrations():
                return False
            
            # Verify schema
            if not self.verify_schema():
                return False
            
            # Run seeders
            if not self.run_seeders_sync():
                return False
            
            # Verify data
            if not self.verify_data():
                return False
            
            self.success = True
            print(f"\n✓ ALL TESTS PASSED FOR {self.provider.upper()}")
            return True
            
        except Exception as e:
            print(f"\n✗ UNEXPECTED ERROR IN {self.provider.upper()}: {e}")
            self.error_message = str(e)
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description='Test migrations across multiple database providers'
    )
    parser.add_argument(
        '--providers',
        nargs='+',
        choices=['sqlite', 'mysql', 'postgresql'],
        default=['sqlite', 'mysql', 'postgresql'],
        help='Database providers to test (default: all)'
    )
    args = parser.parse_args()
    
    # Provider configurations
    provider_configs = {
        'sqlite': {
            'SQLITE_PATH': './test_rag_fortress_sqlite.db',
            'SQLITE_CHECK_SAME_THREAD': 'False'
        },
        'mysql': {
            'DB_HOST': 'localhost',
            'DB_PORT': '3306',
            'DB_USER': 'root',
            'DB_PASSWORD': '',
            'DB_NAME': 'test_rag_fortress_mysql',
            'MYSQL_CHARSET': 'utf8mb4'
        },
        'postgresql': {
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_USER': 'postgres',
            'DB_PASSWORD': '',
            'DB_NAME': 'test_rag_fortress_postgresql',
            'POSTGRES_SSL_MODE': 'prefer'
        }
    }
    
    print("="*80)
    print("MULTI-DATABASE PROVIDER MIGRATION TEST")
    print("="*80)
    print(f"Testing providers: {', '.join(p.upper() for p in args.providers)}")
    print()
    
    # Run tests for each provider
    results = {}
    for provider in args.providers:
        if provider not in provider_configs:
            print(f"✗ Unknown provider: {provider}")
            continue
        
        test = DatabaseProviderTest(provider, provider_configs[provider])
        results[provider] = test.run_all_tests()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for provider, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{provider.upper():15} {status}")
    
    print()
    print(f"Results: {success_count}/{total_count} providers passed")
    
    if success_count == total_count:
        print("\n🎉 ALL DATABASE PROVIDERS ARE COMPATIBLE!")
        print("The migration system is truly provider-agnostic.")
        return 0
    else:
        print(f"\n⚠️  {total_count - success_count} provider(s) failed")
        print("Check the error messages above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
