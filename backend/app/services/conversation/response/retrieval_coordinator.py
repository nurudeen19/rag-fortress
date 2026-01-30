"""
Retrieval Coordinator

Handles multi-query retrieval with partial context tracking for decomposed queries.
Coordinates independent retrieval, security filtering, deduplication, and reranking.
"""

from typing import Dict, Any, List, Optional
from app.services.vector_store.retriever import RetrieverService
from app.models.user_permission import PermissionLevel
from app.core import get_logger

logger = get_logger(__name__)


class RetrievalCoordinator:
    """Coordinates multi-query retrieval with partial context tracking."""
    
    def __init__(self, retriever: RetrieverService):
        """
        Initialize retrieval coordinator.
        
        """
        self.retriever = retriever
    
    def _determine_query_type(
        self,
        user_query: str,
        decomposition_result: Optional[Any]
    ) -> tuple[List[str], bool]:
        """
        Determine query type and whether multi-query processing is needed.

        Returns:
            Tuple of (queries list, is_multi_query flag)
        """
        if not decomposition_result:
            # No decomposition result - use original query
            return [user_query], False
        elif decomposition_result.decomposed:
            # Decomposed into multiple queries
            return decomposition_result.queries, True
        else:
            # Not decomposed - use optimized single query if available
            return decomposition_result.queries, False
    
    def _track_subquery_documents(
        self,
        docs: List[Any],
        subquery_index: int,
        document_map: Dict[str, List[int]]
    ) -> None:
        """
        Track which documents belong to which subquery.
        """
        for doc in docs:
            doc_id = doc.metadata.get("chunk_id") or doc.metadata.get("id") or doc.page_content[:100]
            if doc_id not in document_map:
                document_map[doc_id] = []
            document_map[doc_id].append(subquery_index)
    
    def _deduplicate_documents(
        self,
        all_documents: List[Any]
    ) -> List[Any]:
        """
        Deduplicate documents by ID.
            
        Returns:
            List of unique documents
        """
        seen_ids = set()
        unique_documents = []
        
        for doc in all_documents:
            doc_id = doc.metadata.get("chunk_id") or doc.metadata.get("id") or doc.page_content[:100]
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_documents.append(doc)
        
        logger.debug(f"Deduplicated: {len(unique_documents)} unique docs from {len(all_documents)} total")
        return unique_documents
    
    def _rerank_combined_documents(
        self,
        documents: List[Any],
        user_query: str,
        num_queries: int
    ) -> List[Any]:
        """
        Rerank combined documents against original query.
        
        Only applies to multi-query scenarios (num_queries > 1).
            
        Returns:
            Reranked and filtered documents
        """
        reranker_enabled = self.retriever.settings.app_settings.ENABLE_RERANKER
        
        if not (self.retriever.reranker and reranker_enabled and num_queries > 1):
            return documents
        
        logger.debug(f"Second reranking: {len(documents)} combined documents against original query")
        
        try:
            top_k = self.retriever.settings.app_settings.TOP_K
            reranked_docs, scores = self.retriever.reranker.rerank(
                query=user_query,
                documents=documents,
                top_k=top_k
            )
            
            # Filter by threshold
            reranker_threshold = self.retriever.settings.app_settings.RERANKER_SCORE_THRESHOLD
            filtered_documents = []
            for doc, score in zip(reranked_docs, scores):
                if score >= reranker_threshold:
                    filtered_documents.append(doc)
            
            logger.debug(f"Second reranking complete: {len(filtered_documents)} relevant documents")
            return filtered_documents
            
        except Exception as e:
            logger.warning(f"Second reranking failed: {e}, using unranked results")
            return documents
    
    def _apply_security_filtering(
        self,
        documents: List[Any],
        user_clearance: PermissionLevel,
        user_department_id: Optional[int],
        user_dept_clearance: Optional[PermissionLevel],
        queries: List[str],
        subquery_document_map: Dict[str, List[int]]
    ) -> Dict[str, Any]:
        """
        Apply security filtering to multi-query documents and analyze partial context.
        
        Note: Only called for multi-query scenarios. Single queries are handled
        directly by the retriever and return immediately.
            
        Returns:
            Final result dict with filtered documents or error, including partial context metadata
        """
        logger.debug(f"Applying security filtering to {len(documents)} documents")
        
        # Apply security filtering - returns complete metadata in one pass
        filtered_docs, security_metadata, blocked_depts = self.retriever._filter_by_security(
            documents=documents,
            user_security_level=user_clearance.value,
            user_department_id=user_department_id,
            user_department_security_level=user_dept_clearance.value if user_dept_clearance else None
        )
        
        logger.debug(f"After security filtering: {len(filtered_docs)}/{len(documents)} documents accessible")
        
        # Analyze which subqueries were satisfied
        satisfied_queries, clearance_blocked_queries, unsatisfied_queries = self._analyze_partial_context(
            filtered_docs=filtered_docs,
            all_documents=documents,
            queries=queries,
            subquery_document_map=subquery_document_map
        )
        
        # Build final result with messages and metadata
        context = self._build_result(
            filtered_docs=filtered_docs,
            all_documents=documents,
            queries=queries,
            satisfied_queries=satisfied_queries,
            clearance_blocked_queries=clearance_blocked_queries,
            unsatisfied_queries=unsatisfied_queries,
            security_metadata=security_metadata,
            blocked_depts=blocked_depts
        )
        
        return context
    
    def _analyze_partial_context(
        self,
        filtered_docs: List[Any],
        all_documents: List[Any],
        queries: List[str],
        subquery_document_map: Dict[str, List[int]]
    ) -> tuple[List[str], List[str], List[str]]:
        """
        Analyze which subqueries were satisfied vs blocked for multi-query retrieval.
        
        Returns:
            Tuple of (satisfied_queries, clearance_blocked_queries, unsatisfied_queries)
        """
        # Build set of document IDs that passed security filtering
        filtered_doc_ids = set()
        for doc in filtered_docs:
            doc_id = doc.metadata.get("chunk_id") or doc.metadata.get("id") or doc.page_content[:100]
            filtered_doc_ids.add(doc_id)
        
        # Classify each subquery
        satisfied_queries = []
        clearance_blocked_queries = []
        unsatisfied_queries = []
        
        for idx, subquery in enumerate(queries):
            # Find all document IDs from this subquery
            subquery_doc_ids = [doc_id for doc_id, indices in subquery_document_map.items() if idx in indices]
            
            if not subquery_doc_ids:
                # No documents retrieved (no relevant context)
                unsatisfied_queries.append(subquery)
            else:
                # Check if any docs passed filtering
                passed_filtering = any(doc_id in filtered_doc_ids for doc_id in subquery_doc_ids)
                
                if passed_filtering:
                    satisfied_queries.append(subquery)
                else:
                    clearance_blocked_queries.append(subquery)
        
        logger.debug(
            f"Subquery analysis: {len(satisfied_queries)} satisfied, "
            f"{len(clearance_blocked_queries)} clearance-blocked, "
            f"{len(unsatisfied_queries)} unsatisfied"
        )
        
        return satisfied_queries, clearance_blocked_queries, unsatisfied_queries
    
    def _build_result(
        self,
        filtered_docs: List[Any],
        all_documents: List[Any],
        queries: List[str],
        satisfied_queries: List[str],
        clearance_blocked_queries: List[str],
        unsatisfied_queries: List[str],
        security_metadata: Dict[str, Any],
        blocked_depts: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Build final result dict with appropriate messages and partial context metadata.
        
        Uses centralized message templates from settings.
        
        Returns:
            Final result dict with success/error status and partial context metadata
        """
        # If all documents blocked, return error with partial context
        # keeping max_security_level for backward compatibility
        if not filtered_docs:
            if blocked_depts:
                dept_list = ", ".join(sorted(blocked_depts))
                error_msg = self.retriever.settings.prompt_settings.RETRIEVAL_DEPT_BLOCKED_MESSAGE.format(dept_list=dept_list)
                error_type = "no_clearance"
            else:
                error_msg = self.retriever.settings.prompt_settings.RETRIEVAL_SECURITY_BLOCKED_MESSAGE
                error_type = "insufficient_clearance"
            
            logger.debug(f"All {len(all_documents)} documents blocked by security ({error_type})")
            return {
                "success": False,
                "context": [],
                "count": 0,
                "error": error_type,
                "message": error_msg,
                "blocked_departments": list(blocked_depts) if blocked_depts else None,
                "security_metadata": security_metadata,
                "partial_context": {
                    "is_partial": True,
                    "type": "clearance",
                    "total_queries": len(queries),
                    "satisfied_count": len(satisfied_queries),
                    "satisfied_queries": satisfied_queries,
                    "clearance_blocked_queries": clearance_blocked_queries,
                    "unsatisfied_queries": unsatisfied_queries
                }
            }
        
        # Build partial context metadata if some subqueries failed
        has_partial_context = (len(clearance_blocked_queries) > 0 or len(unsatisfied_queries) > 0)
        partial_context = None
        
        if has_partial_context:
            context_type = "clearance" if clearance_blocked_queries else "missing"
            partial_context = {
                "is_partial": True,
                "type": context_type,
                "total_queries": len(queries),
                "satisfied_count": len(satisfied_queries),
                "satisfied_queries": satisfied_queries,
                "clearance_blocked_queries": clearance_blocked_queries,
                "unsatisfied_queries": unsatisfied_queries
            }
            logger.debug(f"Partial context detected: type={context_type}")
        
        # Success: return filtered documents with complete security metadata        
        result = {
            "success": True,
            "context": filtered_docs,
            "count": len(filtered_docs),
            "security_metadata": security_metadata  # Complete metadata from filtering
        }
        
        if partial_context:
            result["partial_context"] = partial_context
        
        return result
    
    async def retrieve_context(
        self,
        user_query: str,
        user_clearance: PermissionLevel,
        user_department_id: Optional[int],
        user_dept_clearance: Optional[PermissionLevel],
        user_id: int,
        decomposition_result: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Retrieve context documents for query with optional multi-query decomposition.
        
        Flow:
        1. Determine query type (single/multi)
        2. Retrieve documents for each query
        3. For multi-query: deduplicate, rerank, apply security filtering
        4. For single-query: security filtering already applied
        
        Returns:
            Retrieval result dict with success, context, count, and optional partial_context
        """
        # Step 1: Determine query type
        queries, is_multi_query = self._determine_query_type(user_query, decomposition_result)
        
        # Step 2: Unified retrieval loop
        all_documents = []
        subquery_document_map = {}
        
        for idx, query in enumerate(queries):
            if is_multi_query:
                logger.debug(f"Retrieving subquery {idx+1}/{len(queries)}: '{query[:50]}...'")
            
            subquery_result = await self.retriever.query(
                query_text=query,
                user_security_level=user_clearance.value,
                user_department_id=user_department_id,
                user_department_security_level=user_dept_clearance.value if user_dept_clearance else None,
                user_id=user_id,
                skip_security_filter=is_multi_query
            )
            
            # Single query: return immediately (security already applied)
            if not is_multi_query:
                return subquery_result
            
            # Multi-query: collect and track documents
            if subquery_result["success"] and subquery_result.get("count", 0) > 0:
                docs = subquery_result["context"]
                all_documents.extend(docs)
                self._track_subquery_documents(docs, idx, subquery_document_map)
        
        # Step 3: Multi-query post-processing
        if not all_documents:
            logger.info("No documents retrieved for any subquery")
            return {
                "success": False,
                "context": [],
                "count": 0,
                "error": "no_documents",
                "message": "No relevant documents found for any aspect of your query."
            }
        
        # Deduplicate combined documents
        unique_documents = self._deduplicate_documents(all_documents)
        
        # Rerank against original query
        final_documents = self._rerank_combined_documents(
            documents=unique_documents,
            user_query=user_query,
            num_queries=len(queries)
        )
        
        # Step 4: Apply security filtering
        return self._apply_security_filtering(
            documents=final_documents,
            user_clearance=user_clearance,
            user_department_id=user_department_id,
            user_dept_clearance=user_dept_clearance,
            queries=queries,
            subquery_document_map=subquery_document_map
        )
