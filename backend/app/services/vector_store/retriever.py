"""
Retriever service for querying the vector store.
Handles adaptive document retrieval with quality-based top-k adjustment and reranking.
Includes semantic caching with vector similarity.
"""

from typing import List, Optional, Dict, Any, Tuple
from langchain_core.documents import Document

from app.core.vector_store_factory import get_retriever
from app.core import get_logger
from app.core.semantic_cache import get_semantic_cache
from app.core.events import get_event_bus
from app.config.settings import settings
from app.models.user_permission import PermissionLevel
from app.services.vector_store.reranker import get_reranker_service


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
        self.semantic_cache = get_semantic_cache()
    
    def _get_document_security_level(self, doc_security_level: Any) -> int:
        """
        Get numeric security level value from document metadata.
        
        Handles:
        - None or 0 as public/no clearance (returns 0)
        - Integer values (returns as-is)
        - String integers (parses to int)
        - Enum names (looks up value)
        - Invalid values (defaults to GENERAL)
        
        Returns:
            Integer security level value
        """
        # Handle None or 0 as public/no clearance required
        if doc_security_level is None or doc_security_level == 0:
            return 0  # Public document, accessible to all
        
        try:
            # Handle both string enum names and integer values
            if isinstance(doc_security_level, int):
                return doc_security_level
            elif isinstance(doc_security_level, str) and doc_security_level.isdigit():
                return int(doc_security_level)
            else:
                return PermissionLevel[doc_security_level].value
        except (KeyError, ValueError):
            logger.warning(f"Invalid security level '{doc_security_level}' in document metadata, defaulting to GENERAL")
            return PermissionLevel.GENERAL.value  # Default to GENERAL instead of skipping
    
    def _check_department_membership(
        self,
        metadata: Dict[str, Any],
        user_department_id: Optional[int],
        blocked_departments: set
    ) -> bool:
        """
        Check if user belongs to the document's department.
        
        Returns:
            True if user has department access, False otherwise
        """
        doc_department_id = metadata.get("department_id")
        
        # User has no department assignment
        if user_department_id is None:
            dept_name = metadata.get("department", "Unknown Department")
            blocked_departments.add(dept_name)
            logger.info(f"BLOCKED: Dept-only doc (source={metadata.get('source')}) - user has no department")
            return False
        
        # User belongs to different department
        if doc_department_id != user_department_id:
            dept_name = metadata.get("department", "Unknown Department")
            blocked_departments.add(dept_name)
            logger.info(
                f"BLOCKED: Dept mismatch - doc_dept={doc_department_id}, user_dept={user_department_id} "
                f"(source={metadata.get('source')})"
            )
            return False
        
        return True
    
    def _check_department_clearance(
        self,
        doc_level_value: int,
        user_department_security_level: Optional[int],
        metadata: Dict[str, Any],
        blocked_departments: set
    ) -> bool:
        """
        Check if user has sufficient department clearance for document.
        
        Returns:
            True if user has sufficient clearance, False otherwise
        """
        # User has no department clearance
        if user_department_security_level is None:
            dept_name = metadata.get("department", "Unknown Department")
            blocked_departments.add(dept_name)
            logger.debug(f"BLOCKED: Dept-only doc but user has no dept clearance (source={metadata.get('source')})")
            return False
        
        # User's clearance is insufficient
        if user_department_security_level < doc_level_value:
            dept_name = metadata.get("department", "Unknown Department")
            blocked_departments.add(dept_name)
            logger.debug(
                f"BLOCKED: Insufficient dept clearance - user_level={user_department_security_level}, "
                f"doc_level={doc_level_value} (source={metadata.get('source')})"
            )
            return False
        
        return True
    
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
            
        Returns:
            Tuple of (filtered documents, max security level accessed, blocked department names)
        """
        filtered_docs: List[Document] = []
        max_security_level: Optional[int] = None
        blocked_departments: set = set()  # Track departments that blocked access
        
        for doc in documents:
            metadata = doc.metadata
            
            # Get document security level
            doc_security_level = metadata.get("security_level", "GENERAL")
            doc_level_value = self._get_document_security_level(doc_security_level)
            
            # Check department access
            is_department_only = metadata.get("is_department_only", False)
                        
            if is_department_only:
                # Check department membership
                if not self._check_department_membership(metadata, user_department_id, blocked_departments):
                    continue
                
                # Check department clearance level
                if not self._check_department_clearance(
                    doc_level_value, user_department_security_level, metadata, blocked_departments
                ):
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
    
    def _get_high_quality_docs(
        self,
        results: List[Tuple[Document, float]],
        score_threshold: float
    ) -> List[Document]:
        """
        Extract documents that meet the quality threshold from similarity results.
        
        Returns:
            List of documents that passed the threshold
        """
        high_quality_docs = []
        for doc, score in results:
            if score >= score_threshold:
                high_quality_docs.append(doc)
        
        return high_quality_docs
    
    def _perform_reranking(
        self,
        query_text: str,
        results: List[Tuple[Document, float]],
        top_k: int,
        reranker_threshold: float
    ) -> List[Document]:
        """
        Rerank candidates and filter by threshold.
        
        Args:
            query_text: Query to rerank against
            results: List of (document, score) tuples to rerank
            top_k: Number of top results to return
            reranker_threshold: Minimum score required after reranking
        
        Returns:
            List of relevant documents after reranking
        """
        docs_to_rerank = [doc for doc, _ in results]
        
        logger.info(f"Reranking {len(docs_to_rerank)} candidates (target: top {top_k})")
        reranked_docs, reranked_scores = self.reranker.rerank(
            query_text,
            docs_to_rerank,
            top_k=top_k
        )
        
        # Filter by reranker threshold
        relevant_docs = []
        for doc, score in zip(reranked_docs, reranked_scores):
            if score >= reranker_threshold:
                relevant_docs.append(doc)
        
        logger.info(f"Reranker identified {len(relevant_docs)} relevant documents (threshold={reranker_threshold})")
        return relevant_docs
    
    def _select_relevant_documents(
        self,
        results: List[Tuple[Document, float]],
        query_text: str,
        top_k: int
    ) -> List[Document]:
        """
        Select relevant documents using quality threshold and optional reranking.
        
        Strategy:
        - If high-quality docs exist: Use them directly (no reranking needed)
        - If no high-quality docs: Attempt reranking (if enabled)
        - If no reranker: Use quality docs or empty list
        
        Returns:
            List of relevant documents
        """
        score_threshold = self.settings.app_settings.RETRIEVAL_SCORE_THRESHOLD
        reranker_threshold = self.settings.app_settings.RERANKER_SCORE_THRESHOLD
        
        # Check for high-quality results from similarity
        high_quality_docs = self._get_high_quality_docs(results, score_threshold)
        
        # Decide on retrieval strategy
        if self.reranker and self.settings.app_settings.ENABLE_RERANKER:
            if len(high_quality_docs) > 0:
                # Have quality results - use them directly
                logger.info(f"Using {len(high_quality_docs)} high-quality results (threshold={score_threshold})")
                return high_quality_docs[:top_k]
            else:
                # No quality results - try reranking
                logger.info(f"No high-quality results found (threshold={score_threshold}), attempting reranking")
                return self._perform_reranking(query_text, results, top_k, reranker_threshold)
        else:
            # No reranker - use quality docs only
            relevant_docs = high_quality_docs[:top_k] if high_quality_docs else []
            logger.info(f"Found {len(relevant_docs)} relevant documents by similarity (threshold={score_threshold})")
            return relevant_docs
    
    def _build_retrieval_outcome(
        self,
        filtered_docs: List[Document],
        relevant_docs: List[Document],
        max_security_level: Optional[int],
        blocked_depts: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Build final retrieval outcome based on security filtering results.
        
        Args:
            filtered_docs: Documents that passed security filtering
            relevant_docs: All relevant documents before filtering
            max_security_level: Highest security level accessed
            blocked_depts: List of department names that blocked access
        
        Returns:
            Success response with documents or error response with blocking reason
        """
        if filtered_docs:
            return {
                "success": True,
                "context": filtered_docs,
                "count": len(filtered_docs),
                "max_security_level": max_security_level,
            }
        
        # Determine error type based on blocking reason
        if blocked_depts:
            dept_list = ", ".join(blocked_depts)
            error_msg = self.settings.prompt_settings.RETRIEVAL_DEPT_BLOCKED_MESSAGE.format(dept_list=dept_list)
            error_type = "no_clearance"
        else:
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
    
    async def query(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        user_security_level: Optional[int] = None,
        user_department_id: Optional[int] = None,
        user_department_security_level: Optional[int] = None,
        user_id: Optional[int] = None,
        skip_security_filter: bool = False
    ) -> Dict[str, Any]:
        """
        Adaptive document retrieval with quality-based top-k adjustment.
        
        Process:
        1. Check cache for existing results
        2. Retrieve max_k candidates from vector store
        3. Rerank candidates if reranker is enabled
        4. Filter by threshold to get relevant documents
        5. Return top_k final results
            
        Returns:
            Dict with success, context (documents), count, error, message
        """
        # Check context-level semantic cache
        cached_context, should_continue = await self.semantic_cache.get(
            cache_type="context",
            query=query_text,
            user_security_level=user_security_level or 0,
            user_department_id=user_department_id,
            user_department_security_level=user_department_security_level
        )
        
        if cached_context and not should_continue:
            # Deserialize documents from cache (they were stored as dicts)
            if cached_context.get("context"):
                cached_context["context"] = [
                    Document(page_content=doc["page_content"], metadata=doc["metadata"])
                    for doc in cached_context["context"]
                ]
            # Cluster at capacity, return cached immediately
            return cached_context
        
        if should_continue:
            logger.debug("Context cache hit but continuing retrieval to add variation")
        
        # Perform retrieval
        retrieval_result = await self._perform_retrieval(
            query_text,
            top_k,
            user_security_level,
            user_department_id,
            user_department_security_level,
            user_id,
            skip_security_filter
        )
        
        # Cache successful retrieval in context cache (non-blocking)
        if retrieval_result["success"] and retrieval_result.get("context"):
            # Analyze security metadata from documents
            documents = retrieval_result["context"]
            max_security = retrieval_result.get("max_security_level")
            
            # Check if any docs are department-only
            is_departmental = any(
                doc.metadata.get("is_department_only", False) for doc in documents
            )
            
            # Collect department IDs
            dept_ids = list(set(
                doc.metadata.get("department_id")
                for doc in documents
                if doc.metadata.get("is_department_only") and doc.metadata.get("department_id")
            ))
            
            # Emit cache event (non-blocking background processing)
            bus = get_event_bus()
            await bus.emit("semantic_cache", {
                "cache_type": "context",
                "query": query_text,
                "entry": retrieval_result,
                "min_security_level": max_security,
                "is_departmental": is_departmental,
                "department_ids": dept_ids if is_departmental else None
            })
        
        return retrieval_result
    
    async def _perform_retrieval(
        self,
        query_text: str,
        top_k: Optional[int],
        user_security_level: Optional[int],
        user_department_id: Optional[int],
        user_department_security_level: Optional[int],
        user_id: Optional[int],
        skip_security_filter: bool = False
    ) -> Dict[str, Any]:
        """
        Perform retrieval with proper flow: Retrieve → Rerank → Filter → Decide.
        
        Flow:
        1. Retrieve candidates based on similarity scores
           - Uses hybrid search (dense + sparse vectors) if ENABLE_HYBRID_SEARCH=True
           - Falls back to dense-only search if hybrid not configured
        2. Rerank for relevance if enabled (on ALL candidates)
        3. Apply security filtering to relevant results (unless skip_security_filter=True)
        4. Decide outcome:
           - Relevant + allowed → return context
           - Relevant + blocked → insufficient clearance
           - Nothing relevant → no context found
        
        Hybrid Search Details:
        - Qdrant: Uses RetrievalMode.HYBRID with BM25 sparse embeddings (FastEmbed)
        - Weaviate: Native BM25F via alpha parameter (no special config needed)
        - Milvus: Uses BM25BuiltInFunction with separate dense/sparse vectors
        - Results are fused using RRF (Reciprocal Rank Fusion) by default
        
        Args:
            skip_security_filter: If True, return documents without security filtering
        """
        try:
            # Step 1: Retrieve candidates from vector store
            top_k = top_k or self.settings.app_settings.TOP_K
            max_k = self.settings.app_settings.MAX_K
            vector_store = self.retriever.vectorstore
            
            logger.info(f"Retrieving candidates: max_k={max_k}, top_k={top_k}")
            
            try:
                results = vector_store.similarity_search_with_score(query_text, k=max_k)
            except (AttributeError, NotImplementedError):
                logger.warning("Vector store doesn't support scores, falling back")
                return await self._fallback_query(query_text, max_k, top_k, user_security_level, user_department_id, user_department_security_level)
            
            if not results:
                logger.warning("No documents retrieved from vector store")
                return self._log_no_retrieval(
                    query_text=query_text,
                    user_id=user_id,
                    reason="no_documents",
                    details={"k": max_k}
                )
            
            # Step 2: Select relevant documents (quality check + optional reranking)
            relevant_docs = self._select_relevant_documents(results, query_text, top_k)
            
            # Step 3: Check if any relevant documents found
            if not relevant_docs:
                # No relevant documents found at all
                logger.info("No relevant documents found (before security filtering)")
                return self._log_no_retrieval(
                    query_text=query_text,
                    user_id=user_id,
                    reason="no_relevant_documents",
                    details={"candidates_retrieved": len(results), "relevant_after_rerank": 0}
                )
            
            # If skip_security_filter=True, return unfiltered results for multi-query coordination
            if skip_security_filter:
                logger.info(f"Skipping security filter (multi-query mode): returning {len(relevant_docs)} documents")
                return {
                    "success": True,
                    "context": relevant_docs,
                    "count": len(relevant_docs),
                    "max_security_level": None,  # Will be calculated after final filtering
                }
            
            # Apply security filtering
            filtered_docs, max_security_level, blocked_depts = self._filter_by_security(
                relevant_docs, user_security_level, user_department_id, user_department_security_level
            )
            
            logger.info(f"Security filtering: {len(filtered_docs)}/{len(relevant_docs)} documents accessible")
            
            # Step 4: Build and return outcome
            return self._build_retrieval_outcome(
                filtered_docs, relevant_docs, max_security_level, blocked_depts
            )
        
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
        top_k: int,
        user_security_level: Optional[int],
        user_department_id: Optional[int],
        user_department_security_level: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fallback when vector store doesn't support scores."""
        self.retriever.search_kwargs = {"k": k}
        docs = self.retriever.invoke(query_text)
        
        if user_security_level is None:
            # No security filtering needed for public data
            return {
                "success": True,
                "context": docs[:top_k],
                "count": len(docs[:top_k]),
                "max_security_level": None,
            }
        
        # Apply security filtering
        filtered_docs, max_security_level, blocked_depts = self._filter_by_security(
            docs, user_security_level, user_department_id, user_department_security_level
        )
        
        # Limit to top_k
        filtered_docs = filtered_docs[:top_k]
        
        # Build outcome using shared method
        return self._build_retrieval_outcome(
            filtered_docs, docs, max_security_level, blocked_depts
        )


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
    
    return _retriever_service
