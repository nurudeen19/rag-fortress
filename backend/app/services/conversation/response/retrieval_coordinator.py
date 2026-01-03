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
        
        Optimized flow for multi-query:
        1. Retrieve documents for each subquery WITHOUT security filtering (tag with source)
        2. Combine and deduplicate all results  
        3. Rerank combined results against original query (for relevance to original)
        4. Apply security filtering ONCE to final results
        5. Analyze which subqueries were satisfied/blocked/unsatisfied for partial context tracking
        
        This avoids double-filtering, ensures reranker sees full candidate pool, and enables
        specialized prompting based on which aspects of a decomposed query succeeded vs failed.
        
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
        subquery_document_map = {}  # Track which documents came from which subquery
        
        # Retrieve for each subquery WITHOUT security filtering (defer to end)
        for idx, subquery in enumerate(decomposed_queries):
            logger.debug(f"Retrieving subquery {idx+1}/{len(decomposed_queries)}: '{subquery[:50]}...'")
            
            subquery_result = await self.retriever.query(
                query_text=subquery,
                user_security_level=user_clearance.value,
                user_department_id=user_department_id,
                user_department_security_level=user_dept_clearance.value if user_dept_clearance else None,
                user_id=user_id,
                skip_security_filter=True  # Defer security filtering to the end
            )
            
            # Collect all documents (no filtering yet) and tag with source subquery
            if subquery_result["success"] and subquery_result.get("count", 0) > 0:
                docs = subquery_result["context"]
                all_documents.extend(docs)
                
                # Track which documents belong to this subquery
                for doc in docs:
                    doc_id = doc.metadata.get("chunk_id") or doc.metadata.get("id") or doc.page_content[:100]
                    if doc_id not in subquery_document_map:
                        subquery_document_map[doc_id] = []
                    subquery_document_map[doc_id].append(idx)
        
        # Deduplicate documents by ID
        seen_ids = set()
        unique_documents = []
        for doc in all_documents:
            doc_id = doc.metadata.get("chunk_id") or doc.metadata.get("id") or doc.page_content[:100]
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_documents.append(doc)
        
        logger.info(f"Combined results: {len(unique_documents)} unique docs from {len(all_documents)} total")
        
        # If we got no documents at all, return error
        if not unique_documents:
            logger.info("No documents retrieved for any subquery")
            return {
                "success": False,
                "context": [],
                "count": 0,
                "error": "no_documents",
                "message": "No relevant documents found for any aspect of your query."
            }
        
        # Rerank combined results against original query (for relevance to original question)
        final_documents = unique_documents
        
        if self.retriever.reranker and len(decomposed_queries) > 1:
            logger.info(f"Reranking {len(unique_documents)} documents against original query for relevance")
            try:
                reranked_docs, scores = self.retriever.reranker.rerank(
                    query=user_query,  # Use original query for reranking
                    documents=unique_documents
                )
                if reranked_docs:
                    final_documents = reranked_docs
                    logger.info(f"Reranking complete: {len(final_documents)} documents")
            except Exception as e:
                logger.warning(f"Reranking failed: {e}, using unranked results")
        else:
            if len(decomposed_queries) == 1:
                logger.info("Skipping coordinator reranking for single query (already reranked in retriever)")
        
        # NOW apply security filtering ONCE to final results
        logger.info(f"Applying security filtering to {len(final_documents)} final documents")
        filtered_docs, max_security_level, blocked_depts = self.retriever._filter_by_security(
            documents=final_documents,
            user_security_level=user_clearance.value,
            user_department_id=user_department_id,
            user_department_security_level=user_dept_clearance.value if user_dept_clearance else None
        )
        
        logger.info(f"After security filtering: {len(filtered_docs)}/{len(final_documents)} documents accessible")
        
        # Analyze which subqueries were satisfied vs unsatisfied
        # Note: "Unsatisfied" means the query wasn't answered - either due to no relevant 
        # context OR security blocking. We track them separately for specialized prompting.
        satisfied_queries = []  # Queries that contributed to final context
        clearance_blocked_queries = []  # Unsatisfied: had docs but blocked by security
        unsatisfied_queries = []  # Unsatisfied: no relevant context found at all
        
        # Build set of document IDs that passed security filtering
        filtered_doc_ids = set()
        for doc in filtered_docs:
            doc_id = doc.metadata.get("chunk_id") or doc.metadata.get("id") or doc.page_content[:100]
            filtered_doc_ids.add(doc_id)
        
        # Classify each subquery based on its documents
        for idx, subquery in enumerate(decomposed_queries):
            # Find all document IDs that came from this subquery
            subquery_doc_ids = [doc_id for doc_id, indices in subquery_document_map.items() if idx in indices]
            
            if not subquery_doc_ids:
                # UNSATISFIED: No documents retrieved (no relevant context exists)
                unsatisfied_queries.append(subquery)
            else:
                # Check if any of this subquery's documents passed filtering
                passed_filtering = any(doc_id in filtered_doc_ids for doc_id in subquery_doc_ids)
                
                if passed_filtering:
                    # SATISFIED: Documents found and user has access
                    satisfied_queries.append(subquery)
                else:
                    # UNSATISFIED: Documents exist but user lacks clearance
                    clearance_blocked_queries.append(subquery)
        
        logger.info(
            f"Subquery analysis: {len(satisfied_queries)} satisfied, "
            f"{len(clearance_blocked_queries)} clearance-blocked, "
            f"{len(unsatisfied_queries)} unsatisfied"
        )
        
        # If all documents blocked by security, return appropriate error with partial context
        if not filtered_docs:
            if blocked_depts:
                dept_list = ", ".join(sorted(blocked_depts))
                error_msg = f"You do not have access to {dept_list} department content. To request access, please submit a permission override request for the {dept_list} department."
                error_type = "no_clearance"
            else:
                error_msg = "No documents found matching your clearance level."
                error_type = "insufficient_clearance"
            
            logger.info(f"All {len(final_documents)} documents blocked by security ({error_type})")
            return {
                "success": False,
                "context": [],
                "count": 0,
                "error": error_type,
                "message": error_msg,
                "blocked_departments": list(blocked_depts) if blocked_depts else None,
                "max_security_level": max_security_level,
                "partial_context": {
                    "is_partial": True,
                    "type": "clearance",
                    "total_queries": len(decomposed_queries),
                    "satisfied_count": len(satisfied_queries),
                    "satisfied_queries": satisfied_queries,
                    "clearance_blocked_queries": clearance_blocked_queries,
                    "unsatisfied_queries": unsatisfied_queries
                }
            }
        
        # Determine if we have partial context (some subqueries failed)
        has_partial_context = (len(clearance_blocked_queries) > 0 or len(unsatisfied_queries) > 0)
        
        partial_context = None
        if has_partial_context:
            # Determine primary type: clearance if any blocked, otherwise missing
            context_type = "clearance" if clearance_blocked_queries else "missing"
            
            partial_context = {
                "is_partial": True,
                "type": context_type,
                "total_queries": len(decomposed_queries),
                "satisfied_count": len(satisfied_queries),
                "satisfied_queries": satisfied_queries,
                "clearance_blocked_queries": clearance_blocked_queries,
                "unsatisfied_queries": unsatisfied_queries
            }
            
            logger.info(f"Partial context detected: type={context_type}")
        
        # Success: return filtered documents with optional partial context metadata
        result = {
            "success": True,
            "context": filtered_docs,
            "count": len(filtered_docs),
            "max_security_level": max_security_level
        }
        
        if partial_context:
            result["partial_context"] = partial_context
        
        return result
