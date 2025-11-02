"""
Simplified ChromaDB vector store.
"""

from typing import List, Dict, Any
from uuid import uuid4

try:
    import chromadb
except ImportError:
    chromadb = None

from app.services.vector_store.base import VectorStoreBase
from app.core.exceptions import VectorStoreError


class ChromaVectorStore(VectorStoreBase):
    """Simple ChromaDB implementation using persistent storage."""
    
    def __init__(
        self,
        collection_name: str,
        persist_directory: str,
        **kwargs
    ):
        super().__init__(collection_name, **kwargs)
        
        if chromadb is None:
            raise ImportError("chromadb not installed. Install with: pip install chromadb")
        
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
    
    async def initialize(self) -> None:
        """Initialize ChromaDB with persistent storage."""
        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            self._initialized = True
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize ChromaDB: {e}", provider="chroma")
    
    async def close(self) -> None:
        """Close connection."""
        self._initialized = False
    
    async def insert_chunks(
        self,
        contents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        """Insert chunks into ChromaDB."""
        if not self._initialized:
            raise VectorStoreError("ChromaDB not initialized", provider="chroma")
        
        if len(contents) != len(embeddings) != len(metadatas):
            raise ValueError("Contents, embeddings, and metadatas must have same length")
        
        try:
            # Generate IDs
            ids = [str(uuid4()) for _ in contents]
            
            # Insert into ChromaDB
            self.collection.add(
                ids=ids,
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            return True
            
        except Exception as e:
            raise VectorStoreError(f"Failed to insert chunks: {e}", provider="chroma")
