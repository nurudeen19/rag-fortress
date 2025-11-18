#!/usr/bin/env python
"""Drop all tables in the database to start fresh."""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from app.config.database_settings import DatabaseSettings

# Explicitly load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

db = DatabaseSettings()
print(f"Using database provider: {db.DATABASE_PROVIDER}")
print(f"Database URL: {db._get_sync_database_url()[:50]}...")

engine = create_engine(db._get_sync_database_url())

# Get all tables
inspector = inspect(engine)
tables = inspector.get_table_names()

with engine.connect() as conn:
    # Handle MySQL foreign key checks
    if 'mysql' in db._get_sync_database_url().lower():
        print("Disabling foreign key checks for MySQL...")
        conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
    
    # Drop all tables
    for table in tables:
        print(f"Dropping table: {table}")
        conn.execute(text(f'DROP TABLE IF EXISTS `{table}`'))
    
    # Re-enable foreign key checks for MySQL
    if 'mysql' in db._get_sync_database_url().lower():
        print("Re-enabling foreign key checks...")
        conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
    
    conn.commit()

print("\nAll tables dropped successfully!")
