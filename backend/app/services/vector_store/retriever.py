"""
Retriever service for querying the vector store.
Handles adaptive document retrieval with quality-based top-k adjustment and reranking.
Includes caching and query preprocessing.
"""

from typing import List, Optional, Dict, Any, Tuple
from langchain_core.documents import Document
import hashlib
import json

from app.core.vector_store_factory import get_retriever
from app.core import get_logger
from app.core.cache import get_cache
from app.config.settings import settings
from app.models.user_permission import PermissionLevel
from app.services.vector_store.reranker import get_reranker_service
from app.utils.text_processing import preprocess_query


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
        self.settings = settings
        self.reranker = None
        if self.settings.app_settings.ENABLE_RERANKER:
            self.reranker = get_reranker_service()
        self.cache = get_cache()
    
    def _generate_cache_key(
        self,
        query_text: str,
        user_security_level: Optional[int],
        user_department_id: Optional[int],
        user_department_security_level: Optional[int]
    ) -> str:
        """
        Generate cache key for a query based on:
        - The cleaned query
        - User security level (org-wide)
        - Department context (whether query is dept-scoped or org-wide)
        
        This ensures different users with different clearances don't share cached results.
        """
        # Determine scope: if user has department restrictions, include dept_id; otherwise org-wide
        scope = "dept" if (user_department_id and user_department_security_level) else "org"
        
        key_data = {
            "query": query_text,  # Already preprocessed by caller
            "scope": scope,
            "org_level": user_security_level,
            "dept_id": user_department_id if scope == "dept" else None,
            "dept_level": user_department_security_level if scope == "dept" else None,
        }
        
        serialized = json.dumps(key_data, sort_keys=True, default=str)
        return f"retrieval:{hashlib.md5(serialized.encode()).hexdigest()}"
    
    def _filter_by_security(
        self,
        documents: List[Document],
        user_security_level: int,
        user_department_id: Optional[int] = None,
        user_department_security_level: Optional[int] = None
    ) -> Tuple[List[Document], Optional[int]]:
        """
        Filter documents based on user's security clearance and department access.
        
        Access rules:
        1. For org-wide documents: User can access at their org clearance level or below
        2. For department-only documents: User must be in that department AND meet department security level
        3. If user has no department, they can only access non-department documents
        
        Args:
            documents: Retrieved documents from vector store
            user_security_level: User's org-wide clearance level (PermissionLevel enum value)
            user_department_id: User's department ID (None if not assigned)
            user_department_security_level: User's department-specific clearance level (None if not assigned)
            
        Returns:
            Tuple of (filtered documents, max security level accessed)
        """
        filtered_docs: List[Document] = []
        max_security_level: Optional[int] = None
        
        for doc in documents:
            metadata = doc.metadata
            
            # Check security clearance level
            doc_security_level = metadata.get("security_level", "GENERAL")
            try:
                # Handle both string enum names and integer values
                if isinstance(doc_security_level, int):
                    doc_level_value = doc_security_level
                elif isinstance(doc_security_level, str) and doc_security_level.isdigit():
                    doc_level_value = int(doc_security_level)
                else:
                    doc_level_value = PermissionLevel[doc_security_level].value
            except (KeyError, ValueError):
                logger.warning(f"Invalid security level '{doc_security_level}' in document metadata")
                continue
            
            # Check department access first
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
                
                # For department-only docs, use department security level
                if user_department_security_level is None:
                    logger.debug(f"Document blocked: department-only but user has no department security level")
                    continue
                if user_department_security_level < doc_level_value:
                    logger.debug(
                        f"Document blocked: user_dept_level={user_department_security_level} < doc_level={doc_level_value}"
                    )
                    continue
            else:
                # For org-wide documents, use org security level
                if user_security_level < doc_level_value:
                    logger.debug(
                        f"Document blocked: user_org_level={user_security_level} < doc_level={doc_level_value}"
                    )
                    continue
            
            # Document passes all checks
            filtered_docs.append(doc)

            # Track maximum security level among accessible documents
            if max_security_level is None or doc_level_value > max_security_level:
                max_security_level = doc_level_value
        
        return filtered_docs, max_security_level
    
    async def query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        user_security_level: Optional[int] = None,
        user_department_id: Optional[int] = None,
        user_department_security_level: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Adaptive document retrieval with quality-based top-k adjustment.
        
        Process:
        1. Preprocess query (remove stop words, normalize)
        2. Check cache for existing results
        3. If cache miss: Start with min_top_k documents
        4. Check retrieval quality (scores above threshold)
        5. If quality is low, increase top_k (up to max_top_k) and retry
        6. If quality remains low, return empty context with explanation
        7. If only one high-scoring doc exists, return just that one
        
        Args:
            query_text: The search query (will be preprocessed internally)
            top_k: Optional override (uses min_top_k by default)
            user_security_level: User's org-wide clearance level
            user_department_id: User's department ID
            user_department_security_level: User's department-specific clearance level
            user_id: User ID for activity logging (optional)
            
        Returns:
            Dict with success, context (documents), count, error, message
        """
        # Step 1: Preprocess query
        cleaned_query = preprocess_query(query_text)
        
        # Step 2: Check cache
        cache_key = self._generate_cache_key(
            cleaned_query,
            user_security_level,
            user_department_id,
            user_department_security_level
        )
        
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for query (key={cache_key[:8]}...)")
            return cached_result
        
        # Step 3-7: Perform actual retrieval
        retrieval_result = await self._perform_retrieval(
            cleaned_query,
            top_k,
            user_security_level,
            user_department_id,
            user_department_security_level,
            user_id
        )
        
        # Cache successful results (TTL 5 minutes)
        if retrieval_result["success"]:
            await self.cache.set(cache_key, retrieval_result, ttl=300)
        
        return retrieval_result
    
    async def _perform_retrieval(
        self,
        query_text: str,
        top_k: Optional[int],
        user_security_level: Optional[int],
        user_department_id: Optional[int],
        user_department_security_level: Optional[int],
        user_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Perform the actual adaptive retrieval logic.
        Called by query() after cache check.
        """
        try:
            # Get configuration - uses MIN_TOP_K from app settings by default
            min_k = top_k or self.settings.app_settings.MIN_TOP_K
            max_k = self.settings.app_settings.MAX_TOP_K
            score_threshold = self.settings.app_settings.RETRIEVAL_SCORE_THRESHOLD
            
            vector_store = self.retriever.vectorstore
            current_k = min_k
            
            logger.info(f"Starting adaptive retrieval: min_k={min_k}, max_k={max_k}, threshold={score_threshold}")
            
            while current_k <= max_k:
                # Retrieve documents with scores
                try:
                    results = vector_store.similarity_search_with_score(query_text, k=current_k)
                except (AttributeError, NotImplementedError):
                    logger.warning("Vector store doesn't support scores, falling back to basic retrieval")
                    return await self._fallback_query(query_text, current_k, user_security_level, user_department_id, user_department_security_level)
                
                if not results:
                    logger.warning(f"No documents retrieved with k={current_k}")
                    return self._log_no_retrieval(
                        query_text=query_text,
                        user_id=user_id,
                        reason="no_documents",
                        details={"k": current_k}
                    )
                
                # Apply security filtering
                filtered_results = results
                max_security_level = None
                
                if user_security_level is not None:
                    docs = [doc for doc, _ in results]
                    filtered_docs, max_security_level = self._filter_by_security(
                        docs, user_security_level, user_department_id, user_department_security_level
                    )
                    
                    if len(docs) > 0 and len(filtered_docs) == 0:
                        return {
                            "success": False,
                            "error": "insufficient_clearance",
                            "message": "You do not have sufficient clearance to access the retrieved documents.",
                            "count": 0,
                            "max_security_level": max_security_level,
                        }
                    
                    filtered_ids = {id(doc) for doc in filtered_docs}
                    filtered_results = [(doc, score) for doc, score in results if id(doc) in filtered_ids]
                
                # Analyze scores
                scores = [score for _, score in filtered_results]
                high_quality_results = [(doc, score) for doc, score in filtered_results if score >= score_threshold]
                
                logger.info(f"k={current_k}: {len(filtered_results)} docs, {len(high_quality_results)} above threshold")
                
                # Check if we have quality results
                if high_quality_results:
                    # Check for single high-quality document
                    if len(high_quality_results) == 1 and len(filtered_results) > 1:
                        # Only one good result, rest are poor - return just the good one
                        logger.info(f"Single high-quality document found (score={high_quality_results[0][1]:.3f}), returning it")
                        return {
                            "success": True,
                            "context": [high_quality_results[0][0]],
                            "count": 1,
                            "max_security_level": max_security_level,
                        }
                    
                    # Multiple quality results - return them
                    logger.info(f"Found {len(high_quality_results)} quality documents")
                    return {
                        "success": True,
                        "context": [doc for doc, _ in high_quality_results],
                        "count": len(high_quality_results),
                        "max_security_level": max_security_level,
                    }
                
                # No quality results - try reranking if enabled and on first iteration
                if current_k == min_k and self.reranker and self.settings.app_settings.ENABLE_RERANKER:
                    logger.info("Initial results have poor quality, attempting reranking with max_k documents")
                    return await self._rerank_retrieval(
                        query_text,
                        max_k,
                        user_security_level,
                        user_department_id,
                        user_department_security_level,
                        score_threshold,
                        user_id
                    )
                
                # No quality results - try increasing k
                if current_k < max_k:
                    current_k = min(current_k + 2, max_k)
                    logger.info(f"Quality below threshold, increasing k to {current_k}")
                    continue
                else:
                    # Reached max_k with no quality results
                    logger.warning(f"Reached max_k={max_k} with no documents above threshold")
                    return self._log_no_retrieval(
                        query_text=query_text,
                        user_id=user_id,
                        reason="low_quality_results",
                        details={
                            "max_k": max_k,
                            "threshold": score_threshold,
                            "documents_retrieved": len(filtered_results),
                            "above_threshold": 0
                        }
                    )
            
            # Should not reach here
            return {
                "success": False,
                "error": "retrieval_error",
                "message": "Unexpected error during retrieval",
                "count": 0
            }
        
        except Exception as e:
            logger.error(f"Error in adaptive query: {e}", exc_info=True)
            return {
                "success": False,
                "error": "retrieval_error",
                "message": f"Failed to retrieve documents: {str(e)}",
                "count": 0
            }
    
    async def _rerank_retrieval(
        self,
        query_text: str,
        k: int,
        user_security_level: Optional[int],
        user_department_id: Optional[int],
        user_department_security_level: Optional[int],
        score_threshold: float,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve more documents and use reranker to find quality results.
        
        Args:
            query_text: The search query
            k: Number of documents to retrieve (typically max_k)
            user_security_level: User's clearance level
            user_department_id: User's department ID
            score_threshold: Quality threshold for reranker scores
            
        Returns:
            Dict with success, context, count, error, message
        """
        try:
            vector_store = self.retriever.vectorstore
            
            # Retrieve max_k documents
            try:
                results = vector_store.similarity_search_with_score(query_text, k=k)
            except (AttributeError, NotImplementedError):
                logger.warning("Vector store doesn't support scores during reranking")
                return {
                    "success": False,
                    "error": "low_quality_results",
                    "message": "No relevant documents found for your query.",
                    "count": 0
                }
            
            if not results:
                return {
                    "success": False,
                    "error": "no_documents",
                    "message": "No relevant documents found for your query.",
                    "count": 0
                }
            
            # Apply security filtering
            filtered_results = results
            max_security_level = None
            
            if user_security_level is not None:
                docs = [doc for doc, _ in results]
                filtered_docs, max_security_level = self._filter_by_security(
                    docs, user_security_level, user_department_id, user_department_security_level
                )
                
                if len(docs) > 0 and len(filtered_docs) == 0:
                    return {
                        "success": False,
                        "error": "insufficient_clearance",
                        "message": "You do not have sufficient clearance to access the retrieved documents.",
                        "count": 0,
                        "max_security_level": max_security_level,
                    }
                
                filtered_ids = {id(doc) for doc in filtered_docs}
                filtered_results = [(doc, score) for doc, score in results if id(doc) in filtered_ids]
            
            # Use reranker to improve ranking
            docs_to_rerank = [doc for doc, _ in filtered_results]
            reranker_top_k = self.settings.app_settings.RERANKER_TOP_K
            reranker_threshold = self.settings.app_settings.RERANKER_SCORE_THRESHOLD
            
            logger.info(f"Reranking {len(docs_to_rerank)} documents (target: top {reranker_top_k})")
            reranked_docs, reranked_scores = self.reranker.rerank(
                query_text,
                docs_to_rerank,
                top_k=reranker_top_k
            )
            
            # Filter reranked results by score threshold
            quality_results = [
                (doc, score) for doc, score in zip(reranked_docs, reranked_scores)
                if score >= reranker_threshold
            ]
            
            if quality_results:
                logger.info(f"Reranker found {len(quality_results)} quality documents")
                return {
                    "success": True,
                    "context": [doc for doc, _ in quality_results],
                    "count": len(quality_results),
                    "max_security_level": max_security_level,
                }
            else:
                logger.warning("Reranker could not find quality documents above threshold")
                return self._log_no_retrieval(
                    query_text=query_text,
                    user_id=user_id,
                    reason="reranker_no_quality",
                    details={
                        "documents_retrieved": len(docs_to_rerank),
                        "reranker_top_k": reranker_top_k,
                        "reranker_threshold": reranker_threshold,
                        "above_threshold": 0
                    }
                )
        
        except Exception as e:
            logger.error(f"Error during reranking retrieval: {e}", exc_info=True)
            return {
                "success": False,
                "error": "retrieval_error",
                "message": f"Failed to retrieve documents: {str(e)}",
                "count": 0
            }
    
    async def _fallback_query(
        self,
        query_text: str,
        k: int,
        user_security_level: Optional[int],
        user_department_id: Optional[int],
        user_department_security_level: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fallback when vector store doesn't support scores."""
        self.retriever.search_kwargs = {"k": k}
        docs = self.retriever.invoke(query_text)
        
        max_security_level = None
        if user_security_level is not None:
            filtered_docs, max_security_level = self._filter_by_security(
                docs, user_security_level, user_department_id, user_department_security_level
            )
            
            if len(docs) > 0 and len(filtered_docs) == 0:
                return {
                    "success": False,
                    "error": "insufficient_clearance",
                    "message": "You do not have sufficient clearance to access the retrieved documents.",
                    "count": 0,
                    "max_security_level": max_security_level,
                }
            docs = filtered_docs
        
        return {
            "success": True,
            "context": docs,
            "count": len(docs),
            "max_security_level": max_security_level,
        }


    def _log_no_retrieval(
        self,
        query_text: str,
        user_id: Optional[int],
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log no-context retrieval events for analysis.
        
        Args:
            query_text: The query that produced no results
            user_id: User ID if available
            reason: Reason code (no_documents, low_quality_results, reranker_no_quality)
            details: Additional context about the failure
            
        Returns:
            Standard error response dict
        """
        # Log with structured data for analysis
        logger.warning(
            f"No context retrieved - reason={reason}, query='{query_text[:100]}...', "
            f"user_id={user_id}, details={details}"
        )
        
        # Map reasons to user-friendly messages
        messages = {
            "no_documents": "No relevant documents found for your query.",
            "low_quality_results": "No relevant documents found for your query. The available documents do not match your request well enough.",
            "reranker_no_quality": "No relevant documents found for your query. The available documents do not match your request well enough."
        }
        
        return {
            "success": False,
            "error": reason,
            "message": messages.get(reason, "No relevant documents found."),
            "count": 0,
            "query": query_text,
            "details": details
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
