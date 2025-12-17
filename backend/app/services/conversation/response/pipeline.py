"""
Response Pipeline

Orchestrates the RAG response generation process.
Handles retrieval, LLM routing, prompt construction, streaming, and fallback logic.
"""

from typing import Dict, Any, AsyncGenerator, List, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.vector_store.retriever import RetrieverService
from app.services.llm import LLMRouter, LLMType
from app.services.conversation.service import ConversationService
from app.utils.llm_error_handler import LLMErrorHandler, ErrorShouldRetry
from app.config.prompt_settings import get_prompt_settings
from app.models.user_permission import PermissionLevel
from app.models.message import MessageRole
from app.core import get_logger

logger = get_logger(__name__)


class ResponsePipeline:
    """Orchestrates RAG response generation pipeline."""
    
    def __init__(
        self,
        retriever: RetrieverService,
        llm_router: LLMRouter,
        conversation_service: ConversationService
    ):
        """
        Initialize response pipeline.
        
        Args:
            retriever: Vector store retriever service
            llm_router: LLM router service
            conversation_service: Conversation service for history/persistence
        """
        self.retriever = retriever
        self.llm_router = llm_router
        self.conversation_service = conversation_service
        self.prompt_settings = get_prompt_settings()
    
    async def retrieve_context(
        self,
        user_query: str,
        user_clearance: PermissionLevel,
        user_department_id: Optional[int],
        user_dept_clearance: Optional[PermissionLevel],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Retrieve context documents for query.
        
        Args:
            user_query: User's question
            user_clearance: User's organization-level clearance
            user_department_id: User's department ID
            user_dept_clearance: User's department-level clearance
            user_id: User ID for logging
            
        Returns:
            Retrieval result dict with success status, documents, and metadata
        """
        dept_level_str = f", dept_level={user_dept_clearance.name}" if user_dept_clearance else ""
        logger.info(f"Retrieving context for user_id={user_id}, org_level={user_clearance.name}{dept_level_str}")
        
        retrieval_result = await self.retriever.query(
            query_text=user_query,
            user_security_level=user_clearance.value,
            user_department_id=user_department_id,
            user_department_security_level=user_dept_clearance.value if user_dept_clearance else None,
            user_id=user_id
        )
        
        return retrieval_result
    
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
        user_id: int
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
                user_id=user_id
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
                            is_fallback=True
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
        user_id: int
    ) -> str:
        """
        Generate complete RAG response (non-streaming) with fallback.
        
        Args:
            llm: Primary LLM instance
            llm_type: Primary LLM type
            user_query: User's question
            documents: Retrieved context documents
            conversation_id: Conversation ID
            user_id: User ID
            
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
                is_fallback=False
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
                            is_fallback=True
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
        is_fallback: bool = False
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
        
        # Use configurable system prompt
        system_prompt = self.prompt_settings.RAG_SYSTEM_PROMPT
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Context:\n{context}\n\nQuestion: {question}")
        ])
        
        # Convert history to LangChain messages
        history_messages = self._convert_history_to_messages(history)
        
        # Create chain with history
        chain = prompt | llm
        
        # Stream response
        full_response = ""
        async for chunk in chain.astream({
            "context": context_text if context_text else "No relevant context found.",
            "question": user_query,
            "history": history_messages
        }):
            content = chunk.content if hasattr(chunk, 'content') else str(chunk)
            full_response += content
            yield {"type": "token", "content": content}
        
        sources = self._build_sources_payload(documents)
        
        # Cache the exchange (updates cache with both messages)
        await self.conversation_service.cache_conversation_exchange(
            conversation_id,
            user_query,
            full_response,
            user_id=user_id,
            persist_to_db=False,  # Don't persist user message again
            assistant_meta={"sources": sources} if sources else None
        )
        
        # Persist only the assistant message to DB
        meta = {"sources": sources} if sources else {}
        if is_fallback:
            meta["used_fallback_llm"] = True
        
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=full_response,
            token_count=None,
            meta=meta
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
        is_fallback: bool = False
    ) -> str:
        """Attempt response generation with given LLM."""
        # Build context
        context_text = "\n\n".join([
            f"{doc.page_content}"
            for doc in documents
        ])
        
        # Use configurable system prompt
        system_prompt = self.prompt_settings.RAG_SYSTEM_PROMPT
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Context:\n{context}\n\nQuestion: {question}")
        ])
        
        # Convert history
        history_messages = self._convert_history_to_messages(history)
        
        # Generate
        chain = prompt | llm
        response = await chain.ainvoke({
            "context": context_text if context_text else "No relevant context found.",
            "question": user_query,
            "history": history_messages
        })
        
        return response.content if hasattr(response, 'content') else str(response)
    
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
