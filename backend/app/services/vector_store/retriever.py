"""
Retriever service for querying the vector store.
Handles document retrieval with optional filtering, re-ranking, and processing.
"""

from typing import List, Optional, Dict, Any
from langchain_core.documents import Document

from app.core.vector_store_factory import get_retriever
from app.core import get_logger, get_settings
from app.models.user_permission import PermissionLevel


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
        self.settings = get_settings()
    
    def _filter_by_security(
        self,
        documents: List[Document],
        user_security_level: int,
        user_department_id: Optional[int] = None
    ) -> List[Document]:
        """
        Filter documents based on user's security clearance and department access.
        
        Access rules:
        1. User can access documents at their clearance level or below
        2. If document is department-only, user must be in that department
        3. If user has no department, they can only access non-department documents
        
        Args:
            documents: Retrieved documents from vector store
            user_security_level: User's clearance level (PermissionLevel enum value)
            user_department_id: User's department ID (None if not assigned)
            
        Returns:
            Filtered list of documents the user can access
        """
        filtered_docs = []
        
        for doc in documents:
            metadata = doc.metadata
            
            # Check security clearance level
            doc_security_level = metadata.get("security_level", "GENERAL")
            try:
                doc_level_value = PermissionLevel[doc_security_level].value
            except KeyError:
                logger.warning(f"Invalid security level '{doc_security_level}' in document metadata")
                continue
            
            # User must have sufficient clearance
            if user_security_level < doc_level_value:
                logger.debug(
                    f"Document blocked: user_level={user_security_level} < doc_level={doc_level_value}"
                )
                continue
            
            # Check department access
            is_department_only = metadata.get("is_department_only", False)
            doc_department_id = metadata.get("department_id")
            
            if is_department_only:
                # Department-only document - user must be in the same department
                if user_department_id is None:
                    logger.debug(f"Document blocked: department-only but user has no department")
                    continue
                if doc_department_id != user_department_id:
                    logger.debug(
                        f"Document blocked: dept mismatch (user={user_department_id}, doc={doc_department_id})"
                    )
                    continue
            
            # Document passes all checks
            filtered_docs.append(doc)
        
        return filtered_docs
    
    def query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        user_security_level: Optional[int] = None,
        user_department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store and retrieve relevant documents with security filtering.
        
        Uses POST-FILTERING: Retrieves documents first, then filters by user access.
        Returns clear error messages when user lacks access to retrieved documents.
        
        Args:
            query_text: The search query
            top_k: Number of results to return (overrides settings default)
            filters: Optional metadata filters (future feature)
            user_security_level: User's clearance level (PermissionLevel enum value)
            user_department_id: User's department ID for department-only filtering
            
        Returns:
            Dict with:
                - success (bool): Whether retrieval succeeded
                - context (List[Document]): Retrieved documents if successful
                - count (int): Number of documents returned
                - error (str): Error type if failed (e.g., 'insufficient_clearance', 'no_access')
                - message (str): Human-readable error message if failed
        """
        try:
            k = top_k or self.retriever.search_kwargs.get("k", 5)
            
            # Query vector store (no pre-filtering)
            self.retriever.search_kwargs = {"k": k}
            if filters:
                # Apply any custom metadata filters if provided
                self.retriever.search_kwargs["filter"] = filters
            
            docs = self.retriever.invoke(query_text)
            
            logger.info(f"Retrieved {len(docs)} documents for query: '{query_text[:50]}...'")
            
            # Apply security filtering if user credentials provided
            if user_security_level is not None:
                logger.debug(
                    f"Filtering documents for user_level={PermissionLevel(user_security_level).name}, "
                    f"dept={user_department_id}"
                )
                
                filtered_docs = self._filter_by_security(
                    docs,
                    user_security_level,
                    user_department_id
                )
                
                # Check if user has access to any documents
                if len(docs) > 0 and len(filtered_docs) == 0:
                    # Documents were found but user can't access any
                    logger.warning(
                        f"User with level={user_security_level}, dept={user_department_id} "
                        f"has no access to {len(docs)} retrieved documents"
                    )
                    return {
                        "success": False,
                        "error": "insufficient_clearance",
                        "message": "You do not have sufficient clearance to access the retrieved documents.",
                        "count": 0
                    }
                
                docs = filtered_docs
                logger.info(f"After security filtering: {len(docs)} accessible documents")
            
            return {
                "success": True,
                "context": docs,
                "count": len(docs)
            }
        
        except Exception as e:
            logger.error(f"Error querying vector store: {e}", exc_info=True)
            return {
                "success": False,
                "error": "retrieval_error",
                "message": f"Failed to retrieve documents: {str(e)}",
                "count": 0
            }

    def query_with_scores(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        user_security_level: Optional[int] = None,
        user_department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query with similarity scores and security POST-filtering.
        
        Retrieves documents with scores, then filters by user access.
        
        Args:
            query_text: The search query
            top_k: Number of results to return
            user_security_level: User's clearance level (PermissionLevel enum value)
            user_department_id: User's department ID for department-only filtering
            
        Returns:
            Dict with:
                - success (bool): Whether retrieval succeeded
                - context (List[tuple[Document, float]]): Retrieved (document, score) tuples
                - count (int): Number of documents returned
                - error (str): Error type if failed
                - message (str): Human-readable error message if failed
            
        Note:
            Not all vector stores support score retrieval.
            Falls back to regular query if unavailable.
        """
        try:
            # Get vector store from retriever
            vector_store = self.retriever.vectorstore
            k = top_k or self.retriever.search_kwargs.get("k", 5)
            
            # Try to get documents with scores
            try:
                results = vector_store.similarity_search_with_score(query_text, k=k)
                
                logger.info(f"Retrieved {len(results)} documents with scores")
                
                # Apply security filtering if user credentials provided
                if user_security_level is not None:
                    # Extract documents for filtering
                    docs = [doc for doc, _ in results]
                    filtered_docs = self._filter_by_security(
                        docs,
                        user_security_level,
                        user_department_id
                    )
                    
                    # Check if user has access
                    if len(docs) > 0 and len(filtered_docs) == 0:
                        logger.warning(
                            f"User with level={user_security_level}, dept={user_department_id} "
                            f"has no access to {len(docs)} retrieved documents"
                        )
                        return {
                            "success": False,
                            "error": "insufficient_clearance",
                            "message": "You do not have sufficient clearance to access the retrieved documents.",
                            "count": 0
                        }
                    
                    # Rebuild results with only accessible documents
                    filtered_ids = {id(doc) for doc in filtered_docs}
                    results = [(doc, score) for doc, score in results if id(doc) in filtered_ids]
                    logger.info(f"After security filtering: {len(results)} accessible documents")
                
                return {
                    "success": True,
                    "context": results,
                    "count": len(results)
                }
            
            except (AttributeError, NotImplementedError):
                # Fallback to regular query if scores not supported
                logger.warning(
                    "Vector store does not support similarity scores, "
                    "falling back to regular query"
                )
                query_result = self.query(
                    query_text,
                    top_k=top_k,
                    user_security_level=user_security_level,
                    user_department_id=user_department_id
                )
                
                if not query_result["success"]:
                    return query_result
                
                # Add None scores to documents
                docs_with_scores = [(doc, None) for doc in query_result["context"]]
                return {
                    "success": True,
                    "context": docs_with_scores,
                    "count": len(docs_with_scores)
                }
        
        except Exception as e:
            logger.error(f"Error in query_with_scores: {e}", exc_info=True)
            return {
                "success": False,
                "error": "retrieval_error",
                "message": f"Failed to retrieve documents with scores: {str(e)}",
                "count": 0
            }
    
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
