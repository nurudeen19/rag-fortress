"""
Retriever service for querying the vector store.
Handles document retrieval with optional filtering, re-ranking, and processing.
"""

from typing import List, Optional, Dict, Any
from langchain_core.documents import Document

from app.core.vector_store_factory import get_retriever
from app.core import get_logger


logger = get_logger(__name__)


class RetrieverService:
    """
    Service for retrieving documents from the vector store.
    
    Provides query methods with optional filtering and processing.
    Can be extended with features like hybrid search, re-ranking, etc.
    """
    
    def __init__(self):
        """Initialize retriever service."""
        self.retriever = get_retriever()
    
    def query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Query the vector store and retrieve relevant documents.
        
        Args:
            query_text: The search query
            top_k: Number of results to return (overrides settings default)
            filters: Optional metadata filters (future feature)
            
        Returns:
            List[Document]: Retrieved documents with metadata
        """
        # Update top_k if provided
        if top_k is not None:
            self.retriever.search_kwargs = {"k": top_k}
        
        # TODO: Apply filters when implementing filtered search
        # This will require vector store-specific implementations
        
        # Retrieve documents
        docs = self.retriever.invoke(query_text)
        
        logger.info(
            f"Retrieved {len(docs)} documents for query: '{query_text[:50]}...'"
        )
        
        return docs
    
    def query_with_scores(
        self,
        query_text: str,
        top_k: Optional[int] = None
    ) -> List[tuple[Document, float]]:
        """
        Query with similarity scores.
        
        Args:
            query_text: The search query
            top_k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
            
        Note:
            Not all vector stores support score retrieval.
            Falls back to regular query if unavailable.
        """
        # Get vector store from retriever
        vector_store = self.retriever.vectorstore
        
        # Try to get documents with scores
        try:
            k = top_k or self.retriever.search_kwargs.get("k", 5)
            results = vector_store.similarity_search_with_score(
                query_text,
                k=k
            )
            
            logger.info(
                f"Retrieved {len(results)} documents with scores "
                f"for query: '{query_text[:50]}...'"
            )
            
            return results
        
        except (AttributeError, NotImplementedError):
            # Fallback to regular query if scores not supported
            logger.warning(
                "Vector store does not support similarity scores, "
                "falling back to regular query"
            )
            docs = self.query(query_text, top_k=top_k)
            # Return with None scores
            return [(doc, None) for doc in docs]
    
    def format_results(
        self,
        documents: List[Document],
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Format retrieved documents for API responses.
        
        Args:
            documents: Retrieved documents
            include_metadata: Whether to include full metadata
            
        Returns:
            List of formatted document dictionaries
        """
        results = []
        
        for doc in documents:
            result = {
                "content": doc.page_content,
            }
            
            if include_metadata:
                result["metadata"] = doc.metadata
            else:
                # Include only essential metadata
                result["source"] = doc.metadata.get("source")
                result["chunk_index"] = doc.metadata.get("chunk_index")
            
            results.append(result)
        
        return results


# Singleton instance
_retriever_service: Optional[RetrieverService] = None


def get_retriever_service() -> RetrieverService:
    """
    Get retriever service instance.
    Creates singleton instance on first call.
    
    Returns:
        RetrieverService: Retriever service instance
    """
    global _retriever_service
    
    if _retriever_service is None:
        _retriever_service = RetrieverService()
        logger.info("✓ Retriever service initialized")
    
    return _retriever_service
