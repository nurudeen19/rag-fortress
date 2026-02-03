#!/usr/bin/env python3
"""
Database migration and management CLI script.

This script provides commands for managing database migrations using Alembic.
Usage:
    python migrate.py upgrade head       # Apply all pending migrations
    python migrate.py downgrade -1       # Rollback last migration
    python migrate.py current            # Show current migration
    python migrate.py history            # Show migration history
    python migrate.py revision -m "message"  # Create new migration
"""
import sys
from pathlib import Path
from click import command, argument, option
from alembic.config import Config
from alembic import command as alembic_command
from app.config.database_settings import DatabaseSettings

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
ALEMBIC_INI = SCRIPT_DIR / "alembic.ini"


def get_alembic_config() -> Config:
    """Get Alembic configuration."""
    if not ALEMBIC_INI.exists():
        raise FileNotFoundError(f"alembic.ini not found at {ALEMBIC_INI}")
    
    config = Config(str(ALEMBIC_INI))
    
    # Set the database URL from settings
    settings = DatabaseSettings()
    db_url = settings._get_sync_database_url()
    config.set_main_option("sqlalchemy.url", db_url)
    
    return config


@command()
@argument("command")
@option("-m", "--message", default="", help="Migration message (for 'revision' command)")
def main(command: str, message: str):
    """Database migration CLI tool."""
    
    try:
        config = get_alembic_config()
        
        if command == "upgrade":
            revision = "head"
            print(f"Upgrading database to {revision}...")
            alembic_command.upgrade(config, revision)
            print("✓ Database upgraded successfully")
        
        elif command == "downgrade":
            revision = "-1"
            print(f"Downgrading database by {revision}...")
            alembic_command.downgrade(config, revision)
            print("✓ Database downgraded successfully")
        
        elif command == "current":
            print("Current database revision:")
            alembic_command.current(config)
        
        elif command == "history":
            print("Migration history:")
            alembic_command.history(config)
        
        elif command == "revision":
            if not message:
                print("Error: --message/-m is required for 'revision' command")
                sys.exit(1)
            print(f"Creating new migration: {message}")
            alembic_command.revision(config, autogenerate=False, message=message)
            print("✓ Migration created successfully")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: upgrade, downgrade, current, history, revision")
            sys.exit(1)
    
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
