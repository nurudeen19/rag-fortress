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
        
        Args:
            retriever: Vector store retriever service
        """
        self.retriever = retriever
    
    async def retrieve_context(
        self,
        user_query: str,
        user_clearance: PermissionLevel,
        user_department_id: Optional[int],
        user_dept_clearance: Optional[PermissionLevel],
        user_id: int,
        decomposed_queries: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve context documents for query with optional multi-query decomposition.
        
        If decomposed_queries is provided and contains multiple queries:
        - Retrieves documents for each subquery independently
        - Applies security filtering to each subquery's results
        - Combines and reranks all results against the original query
        - Tracks which subqueries were satisfied (got results) vs unsatisfied (blocked/empty)
        - Returns partial context metadata for specialized prompting
        
        Args:
            user_query: User's original question (used for reranking)
            user_clearance: User's organization-level clearance
            user_department_id: User's department ID
            user_dept_clearance: User's department-level clearance
            user_id: User ID for logging
            decomposed_queries: Optional list of decomposed queries to retrieve
            
        Returns:
            Retrieval result dict with:
            - success: bool
            - context: List[Document]
            - count: int
            - max_security_level: Optional[int]
            - partial_context: Optional[Dict] with subquery satisfaction tracking
        """
        dept_level_str = f", dept_level={user_dept_clearance.name}" if user_dept_clearance else ""
        logger.info(f"Retrieving context for user_id={user_id}, org_level={user_clearance.name}{dept_level_str}")
        
        # If no decomposition or only single query, use standard retrieval
        if not decomposed_queries or len(decomposed_queries) <= 1:
            query_to_use = decomposed_queries[0] if decomposed_queries else user_query
            
            retrieval_result = await self.retriever.query(
                query_text=query_to_use,
                user_security_level=user_clearance.value,
                user_department_id=user_department_id,
                user_department_security_level=user_dept_clearance.value if user_dept_clearance else None,
                user_id=user_id
            )
            
            return retrieval_result
        
        # Multi-query decomposition path
        logger.info(f"Decomposed retrieval: {len(decomposed_queries)} subqueries")
        
        all_documents = []
        satisfied_queries = []
        unsatisfied_queries = []
        clearance_blocked_queries = []
        
        # Retrieve for each subquery
        for idx, subquery in enumerate(decomposed_queries):
            logger.debug(f"Retrieving subquery {idx+1}/{len(decomposed_queries)}: '{subquery[:50]}...'")
            
            subquery_result = await self.retriever.query(
                query_text=subquery,
                user_security_level=user_clearance.value,
                user_department_id=user_department_id,
                user_department_security_level=user_dept_clearance.value if user_dept_clearance else None,
                user_id=user_id
            )
            
            # Track satisfaction status
            if subquery_result["success"] and subquery_result.get("count", 0) > 0:
                satisfied_queries.append(subquery)
                all_documents.extend(subquery_result["context"])
            else:
                # Determine if blocked by clearance or just no matches
                error_type = subquery_result.get("error")
                if error_type == "no_clearance":
                    clearance_blocked_queries.append(subquery)
                else:
                    unsatisfied_queries.append(subquery)
        
        # Deduplicate documents by ID
        seen_ids = set()
        unique_documents = []
        for doc in all_documents:
            doc_id = doc.metadata.get("chunk_id") or doc.metadata.get("id") or doc.page_content[:100]
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_documents.append(doc)
        
        logger.info(
            f"Combined results: {len(unique_documents)} unique docs from {len(all_documents)} total "
            f"({len(satisfied_queries)} satisfied, {len(clearance_blocked_queries)} clearance-blocked, "
            f"{len(unsatisfied_queries)} no-matches)"
        )
        
        # If we got no documents at all, return error
        if not unique_documents:
            # Determine primary error type
            if clearance_blocked_queries:
                return {
                    "success": False,
                    "context": [],
                    "count": 0,
                    "error": "no_clearance",
                    "message": "No documents found matching your clearance level for any aspect of your query."
                }
            else:
                return {
                    "success": False,
                    "context": [],
                    "count": 0,
                    "error": "no_context",
                    "message": "No relevant documents found for any aspect of your query."
                }
        
        # Rerank combined results against original query if reranker is available
        final_documents = unique_documents
        max_security_level = None
        
        if self.retriever.reranker:
            logger.info(f"Reranking {len(unique_documents)} documents against original query")
            try:
                reranked = await self.retriever.reranker.rerank(
                    query=user_query,  # Use original query for reranking
                    documents=unique_documents
                )
                if reranked:
                    final_documents = reranked
                    logger.info(f"Reranked to {len(final_documents)} documents")
            except Exception as e:
                logger.warning(f"Reranking failed: {e}, using unranked results")
        
        # Calculate max security level from final documents
        for doc in final_documents:
            doc_level = doc.metadata.get("security_level")
            if doc_level is not None:
                try:
                    if isinstance(doc_level, int):
                        level_value = doc_level
                    else:
                        level_value = PermissionLevel[str(doc_level)].value
                    
                    if max_security_level is None or level_value > max_security_level:
                        max_security_level = level_value
                except (KeyError, ValueError):
                    pass
        
        # Build partial context metadata
        partial_context_info = None
        if clearance_blocked_queries or unsatisfied_queries:
            partial_context_info = {
                "is_partial": True,
                "satisfied_queries": satisfied_queries,
                "clearance_blocked_queries": clearance_blocked_queries,
                "unsatisfied_queries": unsatisfied_queries,
                "total_queries": len(decomposed_queries),
                "satisfied_count": len(satisfied_queries),
                "type": "clearance" if clearance_blocked_queries else "missing"
            }
            
            logger.info(
                f"Partial context: {len(satisfied_queries)}/{len(decomposed_queries)} queries satisfied "
                f"(type={partial_context_info['type']})"
            )
        
        return {
            "success": True,
            "context": final_documents,
            "count": len(final_documents),
            "max_security_level": max_security_level,
            "partial_context": partial_context_info
        }
