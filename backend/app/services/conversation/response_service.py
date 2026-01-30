"""
Conversation Response Generation Service

Clean orchestration service that delegates to specialized components:
- IntentHandler: Template responses for simple queries (hybrid heuristic + LLM)
- ResponsePipeline: RAG response generation with query decomposition
- ErrorResponseHandler: Error response formatting
- ConversationActivityLogger: Activity logging
"""

from typing import Dict, Any, Optional

from app.services.vector_store.retriever import get_retriever_service
from app.services.llm import get_llm_router
from app.services.conversation.service import ConversationService
from app.services.user.user_service import UserAccountService
from app.services.conversation.response import (
    IntentHandler,
    ResponsePipeline,
    ErrorResponseHandler,
    ConversationActivityLogger
)
from app.core.semantic_cache import get_semantic_cache, is_semantic_cache_enabled
from app.utils.intent_classifier import get_intent_classifier
from app.services.llm.classifier import get_llm_intent_classifier
from app.services.llm.decomposer import get_query_decomposer
from app.config.settings import settings
from app.core import get_logger

logger = get_logger(__name__)


class ConversationResponseService:
    """
    Clean orchestrator for AI response generation.
    
    Delegates to specialized components for single-responsibility design.
    Supports hybrid intent classification and query decomposition.
    """
    
    def __init__(self, session):
        self.session = session
        
        # Core services
        self.conversation_service = ConversationService(session)
        self.user_service = UserAccountService(session)
        retriever = get_retriever_service()
        llm_router = get_llm_router()
        self.semantic_cache = get_semantic_cache()
        
        # Initialize classifier (LLM or heuristic)
        classifier, classifier_type = self._initialize_classifier()
        
        # Initialize query decomposer if enabled
        query_decomposer = self._initialize_decomposer()
        
        # Initialize specialized components
        self._initialize_components(
            retriever,
            llm_router,
            query_decomposer,
            classifier,
            classifier_type
        )
        
        logger.debug(
            f"ConversationResponseService initialized "
            f"(classifier={classifier_type}, "
            f"decomposer={'on' if query_decomposer else 'off'})"
        )
    
    def _initialize_classifier(self) -> tuple[Optional[Any], str]:
        """
        Initialize intent classifier (LLM or heuristic).
        
        Returns:
            Tuple of (classifier instance, classifier_type string)
        """
        classifier = None
        classifier_type = "heuristic"  # default
        
        # Try LLM classifier first if enabled
        if settings.llm_settings.ENABLE_LLM_CLASSIFIER:
            llm_classifier = get_llm_intent_classifier()
            if llm_classifier and llm_classifier.llm:
                classifier = llm_classifier
                classifier_type = "llm"
                logger.info("LLM intent classifier enabled")
            else:
                logger.warning("LLM classifier initialization failed, falling back to heuristic")
        
        # Fall back to heuristic classifier if LLM not available
        if classifier is None:
            classifier = get_intent_classifier()
            classifier_type = "heuristic"
            logger.info("Heuristic intent classifier enabled")
        
        return classifier, classifier_type
    
    def _initialize_decomposer(self) -> Any:
        """
        Initialize query decomposer if enabled.
        
        Returns:
            Query decomposer instance or None if disabled/failed
        """
        if not settings.llm_settings.ENABLE_QUERY_DECOMPOSER:
            return None
        
        query_decomposer = get_query_decomposer()
        if query_decomposer and query_decomposer.llm:
            logger.debug("Query decomposer enabled")
            return query_decomposer
        else:
            logger.warning("Query decomposer initialization failed")
            return None
    
    def _initialize_components(
        self,
        retriever: Any,
        llm_router: Any,
        query_decomposer: Any,
        classifier: Any,
        classifier_type: str
    ) -> None:
        """
        Initialize specialized components (pipeline, handlers).
        
        """
        # Initialize response pipeline
        self.pipeline = ResponsePipeline(
            retriever,
            llm_router,
            self.conversation_service,
            query_decomposer
        )
        
        # Initialize error handler
        self.error_handler = ErrorResponseHandler(self.conversation_service)
        
        # Initialize intent handler with classifier
        self.intent_handler = IntentHandler(
            classifier_type,
            self.conversation_service,
            classifier
        )
    
    async def get_classification_result(self, user_query: str) -> Any:
        """
        Get classification result for user query.
        """
        classification_result = await self.intent_handler.classify(user_query)
        
        if classification_result:
            logger.debug(
                f"Intent classification: requires_rag={classification_result.requires_rag}, "
                f"confidence={classification_result.confidence:.2f}, "
                f"source={self.intent_handler.classifier_type}"
            )
        else:
            logger.warning("Classification failed, will default to RAG pipeline")
        
        return classification_result
    
    async def _generate_static_response(
        self,
        handler_method_streaming: Any,
        handler_method_non_streaming: Any,
        stream: bool,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Unified static response generation for both streaming and non-streaming modes.
        
        Handles template responses and error responses (non-RAG static text).
        Routes to appropriate streaming or non-streaming handlers.
                    
        Returns:
            Response dict with success status and either generator or text
        """
        if stream:
            return {
                "success": True,
                "streaming": True,
                "generator": handler_method_streaming(**kwargs)
            }
        else:
            response_text = await handler_method_non_streaming(**kwargs)
            return {
                "success": True,
                "streaming": False,
                "response": response_text
            }
    
    async def _handle_template_response(
        self,
        classification_result: Any,
        conversation_id: str,
        user_id: int,
        user_query: str,
        stream: bool
    ) -> Dict[str, Any]:
        """
        Handle template/direct response without RAG.
            
        Returns:
            Response dict with success status and either generator or text
        """
        response_text = classification_result.response
        
        # Build metadata
        meta = {"classifier": self.intent_handler.classifier_type}
        if hasattr(classification_result, 'intent') and classification_result.intent:
            meta["intent"] = classification_result.intent.value
        
        return await self._generate_static_response(
            handler_method_streaming=self.intent_handler.generate_template_response_streaming,
            handler_method_non_streaming=self.intent_handler.generate_template_response,
            stream=stream,
            response_text=response_text,
            conversation_id=conversation_id,
            user_id=user_id,
            user_query=user_query,
            meta=meta
        )
    
    async def _retrieve_context(
        self,
        user_query: str,
        query_info: dict,
        user_clearance: Any,
        user_department_id: int,
        user_dept_clearance: Any,
        user_id: int,
        conversation_id: str,
        stream: bool
    ) -> Dict[str, Any]:
        """
        Retrieve context documents with security filtering.
        
        Checks context cache first. If hit, returns pre-formatted context.
        If miss, performs retrieval and emits to cache in background.
        
        Returns:
            Dict with either:
            - success=True: documents OR cached_context, max_doc_level, partial_context
            - success=False: error response (already handled)
        """
        # Check context cache first (before retrieval!)        
        if is_semantic_cache_enabled() and self.semantic_cache:
            cache_result, access_denied_info = await self.semantic_cache.get(
                cache_type="context",
                query=user_query,
                min_security_level=user_clearance.value if user_clearance else 0,
                is_department_only=bool(user_dept_clearance),
                department_id=user_department_id if user_dept_clearance else None
            )
            
            if access_denied_info:
                # Cache hit but access denied - return appropriate error
                error_type = "no_clearance" if access_denied_info.get("is_departmental") else "insufficient_clearance"
                error_response = await self._handle_retrieval_error(
                    retrieval_result={"success": False, "error_type": error_type},
                    user_query=user_query,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    stream=stream
                )
                return {"success": False, "error_response": error_response}
            
            if cache_result:
                # Cache hit - return cached context
                logger.info(f"Context cache HIT - using cached formatted context")
                return {
                    "success": True,
                    "cached_context_text": cache_result.get("context_text") if isinstance(cache_result, dict) else cache_result,
                    "max_doc_level": cache_result.get("min_security_level") if isinstance(cache_result, dict) else None,
                    "source_count": cache_result.get("source_count", 0) if isinstance(cache_result, dict) else 0,
                    "from_cache": True
                }
        
        # Cache miss - perform retrieval
        retrieval_result = await self.pipeline.retrieve_context(
            user_query=user_query,
            user_clearance=user_clearance,
            user_department_id=user_department_id,
            user_dept_clearance=user_dept_clearance,
            user_id=user_id,
            decomposition_result=query_info.get("decomposition_result")
        )
        
        # Handle retrieval errors
        if not retrieval_result["success"]:
            error_response = await self._handle_retrieval_error(
                retrieval_result=retrieval_result,
                user_query=user_query,
                conversation_id=conversation_id,
                user_id=user_id,
                stream=stream
            )
            return {"success": False, "error_response": error_response}
        
        # Extract documents and metadata
        documents = retrieval_result["context"]
        max_doc_level = retrieval_result.get("max_security_level")
        partial_context = retrieval_result.get("partial_context")
        security_metadata = retrieval_result.get("security_metadata", {})
        
        logger.info(f"Retrieved {len(documents)} documents")
        if partial_context:
            logger.info(
                f"Partial context: {partial_context['type']}, "
                f"{partial_context['satisfied_count']}/{partial_context['total_queries']} satisfied"
            )
        
        return {
            "success": True,
            "documents": documents,
            "max_doc_level": max_doc_level,
            "partial_context": partial_context,
            "security_metadata": security_metadata
        }
    
    async def _generate_llm_response(
        self,
        documents: Optional[list[Any]],
        cached_context_text: Optional[str],
        max_doc_level: Any,
        partial_context: Dict[str, Any],
        user_query: str,
        conversation_id: str,
        user_id: int,
        stream: bool,
        security_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate LLM response from retrieved documents or cached context.
        
        Handles LLM selection and both streaming/non-streaming generation.
        Accepts either raw documents (first retrieval) or pre-formatted context (cache hit).
        
        Returns:
            Response dict with success status and either generator or text
        """
        # Select appropriate LLM
        llm, llm_type = self.pipeline.select_llm(max_doc_level)
        
        # Use provided security metadata or default to empty dict
        if security_metadata is None:
            security_metadata = {}
        
        if stream:
            return {
                "success": True,
                "streaming": True,
                "generator": self.pipeline.stream_rag_response(
                    llm=llm,
                    llm_type=llm_type,
                    user_query=user_query,
                    documents=documents,
                    cached_context_text=cached_context_text,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    partial_context=partial_context,
                    security_metadata=security_metadata
                )
            }
        else:
            # Non-streaming response
            response_text = await self.pipeline.generate_rag_response(
                llm=llm,
                llm_type=llm_type,
                user_query=user_query,
                documents=documents,
                cached_context_text=cached_context_text,
                conversation_id=conversation_id,
                user_id=user_id,
                partial_context=partial_context,
                security_metadata=security_metadata
            )
            
            # Build sources only if we have documents (not from cache)
            sources = self.pipeline._build_sources_payload(documents) if documents else []
            
            # Save response (cache + persist)
            await self.conversation_service.save_assistant_response(
                conversation_id=conversation_id,
                user_id=user_id,
                user_query=user_query,
                response_text=response_text,
                assistant_meta={"sources": sources} if sources else None
            )
            
            return {
                "success": True,
                "streaming": False,
                "response": response_text
            }
    
    async def _check_response_cache(
        self,
        user_query: str,
        user_clearance: Any,
        user_department_id: int,
        user_dept_clearance: Any,
        stream: bool
    ) -> tuple[Dict[str, Any] | None, bool]:
        """
        Check response cache and return formatted response if found.
        
        Args:
            user_query: User's query
            user_clearance: User's organization-level security clearance
            user_department_id: User's department ID
            user_dept_clearance: User's department-level security clearance
            stream: Whether response should be streamed
            
        Returns:
            Tuple of (response_dict, access_denied_info)
            - response_dict: Formatted response if cache hit at capacity, None otherwise
            - access_denied_info: Dict if access denied, None otherwise
        """
        
        if not is_semantic_cache_enabled() or not self.semantic_cache:
            return None, None
        
        cache_result, access_denied_info = await self.semantic_cache.get(
            cache_type="response",
            query=user_query,
            min_security_level=user_clearance.value if user_clearance else 0,
            is_department_only=bool(user_dept_clearance),
            department_id=user_department_id if user_dept_clearance else None
        )
        
        # Handle access denial
        if access_denied_info:
            logger.info(f"Response cache HIT but ACCESS DENIED for query: '{user_query[:50]}...'")
            return None, access_denied_info
        
        # Handle cache miss
        if not cache_result:
            logger.debug(f"Response cache MISS for query: '{user_query[:50]}...'")
            return None, None
        
        # Cache hit - return cached response
        logger.info(f"Response cache HIT for query: '{user_query[:50]}...'")
        
        if stream:
            # For streaming, wrap cached response in async generator
            async def cached_response_generator():
                yield {"type": "content", "content": cache_result}
                yield {"type": "end"}
            
            return {
                "success": True,
                "streaming": True,
                "generator": cached_response_generator()
            }, None
        else:
            return {
                "success": True,
                "streaming": False,
                "response": cache_result
            }, None
    
    async def _handle_rag_pipeline(
        self,
        user_query: str,
        user_clearance: Any,
        user_department_id: int,
        user_dept_clearance: Any,
        user_id: int,
        conversation_id: str,
        stream: bool
    ) -> Dict[str, Any]:
        """
        Handle RAG pipeline: query processing, retrieval, and response generation.
        
        Returns:
            Response dict with success status and either generator or text
        """
        # Step 0: Check response cache (before entire pipeline)
        cached_result, access_denied_info = await self._check_response_cache(
            user_query=user_query,
            user_clearance=user_clearance,
            user_department_id=user_department_id,
            user_dept_clearance=user_dept_clearance,
            stream=stream
        )
        
        # Handle access denial from cache
        if access_denied_info:
            error_type = "no_clearance" if access_denied_info.get("is_departmental") else "insufficient_clearance"
            if stream:
                return {
                    "success": True,
                    "streaming": True,
                    "generator": self.error_handler.stream_no_context_response(
                        error_type=error_type,
                        user_query=user_query,
                        conversation_id=conversation_id,
                        user_id=user_id
                    )
                }
            else:
                return {
                    "success": True,
                    "streaming": False,
                    "response": await self.error_handler.generate_no_context_response(
                        error_type=error_type,
                        user_query=user_query,
                        conversation_id=conversation_id,
                        user_id=user_id
                    )
                }
        
        # If cache hit at capacity, return cached response immediately
        if cached_result:
            logger.debug("Cache hit at capacity, returning cached response")
            return cached_result
        
        # Cache miss or below max_entries - continue to pipeline
        # Step 1: Query Processing and Decomposition
        query_info = await self.pipeline.process_query(user_query)
        
        all_queries = query_info.get("all_queries", [user_query])
        decomposition_strategy = query_info["strategy"]
        
        logger.debug(
            f"Query processed (strategy={decomposition_strategy}, {len(all_queries)} queries): "
            f"'{user_query[:50]}...'"
        )
        
        # Step 2: Retrieve context with security filtering
        context_result = await self._retrieve_context(
            user_query=user_query,
            query_info=query_info,
            user_clearance=user_clearance,
            user_department_id=user_department_id,
            user_dept_clearance=user_dept_clearance,
            user_id=user_id,
            conversation_id=conversation_id,
            stream=stream
        )
        
        # Return error response if retrieval failed
        if not context_result["success"]:
            return context_result["error_response"]
        
        # Step 3: Generate LLM response from documents or cached context
        return await self._generate_llm_response(
            documents=context_result.get("documents"),
            cached_context_text=context_result.get("cached_context_text"),
            max_doc_level=context_result["max_doc_level"],
            partial_context=context_result.get("partial_context"),
            user_query=user_query,
            conversation_id=conversation_id,
            user_id=user_id,
            stream=stream,
            security_metadata=context_result.get("security_metadata", {})
        )
    
    async def generate_response(
        self,
        conversation_id: str,
        user_id: int,
        user_query: str,
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        Orchestrate AI response generation workflow.
        
        High-level orchestrator that routes requests to appropriate handlers.
        
        Flow:
        1. Get user clearance info
        2. Classify user intent (template vs RAG)
        3. Route to template handler or RAG pipeline
                    
        Returns:
            Dict with success status and either generator or error
        """
        try:
            # Get user info for clearance-based operations
            user_info = await self.user_service.get_user_clearance_info(user_id)
            if not user_info:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "message": "User information not found"
                }
            
            user_clearance = user_info["clearance"]
            user_department_id = user_info.get("department_id")
            user_dept_clearance = user_info.get("department_security_level")
            
            # Step 1: Classify intent
            classification_result = await self.get_classification_result(user_query)
            
            # Step 2: Route to appropriate handler
            if classification_result and not classification_result.requires_rag:
                # Template response path
                return await self._handle_template_response(
                    classification_result=classification_result,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    user_query=user_query,
                    stream=stream
                )
            
            # Step 3: RAG pipeline path
            return await self._handle_rag_pipeline(
                user_query=user_query,
                user_clearance=user_clearance,
                user_department_id=user_department_id,
                user_dept_clearance=user_dept_clearance,
                user_id=user_id,
                conversation_id=conversation_id,
                stream=stream
            )
        
        except Exception as e:
            logger.error(f"Response generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": "generation_error",
                "message": "I encountered an error while generating your response. Please try again."
            }
    
    async def _handle_retrieval_error(
        self,
        retrieval_result: Dict[str, Any],
        user_query: str,
        conversation_id: str,
        user_id: int,
        stream: bool
    ) -> Dict[str, Any]:
        """
        Handle retrieval errors with appropriate logging and responses.
            
        Returns:
            Response dict
        """
        error_type = retrieval_result.get("error", "retrieval_error")
        logger.warning(f"Retrieval failed: {error_type}")
        
        # Log retrieval error - pass error_type directly from retriever
        details = {"message": retrieval_result.get("message")}
        if retrieval_result.get("max_security_level") is not None:
            details["max_security_level"] = retrieval_result.get("max_security_level")
        
        await ConversationActivityLogger.log_retrieval_error(
            user_id=user_id,
            error_type=error_type,
            user_query=user_query,
            details=details
        )
        
        # Generate error response
        return await self._generate_static_response(
            handler_method_streaming=self.error_handler.stream_no_context_response,
            handler_method_non_streaming=self.error_handler.generate_no_context_response,
            stream=stream,
            error_type=error_type,
            user_query=user_query,
            conversation_id=conversation_id,
            user_id=user_id
        )
    

def get_conversation_response_service(session) -> ConversationResponseService:
    """Get conversation response service instance."""
    return ConversationResponseService(session)
