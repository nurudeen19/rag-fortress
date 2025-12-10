"""
Conversation Response Generation Service

Simple orchestration:
1. Get user info (clearance, department) from cache
2. Retrieve context with user credentials  
3. Route to appropriate LLM based on document security levels
4. Get conversation history
5. Generate streaming response using LangChain
6. Return stream or error
"""

from typing import Dict, Any, AsyncGenerator, Optional, List, Tuple
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseLanguageModel

from app.services.vector_store.retriever import get_retriever_service
from app.services.llm_router_service import get_llm_router, LLMType
from app.services.conversation.service import ConversationService
from app.services import activity_logger_service
from app.utils.user_clearance_cache import get_user_clearance_cache
from app.utils.text_processing import preprocess_query
from app.utils.llm_error_handler import LLMErrorHandler, ErrorShouldRetry
from app.utils.intent_classifier import get_intent_classifier, IntentType
from app.config.prompt_settings import get_prompt_settings
from app.config.response_templates import get_template_response
from app.config.settings import settings
from app.models.user_permission import PermissionLevel
from app.models.message import MessageRole
from app.core import get_logger

logger = get_logger(__name__)


class ConversationResponseService:
    """
    Simple orchestrator for AI response generation.
    
    Flow: User info → Context retrieval → LLM routing → History → Stream response
    """
    
    def __init__(self, session):
        self.session = session
        self.retriever = get_retriever_service()
        self.llm_router = get_llm_router()
        self.conversation_service = ConversationService(session)
        self.prompt_settings = get_prompt_settings()
        
        # Initialize intent classifier if enabled
        self.intent_classifier = None
        if settings.ENABLE_INTENT_CLASSIFIER:
            self.intent_classifier = get_intent_classifier(
                confidence_threshold=settings.INTENT_CONFIDENCE_THRESHOLD
            )
            logger.info("Intent classifier enabled")
    
    async def generate_response(
        self,
        conversation_id: str,
        user_id: int,
        user_query: str,
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        Generate AI response with security filtering.
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            user_query: User's question
            stream: Whether to return streaming response
            
        Returns:
            Dict with success status and either generator or error
        """
        try:
            # Step 0: Intent Classification Interceptor
            # Check if this is a simple pleasantry/greeting that doesn't need RAG pipeline
            if self.intent_classifier:
                intent_result = self.intent_classifier.classify(user_query)
                
                # If we should use a template response (high confidence non-knowledge query)
                if self.intent_classifier.should_use_template(intent_result):                    
                    # Return template response directly without RAG pipeline
                    if stream:
                        return {
                            "success": True,
                            "streaming": True,
                            "generator": self._stream_template_response(
                                intent=intent_result.intent,
                                conversation_id=conversation_id,
                                user_id=user_id,
                                user_query=user_query
                            )
                        }
                    else:
                        template_response = get_template_response(intent_result.intent)
                        
                        # Cache and persist the template response
                        await self.conversation_service.cache_conversation_exchange(
                            conversation_id,
                            user_query,
                            template_response,
                            user_id=user_id,
                            persist_to_db=False,
                            assistant_meta={"intent": intent_result.intent.value}
                        )
                        
                        await self.conversation_service.add_message(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            role=MessageRole.ASSISTANT,
                            content=template_response,
                            token_count=None,
                            meta={"intent": intent_result.intent.value}
                        )
                        
                        return {
                            "success": True,
                            "streaming": False,
                            "response": template_response
                        }
            
            # Step 1: Get user info from cache (clearance, department)
            user_info = await self._get_user_info(user_id)
            if not user_info:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "message": "User information not found"
                }
            
            user_clearance = user_info["clearance"]
            user_department_id = user_info.get("department_id")
            user_dept_clearance = user_info.get("department_security_level")
            
            # Step 2: Retrieve context with user credentials
            # (Query preprocessing, caching, and adaptive k adjustment all handled by retriever)
            dept_level_str = f", dept_level={user_dept_clearance.name}" if user_dept_clearance else ""
            logger.info(f"Retrieving context for user_id={user_id}, org_level={user_clearance.name}{dept_level_str}")
            
            retrieval_result = await self.retriever.query(
                query_text=user_query,
                user_security_level=user_clearance.value,
                user_department_id=user_department_id,
                user_department_security_level=user_dept_clearance.value if user_dept_clearance else None,
                user_id=user_id
            )
            
            # Handle retrieval errors (access denied, etc.)
            if not retrieval_result["success"]:
                error_type = retrieval_result.get("error", "retrieval_error")
                logger.warning(f"Retrieval failed: {error_type}")
                
                # Log no-retrieval events to activity logs for analysis
                if error_type in ["no_documents", "low_quality_results", "reranker_no_quality"]:
                    try:
                        await activity_logger_service.log_activity(
                            db=self.session,
                            user_id=user_id,
                            incident_type="retrieval_no_context",
                            severity="info",
                            description=f"No context retrieved: {error_type}",
                            user_query=user_query[:500],  # Truncate long queries
                            details=retrieval_result.get("details")
                        )
                    except Exception as e:
                        logger.error(f"Failed to log no-retrieval event: {e}")
                
                # Generate appropriate response based on error type
                if stream:
                    return {
                        "success": True,  # Consider this successful - we're returning a valid response
                        "streaming": True,
                        "generator": self._stream_no_context_response(
                            error_type=error_type,
                            user_query=user_query,
                            conversation_id=conversation_id,
                            user_id=user_id
                        )
                    }
                else:
                    response_text = self._get_no_context_response_text(error_type)
                    return {
                        "success": True,
                        "streaming": False,
                        "response": response_text
                    }
            
            # Extract documents and their max security level
            documents = retrieval_result["context"]
            max_doc_level = retrieval_result.get("max_security_level")
            
            max_doc_label = "NONE"
            if max_doc_level is not None:
                try:
                    max_doc_label = PermissionLevel(max_doc_level).name
                except ValueError:
                    max_doc_label = str(max_doc_level)
            logger.info(f"Retrieved {len(documents)} documents, max_level={max_doc_label}")

            # Step 3: Route to appropriate LLM based on document security
            llm, llm_type = self.llm_router.select_llm(max_doc_level)
            logger.info(f"Selected {llm_type.value} LLM for this request")
            
            # Step 4: Get conversation history
            history = await self.conversation_service.get_conversation_history(conversation_id, user_id)
            
            # Step 5: Generate streaming response using LangChain
            if stream:
                return {
                    "success": True,
                    "streaming": True,
                    "generator": self._stream_response(
                        llm=llm,
                        llm_type=llm_type,
                        user_query=user_query,
                        documents=documents,
                        history=history,
                        conversation_id=conversation_id,
                        user_id=user_id
                    )
                }
            else:
                # Non-streaming (if needed)
                response_text = await self._generate_complete_response(
                    llm=llm,
                    llm_type=llm_type,
                    user_query=user_query,
                    documents=documents,
                    history=history
                )
                sources = self._build_sources_payload(documents)
                
                # Cache the exchange (don't persist user message again)
                await self.conversation_service.cache_conversation_exchange(
                    conversation_id,
                    user_query,
                    response_text,
                    user_id=user_id,
                    persist_to_db=False,
                    assistant_meta={"sources": sources} if sources else None
                )
                
                # Persist only the assistant message to DB
                await self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role=MessageRole.ASSISTANT,
                    content=response_text,
                    token_count=None,
                    meta={"sources": sources} if sources else None
                )
                
                return {
                    "success": True,
                    "streaming": False,
                    "response": response_text
                }
        
        except Exception as e:
            logger.error(f"Response generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": "generation_error",
                "message": str(e)
            }
    
    def _get_no_context_response_text(self, error_type: str) -> str:
        """Get response when no context is available."""
        return self.prompt_settings.NO_CONTEXT_RESPONSE
    
    async def _stream_no_context_response(
        self,
        error_type: str,
        user_query: str,
        conversation_id: str,
        user_id: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a response when no relevant context is found."""
        # Get appropriate message based on error type
        response_text = self._get_no_context_response_text(error_type)
        
        # Stream the message word by word for consistency
        words = response_text.split()
        for word in words:
            yield {"type": "token", "content": word + " "}
        
        # Persist the response
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            token_count=None,
            meta={"source": "no_context", "error_type": error_type}
        )
        
        logger.info(f"Completed no-context response for conversation {conversation_id}")
    
    async def _get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user info from cache (clearance, department).
        
        Fetches from clearance cache which includes security level with overrides.
        If not cached, automatically fetches from DB and caches it.
        
        Returns:
            Dict with 'clearance' (PermissionLevel) and 'department_id' (int or None)
        """
        try:
            
            clearance_cache = get_user_clearance_cache(self.session)
            clearance = await clearance_cache.get_clearance(user_id)
            
            if not clearance:
                logger.warning(f"User clearance not found for user_id={user_id}")
                return None
            
            # Convert security level strings to PermissionLevel enums
            dept_security_level = None
            if clearance.get("department_security_level"):
                dept_security_level = PermissionLevel[clearance["department_security_level"]]
            
            return {
                "clearance": PermissionLevel[clearance["security_level"]],
                "department_security_level": dept_security_level,
                "department_id": clearance["department_id"]
            }
        
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    

    
    async def _stream_response(
        self,
        llm: Any,
        llm_type: LLMType,
        user_query: str,
        documents: List[Any],
        history: List[Dict[str, str]],
        conversation_id: str,
        user_id: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming response using LangChain with fallback on error.
        
        If primary LLM fails with a transient error, tries fallback LLM.
        Returns error if: auth/config error, or no fallback configured, or fallback also fails.
        """
        primary_exception = None
        attempted_fallback = False
        fallback_exception = None
        
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
        Yields tokens or error. Persists successful response to DB.
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
        history_messages = []
        for msg in history:
            if msg["role"] == "user":
                history_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                history_messages.append(SystemMessage(content=msg["content"]))
        
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
        # But only persist assistant message to DB since user message was saved in handler
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
    
    async def _generate_complete_response(
        self,
        llm: Any,
        llm_type: LLMType,
        user_query: str,
        documents: List[Any],
        history: List[Dict[str, str]]
    ) -> str:
        """
        Generate complete non-streaming response with fallback on error.
        
        If primary LLM fails with transient error, tries fallback.
        Raises exception if: auth/config error, no fallback, or fallback also fails.
        """
        primary_exception = None
        attempted_fallback = False
        fallback_exception = None
        
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
        history_messages = []
        for msg in history:
            if msg["role"] == "user":
                history_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                history_messages.append(SystemMessage(content=msg["content"]))
        
        # Generate
        chain = prompt | llm
        response = await chain.ainvoke({
            "context": context_text if context_text else "No relevant context found.",
            "question": user_query,
            "history": history_messages
        })
        
        return response.content if hasattr(response, 'content') else str(response)

    async def _stream_template_response(
        self,
        intent: IntentType,
        conversation_id: str,
        user_id: int,
        user_query: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a template response for simple intents.
        
        Simulates streaming behavior to maintain consistent UX with RAG responses.
        Streams character-by-character with small delays for natural feel.
        """
        import asyncio
        
        # Get template response
        template_response = get_template_response(intent)
        
        # Stream character by character for natural feel
        for char in template_response:
            yield {"type": "token", "content": char}
            # Small delay to simulate streaming (adjust as needed)
            await asyncio.sleep(0.01)
        
        # Cache and persist the template response
        await self.conversation_service.cache_conversation_exchange(
            conversation_id,
            user_query,
            template_response,
            user_id=user_id,
            persist_to_db=False,
            assistant_meta={"intent": intent.value, "template_response": True}
        )
        
        await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=template_response,
            token_count=None,
            meta={"intent": intent.value, "template_response": True}
        )
        
        logger.info(f"Template response streamed for intent: {intent.value}")
    
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
    

def get_conversation_response_service(session) -> ConversationResponseService:
    """Get conversation response service instance."""
    return ConversationResponseService(session)
