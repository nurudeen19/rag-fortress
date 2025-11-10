"""Base seeder class for database seeding operations."""

from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession


class BaseSeed(ABC):
    """Abstract base class for all seeders."""
    
    name: str = "base_seeder"
    description: str = "Base seeder class"
    
    @abstractmethod
    async def run(self, session: AsyncSession) -> dict:
        """
        Run the seeder.
        
        Args:
            session: AsyncSession for database operations
            
        Returns:
            Dict with results: {"success": bool, "message": str, ...}
        """
        pass
