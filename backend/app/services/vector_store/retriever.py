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
    ) -> Tuple[List[Document], Optional[int], Optional[List[str]]]:
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
            Tuple of (filtered documents, max security level accessed, blocked department names)
        """
        filtered_docs: List[Document] = []
        max_security_level: Optional[int] = None
        blocked_departments: set = set()  # Track departments that blocked access
        
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
            
            # Enhanced logging for department filtering
            if is_department_only:
                logger.debug(
                    f"Checking dept-only doc: source={metadata.get('source', 'unknown')}, "
                    f"doc_dept_id={doc_department_id}, user_dept_id={user_department_id}, "
                    f"doc_level={doc_level_value}, user_dept_level={user_department_security_level}"
                )
            
            if is_department_only:
                # Department-only document - user must be in the same department
                if user_department_id is None:
                    dept_name = metadata.get("department", "Unknown Department")
                    blocked_departments.add(dept_name)
                    logger.info(f"BLOCKED: Dept-only doc (source={metadata.get('source')}) - user has no department")
                    continue
                if doc_department_id != user_department_id:
                    dept_name = metadata.get("department", "Unknown Department")
                    blocked_departments.add(dept_name)
                    logger.info(
                        f"BLOCKED: Dept mismatch - doc_dept={doc_department_id}, user_dept={user_department_id} "
                        f"(source={metadata.get('source')})"
                    )
                    continue
                
                # For department-only docs, use department security level
                if user_department_security_level is None:
                    dept_name = metadata.get("department", "Unknown Department")
                    blocked_departments.add(dept_name)
                    logger.info(f"BLOCKED: Dept-only doc but user has no dept clearance (source={metadata.get('source')})")
                    continue
                if user_department_security_level < doc_level_value:
                    dept_name = metadata.get("department", "Unknown Department")
                    blocked_departments.add(dept_name)
                    logger.info(
                        f"BLOCKED: Insufficient dept clearance - user_level={user_department_security_level}, "
                        f"doc_level={doc_level_value} (source={metadata.get('source')})"
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
        
        return filtered_docs, max_security_level, list(blocked_departments) if blocked_departments else None
    
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
        
        # Note: Caching disabled - Document objects are not JSON serializable
        # TODO: Implement custom serialization for Document objects if caching is needed
        # if retrieval_result["success"]:
        #     await self.cache.set(cache_key, retrieval_result, ttl=300)
        
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
        Perform retrieval with proper flow: Retrieve → Rerank → Filter → Decide.
        
        Flow:
        1. Retrieve candidates based on similarity scores
        2. Rerank for relevance if enabled (on ALL candidates)
        3. Apply security filtering to relevant results
        4. Decide outcome:
           - Relevant + allowed → return context
           - Relevant + blocked → insufficient clearance with dept names
           - Nothing relevant → no context found
        """
        try:
            # Step 1: Retrieve candidates from vector store
            min_k = top_k or self.settings.app_settings.MIN_TOP_K
            max_k = self.settings.app_settings.MAX_TOP_K
            vector_store = self.retriever.vectorstore
            
            logger.info(f"Retrieving candidates: max_k={max_k}")
            
            try:
                results = vector_store.similarity_search_with_score(query_text, k=max_k)
            except (AttributeError, NotImplementedError):
                logger.warning("Vector store doesn't support scores, falling back")
                return await self._fallback_query(query_text, max_k, user_security_level, user_department_id, user_department_security_level)
            
            if not results:
                logger.warning("No documents retrieved from vector store")
                return self._log_no_retrieval(
                    query_text=query_text,
                    user_id=user_id,
                    reason="no_documents",
                    details={"k": max_k}
                )
            
            logger.info(f"Retrieved {len(results)} candidates from vector store")
            
            # Step 2: Rerank ALL candidates to identify truly relevant documents
            relevant_docs = []
            reranker_threshold = self.settings.app_settings.RERANKER_SCORE_THRESHOLD
            
            if self.reranker and self.settings.app_settings.ENABLE_RERANKER:
                docs_to_rerank = [doc for doc, _ in results]
                reranker_top_k = self.settings.app_settings.RERANKER_TOP_K
                
                logger.info(f"Reranking {len(docs_to_rerank)} candidates (target: top {reranker_top_k})")
                reranked_docs, reranked_scores = self.reranker.rerank(
                    query_text,
                    docs_to_rerank,
                    top_k=reranker_top_k
                )
                
                # Filter by reranker threshold to get truly relevant docs
                for doc, score in zip(reranked_docs, reranked_scores):
                    if score >= reranker_threshold:
                        relevant_docs.append(doc)
                
                logger.info(f"Reranker identified {len(relevant_docs)} relevant documents (threshold={reranker_threshold})")
            else:
                # No reranker - use similarity scores
                score_threshold = self.settings.app_settings.RETRIEVAL_SCORE_THRESHOLD
                for doc, score in results:
                    if score >= score_threshold:
                        relevant_docs.append(doc)
                logger.info(f"Found {len(relevant_docs)} relevant documents by similarity (threshold={score_threshold})")
            
            # Step 3: Apply security filtering to relevant documents
            if not relevant_docs:
                # No relevant documents found at all
                logger.info("No relevant documents found (before security filtering)")
                return self._log_no_retrieval(
                    query_text=query_text,
                    user_id=user_id,
                    reason="no_relevant_documents",
                    details={"candidates_retrieved": len(results), "relevant_after_rerank": 0}
                )
            
            # Apply security filtering
            filtered_docs, max_security_level, blocked_depts = self._filter_by_security(
                relevant_docs, user_security_level, user_department_id, user_department_security_level
            )
            
            logger.info(f"Security filtering: {len(filtered_docs)}/{len(relevant_docs)} documents accessible")
            
            # Step 4: Decide outcome based on filtering results
            if filtered_docs:
                # SUCCESS: Have relevant documents that user can access
                logger.info(f"Returning {len(filtered_docs)} relevant and accessible documents")
                return {
                    "success": True,
                    "context": filtered_docs,
                    "count": len(filtered_docs),
                    "max_security_level": max_security_level,
                }
            else:
                # BLOCKED: Relevant documents exist but user lacks clearance
                # Determine error type based on blocking reason
                if blocked_depts:
                    # Department access issue
                    dept_list = ", ".join(blocked_depts)
                    error_msg = self.settings.prompt_settings.RETRIEVAL_DEPT_BLOCKED_MESSAGE.format(dept_list=dept_list)
                    error_type = "no_clearance"
                else:
                    # General security clearance issue
                    error_msg = self.settings.prompt_settings.RETRIEVAL_SECURITY_BLOCKED_MESSAGE
                    error_type = "insufficient_clearance"
                
                logger.info(f"All {len(relevant_docs)} relevant documents blocked by security ({error_type}): {blocked_depts}")
                return {
                    "success": False,
                    "error": error_type,
                    "message": error_msg,
                    "count": 0,
                    "max_security_level": max_security_level,
                    "blocked_departments": blocked_depts
                }
        
        except Exception as e:
            logger.error(f"Error during retrieval: {e}", exc_info=True)
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
            filtered_docs, max_security_level, blocked_depts = self._filter_by_security(
                docs, user_security_level, user_department_id, user_department_security_level
            )
            
            if len(docs) > 0 and len(filtered_docs) == 0:
                # Determine error type based on blocking reason
                if blocked_depts:
                    # Department access issue
                    dept_list = ",".join(blocked_depts)
                    error_msg = self.settings.prompt_settings.RETRIEVAL_DEPT_BLOCKED_MESSAGE.format(dept_list=dept_list)
                    error_type = "no_clearance"
                else:
                    # General security clearance issue
                    error_msg = self.settings.prompt_settings.RETRIEVAL_SECURITY_BLOCKED_MESSAGE
                    error_type = "insufficient_clearance"
                
                return {
                    "success": False,
                    "error": error_type,
                    "message": error_msg,
                    "count": 0,
                    "blocked_departments": blocked_depts
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
