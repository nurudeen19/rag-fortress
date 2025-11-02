"""
Simplified vector store base class.
Focus: Store chunks with embeddings. That's it.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class VectorStoreBase(ABC):
    """
    Simplified vector store interface.
    Only what we need: initialize, insert chunks, close.
    """
    
    def __init__(self, collection_name: str, **kwargs):
        self.collection_name = collection_name
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize connection and create collection if needed."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close connection and cleanup."""
        pass
    
    @abstractmethod
    async def insert_chunks(
        self,
        contents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        """
        Insert chunks with their embeddings.
        
        Args:
            contents: List of text contents
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts
            
        Returns:
            bool: True if successful
        """
        pass
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
