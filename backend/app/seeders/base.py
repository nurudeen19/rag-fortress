"""Base seeder class for database seeding operations."""

from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect
import logging

logger = logging.getLogger(__name__)


class BaseSeed(ABC):
    """Abstract base class for all seeders."""
    
    name: str = "base_seeder"
    description: str = "Base seeder class"
    required_tables: list = []  # Override in subclasses to specify required tables
    
    @abstractmethod
    async def run(self, session: AsyncSession) -> dict:
        """
        Run the seeder.
        
        Args:
            session: AsyncSession for database operations
            
        Returns:
            Dict with results: {"success": bool, "message": str, ...}
        """
    
    async def validate_tables_exist(self, session: AsyncSession) -> tuple:
        """
        Validate that all required tables exist in the database.
        
        Args:
            session: AsyncSession for database operations
            
        Returns:
            Tuple of (all_exist: bool, missing_tables: list)
        """
        if not self.required_tables:
            # No validation required if no tables specified
            return True, []
        
        try:
            # Get table names using engine.inspect with run_sync
            # run_sync passes the connection/session as first argument
            engine = session.get_bind()
            
            def _inspect_tables(sync_session):
                """Get table names (must be sync code). Gets sync session from run_sync."""
                inspector = inspect(engine)
                return inspector.get_table_names()
            
            # Execute synchronous inspection code
            existing_tables = await session.run_sync(_inspect_tables)
            
            missing_tables = [
                table for table in self.required_tables 
                if table not in existing_tables
            ]
            
            all_exist = len(missing_tables) == 0
            return all_exist, missing_tables
            
        except Exception as e:
            logger.error(f"Error validating tables: {e}")
            return False, self.required_tables
