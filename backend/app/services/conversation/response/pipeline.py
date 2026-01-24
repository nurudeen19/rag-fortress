"""
Response Pipeline

Orchestrates the RAG response generation process.
Handles retrieval, LLM routing, prompt construction, streaming, and fallback logic.
Includes query decomposition for improved retrieval.
"""

from typing import Dict, Any, AsyncGenerator, List, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.vector_store.retriever import RetrieverService
from app.services.conversation.response.retrieval_coordinator import RetrievalCoordinator
from app.services.llm import LLMRouter, LLMType
from app.services.conversation.service import ConversationService
from app.utils.llm_error_handler import LLMErrorHandler, ErrorShouldRetry
from app.utils.text_processing import preprocess_query
from app.config.prompt_settings import get_prompt_settings
from app.models.user_permission import PermissionLevel
from app.models.message import MessageRole
from app.config.settings import settings
from app.core import get_logger
from app.core.semantic_cache import get_semantic_cache

logger = get_logger(__name__)


class ResponsePipeline:
    """Orchestrates RAG response generation pipeline with query decomposition."""
    
    def __init__(
        self,
        retriever: RetrieverService,
        llm_router: LLMRouter,
        conversation_service: ConversationService,
        query_decomposer=None
    ):
        """
        Initialize response pipeline.
        """
        self.retriever = retriever
        self.retrieval_coordinator = RetrievalCoordinator(retriever)
        self.llm_router = llm_router
        self.conversation_service = conversation_service
        self.query_decomposer = query_decomposer
        self.prompt_settings = get_prompt_settings()
        self.semantic_cache = get_semantic_cache()
        
        logger.info(
            f"ResponsePipeline initialized "
            f"(decomposer={'enabled' if query_decomposer else 'disabled'})"
        )

    def _preprocess_query(self, query: str) -> Dict[str, Any]:
        """
        Preprocess query using simple preprocessing and stop-word removal.

        returns Dict with preprocessed query info
        """
        preprocessing_result = preprocess_query(query)
        optimized_query = preprocessing_result.queries[0]
        
        return {
            "primary_query": optimized_query,
            "all_queries": [optimized_query],
            "decomposition_result": preprocessing_result,
            "strategy": "preprocessed"
        }

    
    async def process_query(
        self,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Process and potentially decompose a query.
        
        If LLM decomposer is enabled: Use LLM to decompose query
        If decomposer is disabled: Use preprocessing for query optimization
        
        Returns:
            Dict with processed query info:
            - 'primary_query': Main query to use for retrieval
            - 'all_queries': List of all queries (decomposed or single optimized)
            - 'decomposition_result': Full result (from decomposer or preprocessor)
            - 'strategy': Processing strategy used
        """
        # Check if decomposer is available and enabled in settings
        if not self.query_decomposer or not settings.llm_settings.ENABLE_QUERY_DECOMPOSER:
            # No decomposer - use preprocessing instead
            logger.debug("LLM decomposer disabled, using query preprocessing")
            return self._preprocess_query(user_query)
        
        try:
            # Attempt LLM query decomposition
            decomposition_result = await self.query_decomposer.decompose(user_query)
            
            if decomposition_result and decomposition_result.queries:
                all_queries = decomposition_result.queries
                primary = all_queries[0]
                
                logger.info(
                    f"Query decomposed: {len(all_queries)} queries "
                    f"(decomposed={decomposition_result.decomposed})"
                )
                
                return {
                    "primary_query": primary,
                    "all_queries": all_queries,
                    "decomposition_result": decomposition_result,
                    "strategy": "decomposed" if decomposition_result.decomposed else "llm_optimized"
                }
            else:
                # Decomposition failed - fallback to preprocessing
                logger.warning("Query decomposition returned empty, falling back to preprocessing")
                
                return self._preprocess_query(user_query)
        
        except Exception as e:
            logger.error(f"Error in query decomposition: {e}, falling back to preprocessing", exc_info=True)
            
            # Fallback to preprocessing on error
            return self._preprocess_query(user_query)
    
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
        
        Delegates to RetrievalCoordinator for actual retrieval logic.
        
        Args:
            user_query: User's original question (used for reranking)
            user_clearance: User's organization-level clearance
            user_department_id: User's department ID
            user_dept_clearance: User's department-level clearance
            user_id: User ID for logging
            decomposed_queries: Optional list of decomposed queries to retrieve
            
        Returns:
            Retrieval result dict with success status, documents, and metadata
        """
        return await self.retrieval_coordinator.retrieve_context(
            user_query=user_query,
            user_clearance=user_clearance,
            user_department_id=user_department_id,
            user_dept_clearance=user_dept_clearance,
            user_id=user_id,
            decomposed_queries=decomposed_queries
        )
    
    async def _cache_response(
        self,
        user_query: str,
        response_text: str,
        documents: List[Any]
    ):
        """
        Cache the generated response with security metadata from documents.
        
        Args:
            user_query: Original user query
            response_text: Generated response to cache
            documents: Context documents used (for security metadata)
        """
        try:
            # Extract security metadata from documents
            min_security_level = None
            is_departmental = False
            department_ids = set()
            
            for doc in documents:
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                
                # Track max security level
                sec_level = metadata.get('min_security_level')
                if sec_level is not None:
                    if min_security_level is None:
                        min_security_level = sec_level
                    else:
                        min_security_level = max(min_security_level, sec_level)
                
                # Track departmental status
                if metadata.get('is_departmental'):
                    is_departmental = True
                    dept_id = metadata.get('department_id')
                    if dept_id:
                        department_ids.add(dept_id)
            
            # Store in response cache
            await self.semantic_cache.set(
                cache_type="response",
                query=user_query,
                entry=response_text,
                min_security_level=min_security_level,
                is_departmental=is_departmental,
                department_ids=list(department_ids) if department_ids else None
            )
            
            logger.debug(
                f"Cached response (sec_level={min_security_level}, "
                f"dept={is_departmental}, query='{user_query[:50]}...')"
            )
            
        except Exception as e:
            logger.error(f"Failed to cache response: {e}", exc_info=True)
    
    def select_llm(self, max_doc_level: Optional[int]) -> Tuple[Any, LLMType]:
        """
        Select appropriate LLM based on document security.
        
        Args:
            max_doc_level: Maximum document security level
            
        Returns:
            Tuple of (llm instance, llm type)
        """
        max_doc_label = "NONE"
        if max_doc_level is not None:
            try:
                max_doc_label = PermissionLevel(max_doc_level).name
            except ValueError:
                max_doc_label = str(max_doc_level)
        
        llm, llm_type = self.llm_router.select_llm(max_doc_level)
        logger.info(f"Selected {llm_type.value} LLM for max_level={max_doc_label}")
        
        return llm, llm_type
    
    async def stream_rag_response(
        self,
        llm: Any,
        llm_type: LLMType,
        user_query: str,
        documents: List[Any],
        conversation_id: str,
        user_id: int,
        partial_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming RAG response with fallback on error.
        
        If primary LLM fails with transient error, tries fallback LLM.
        
        Args:
            llm: Primary LLM instance
            llm_type: Primary LLM type
            user_query: User's question
            documents: Retrieved context documents
            conversation_id: Conversation ID
            user_id: User ID
            partial_context: Optional partial context metadata for specialized prompting
            
        Yields:
            Stream chunks with tokens, metadata, or errors
        """
        primary_exception = None
        attempted_fallback = False
        fallback_exception = None
        
        # Get conversation history
        history = await self.conversation_service.get_conversation_history(conversation_id, user_id)
        
        try:
            async for item in self._try_stream(
                llm=llm,
                user_query=user_query,
                documents=documents,
                history=history,
                conversation_id=conversation_id,
                user_id=user_id,
                partial_context=partial_context
            ):
                yield item
            return
        
        except Exception as e:
            primary_exception = e
            logger.error(f"Primary LLM error ({llm_type.value}): {e}", exc_info=True)
            
            # Determine if we should try fallback
            should_retry, reason = LLMErrorHandler.should_retry_with_fallback(
                e,
                fallback_configured=self.llm_router.is_fallback_configured()
            )
            
            logger.info(f"Fallback decision: {reason}")
            
            if should_retry in [ErrorShouldRetry.YES, ErrorShouldRetry.LAST_RESORT]:
                fallback_llm = self.llm_router.get_fallback_llm()
                if fallback_llm:
                    attempted_fallback = True
                    logger.info("Attempting fallback LLM")
                    try:
                        async for item in self._try_stream(
                            llm=fallback_llm,
                            user_query=user_query,
                            documents=documents,
                            history=history,
                            conversation_id=conversation_id,
                            user_id=user_id,
                            is_fallback=True,
                            partial_context=partial_context
                        ):
                            yield item
                        return
                    except Exception as fallback_err:
                        fallback_exception = fallback_err
                        logger.error(f"Fallback LLM also failed: {fallback_err}", exc_info=True)
        
        # If we get here, both primary and potentially fallback failed
        error_response = LLMErrorHandler.format_error_response(
            original_exception=primary_exception,
            attempted_fallback=attempted_fallback,
            fallback_exception=fallback_exception
        )
        
        logger.error(f"Response generation failed: {error_response['message']}")
        yield {"type": "error", "content": error_response["message"]}
    
    async def generate_rag_response(
        self,
        llm: Any,
        llm_type: LLMType,
        user_query: str,
        documents: List[Any],
        conversation_id: str,
        user_id: int,
        partial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate complete RAG response (non-streaming) with fallback.
            
        Returns:
            Generated response text
            
        Raises:
            Exception: If generation fails (after trying fallback if applicable)
        """
        primary_exception = None
        attempted_fallback = False
        fallback_exception = None
        
        # Get conversation history
        history = await self.conversation_service.get_conversation_history(conversation_id, user_id)
        
        try:
            return await self._try_generate(
                llm=llm,
                user_query=user_query,
                documents=documents,
                history=history,
                is_fallback=False,
                partial_context=partial_context
            )
        
        except Exception as e:
            primary_exception = e
            logger.error(f"Primary LLM error ({llm_type.value}): {e}", exc_info=True)
            
            # Determine if we should try fallback
            should_retry, reason = LLMErrorHandler.should_retry_with_fallback(
                e,
                fallback_configured=self.llm_router.is_fallback_configured()
            )
            
            logger.info(f"Fallback decision: {reason}")
            
            if should_retry in [ErrorShouldRetry.YES, ErrorShouldRetry.LAST_RESORT]:
                fallback_llm = self.llm_router.get_fallback_llm()
                if fallback_llm:
                    attempted_fallback = True
                    logger.info("Attempting fallback LLM")
                    try:
                        return await self._try_generate(
                            llm=fallback_llm,
                            user_query=user_query,
                            documents=documents,
                            history=history,
                            is_fallback=True,
                            partial_context=partial_context
                        )
                    except Exception as fallback_err:
                        fallback_exception = fallback_err
                        logger.error(f"Fallback LLM also failed: {fallback_err}", exc_info=True)
            
            # If we get here, both failed or we shouldn't retry
            error_response = LLMErrorHandler.format_error_response(
                original_exception=primary_exception,
                attempted_fallback=attempted_fallback,
                fallback_exception=fallback_exception
            )
            
            logger.error(f"Response generation failed: {error_response['message']}")
            raise Exception(error_response["message"])
    
    async def _try_stream(
        self,
        llm: Any,
        user_query: str,
        documents: List[Any],
        history: List[Dict[str, str]],
        conversation_id: str,
        user_id: int,
        is_fallback: bool = False,
        partial_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Attempt streaming response generation with given LLM.
        
        Yields tokens and metadata. Persists successful response to DB.
        """
        # Build context from documents
        context_text = "\n\n".join([
            f"{doc.page_content}"
            for doc in documents
        ])
        
        # Select appropriate system prompt based on partial context
        system_prompt = self._select_prompt(partial_context)
        
        # Build human message with partial context details if applicable
        human_message = self._build_human_message(user_query, context_text, partial_context)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", human_message)
        ])
        
        # Convert history to LangChain messages
        history_messages = self._convert_history_to_messages(history)
        
        # Create chain with history
        chain = prompt | llm
        
        # Stream response
        full_response = ""
        async for chunk in chain.astream({
            "history": history_messages
        }):
            content = chunk.content if hasattr(chunk, 'content') else str(chunk)
            full_response += content
            yield {"type": "token", "content": content}
        
        sources = self._build_sources_payload(documents)
        
        # Build metadata
        meta = {"sources": sources} if sources else {}
        if is_fallback:
            meta["used_fallback_llm"] = True
        if partial_context:
            meta["partial_context"] = partial_context
        
        # Cache the complete response after streaming
        await self._cache_response(user_query, full_response, documents)
        
        # Save response (cache + persist)
        await self.conversation_service.save_assistant_response(
            conversation_id=conversation_id,
            user_id=user_id,
            user_query=user_query,
            response_text=full_response,
            assistant_meta=meta if meta else None
        )
        
        if sources:
            yield {"type": "metadata", "sources": sources}

        logger.info(f"Streaming completed for conversation {conversation_id}")
    
    async def _try_generate(
        self,
        llm: Any,
        user_query: str,
        documents: List[Any],
        history: List[Dict[str, str]],
        is_fallback: bool = False,
        partial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Attempt response generation with given LLM."""
        # Build context
        context_text = "\n\n".join([
            f"{doc.page_content}"
            for doc in documents
        ])
        
        # Select appropriate system prompt based on partial context
        system_prompt = self._select_prompt(partial_context)
        
        # Build human message with partial context details if applicable
        human_message = self._build_human_message(user_query, context_text, partial_context)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", human_message)
        ])
        
        # Convert history
        history_messages = self._convert_history_to_messages(history)
        
        # Generate
        chain = prompt | llm
        response = await chain.ainvoke({
            "history": history_messages
        })
        
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Cache the response
        await self._cache_response(user_query, response_text, documents)
        
        return response_text
    
    def _convert_history_to_messages(self, history: List[Dict[str, str]]) -> List[Any]:
        """Convert history dicts to LangChain message objects."""
        history_messages = []
        for msg in history:
            if msg["role"] == "user":
                history_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                history_messages.append(SystemMessage(content=msg["content"]))
        return history_messages
    
    def _build_sources_payload(self, documents: List[Any]) -> List[Dict[str, Any]]:
        """Extract lightweight source metadata for the frontend."""
        sources: List[Dict[str, Any]] = []
        for doc in documents:
            metadata = getattr(doc, "metadata", {}) or {}
            source_name = (
                metadata.get("title")
                or metadata.get("source")
                or metadata.get("document_id")
                or metadata.get("path")
                or "Document"
            )
            score = metadata.get("score") or metadata.get("similarity") or metadata.get("relevance", 0)
            try:
                score_val = float(score) if score is not None else 0.0
            except (TypeError, ValueError):
                score_val = 0.0

            sources.append({
                "document": source_name,
                "score": max(0.0, min(score_val, 1.0)),
                "chunk_index": metadata.get("chunk_index"),
                "security_level": metadata.get("security_level"),
            })

        return sources    
    def _select_prompt(self, partial_context: Optional[Dict[str, Any]]) -> str:
        """
        Select appropriate system prompt based on partial context type.
        
        Args:
            partial_context: Partial context metadata if applicable
            
        Returns:
            Appropriate system prompt string
        """
        if not partial_context or not partial_context.get("is_partial"):
            return self.prompt_settings.RAG_SYSTEM_PROMPT
        
        # Determine type of partial context
        context_type = partial_context.get("type", "missing")
        
        if context_type == "clearance":
            # Some subqueries blocked by security clearance
            logger.info("Using clearance-based partial context prompt")
            return self.prompt_settings.PARTIAL_CONTEXT_CLEARANCE_PROMPT
        else:
            # Some subqueries had no matching documents
            logger.info("Using missing-data partial context prompt")
            return self.prompt_settings.PARTIAL_CONTEXT_MISSING_PROMPT
    
    def _build_human_message(
        self,
        user_query: str,
        context_text: str,
        partial_context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build human message with context and optional partial context details.
        
        Args:
            user_query: User's question
            context_text: Retrieved context documents as text
            partial_context: Optional partial context metadata
            
        Returns:
            Formatted human message string
        """
        # Base message parts
        parts = []
        
        # Add context
        if context_text:
            parts.append(f"Context:\n{context_text}")
        else:
            parts.append("Context:\nNo relevant context found.")
        
        # Add partial context details if applicable
        if partial_context and partial_context.get("is_partial"):
            parts.append("\n--- Query Decomposition Results ---")
            parts.append(f"Total subqueries: {partial_context.get('total_queries', 0)}")
            parts.append(f"Satisfied: {partial_context.get('satisfied_count', 0)}")
            
            satisfied = partial_context.get("satisfied_queries", [])
            if satisfied:
                parts.append(f"\nSubqueries with results:")
                for q in satisfied:
                    parts.append(f"  - {q}")
            
            clearance_blocked = partial_context.get("clearance_blocked_queries", [])
            if clearance_blocked:
                parts.append(f"\nSubqueries blocked by clearance:")
                for q in clearance_blocked:
                    parts.append(f"  - {q}")
            
            unsatisfied = partial_context.get("unsatisfied_queries", [])
            if unsatisfied:
                parts.append(f"\nSubqueries with no matches:")
                for q in unsatisfied:
                    parts.append(f"  - {q}")
        
        # Add question
        parts.append(f"\nQuestion: {user_query}")
        
        return "\n".join(parts)