"""
Conversation Response Generation Service

Clean orchestration service that delegates to specialized components:
- IntentHandler: Template responses for simple queries (hybrid heuristic + LLM)
- ResponsePipeline: RAG response generation with query decomposition
- ErrorResponseHandler: Error response formatting
- ConversationActivityLogger: Activity logging
"""

from typing import Dict, Any

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
from app.utils.intent_classifier import get_intent_classifier
from app.services.llm.classifier import get_llm_intent_classifier
from app.services.llm.decomposer import get_query_decomposer
from app.config.settings import settings
from app.models.message import MessageRole
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
        
        # Determine which classifier to use
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
        
        # Initialize query decomposer if enabled
        query_decomposer = None
        if settings.llm_settings.ENABLE_QUERY_DECOMPOSER:
            query_decomposer = get_query_decomposer()
            if query_decomposer and query_decomposer.llm:
                logger.info("Query decomposer enabled")
            else:
                logger.warning("Query decomposer initialization failed")
                query_decomposer = None
        
        # Initialize specialized components
        self.pipeline = ResponsePipeline(
            retriever,
            llm_router,
            self.conversation_service,
            query_decomposer
        )
        self.error_handler = ErrorResponseHandler(self.conversation_service)
        
        # Initialize intent handler with single classifier
        self.intent_handler = IntentHandler(
            classifier_type,
            self.conversation_service,
            classifier
        )
        
        logger.info(
            f"ConversationResponseService initialized "
            f"(classifier={classifier_type}, "
            f"decomposer={'on' if query_decomposer else 'off'})"
        )
    
    async def generate_response(
        self,
        conversation_id: str,
        user_id: int,
        user_query: str,
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        Generate AI response with security filtering.
        
        Flow:
        1. Check for template intent (hybrid heuristic + LLM classification)
        2. Get user info (clearance, department)
        3. Process/decompose query if enabled
        4. Retrieve context with security filtering (using processed query)
        5. Handle retrieval errors (no context, insufficient clearance)
        6. Select appropriate LLM and generate response
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            user_query: User's question
            stream: Whether to return streaming response
            
        Returns:
            Dict with success status and either generator or error
        """
        try:
            # Get user info early for clearance-based operations
            user_info = await self.user_service.get_user_clearance_info(user_id)
            if not user_info:
                return {
                    "success": False,
                    "error": "user_not_found",
                    "message": "User information not found"
                }
            
            user_clearance = user_info["clearance"]
            user_clearance_level = user_clearance.value
            user_department_id = user_info.get("department_id")
            user_dept_clearance = user_info.get("department_security_level")
            
            # Step 1: Intent Classification
            # Get raw classification result from classifier
            classification_result = await self.intent_handler.classify(user_query)
            
            # Check if RAG is required (main decision point)
            if classification_result and not classification_result.requires_rag:
                # Template/direct response - no RAG needed
                confidence = classification_result.confidence
                response_text = classification_result.response
                
                logger.info(
                    f"Intent classification: requires_rag={classification_result.requires_rag}, "
                    f"confidence={confidence:.2f}, source={self.intent_handler.classifier_type}"
                )
                
                # Build metadata
                meta = {"classifier": self.intent_handler.classifier_type}
                if hasattr(classification_result, 'intent') and classification_result.intent:
                    meta["intent"] = classification_result.intent.value
                                
                if stream:
                    return {
                        "success": True,
                        "streaming": True,
                        "generator": self.intent_handler.generate_template_response_streaming(
                            response_text=response_text,
                            conversation_id=conversation_id,
                            user_id=user_id,
                            user_query=user_query,
                            meta=meta
                        )
                    }
                else:
                    response_text = await self.intent_handler.generate_template_response(
                        response_text=response_text,
                        conversation_id=conversation_id,
                        user_id=user_id,
                        user_query=user_query,
                        meta=meta
                    )
                    
                    return {
                        "success": True,
                        "streaming": False,
                        "response": response_text
                    }
            
            # Step 2: Proceed with RAG pipeline
            # Either classifier failed or requires_rag=True
            if not classification_result:
                logger.warning("Classification failed, defaulting to RAG pipeline")            
            
            # Query Processing and Decomposition
            query_info = await self.pipeline.process_query(
                user_query,
                user_clearance_level
            )
            
            processed_query = query_info["primary_query"]
            all_queries = query_info.get("all_queries", [user_query])
            decomposition_strategy = query_info["strategy"]
            
            logger.info(
                f"Query processed (strategy={decomposition_strategy}, {len(all_queries)} queries): "
                f"'{user_query[:50]}...'"
            )
            
            # Step 3: Retrieve context with user credentials
            # Pass all decomposed queries for multi-query retrieval
            retrieval_result = await self.pipeline.retrieve_context(
                user_query=user_query,  # Original query for reranking
                user_clearance=user_clearance,
                user_department_id=user_department_id,
                user_dept_clearance=user_dept_clearance,
                user_id=user_id,
                decomposed_queries=all_queries  # Pass decomposed queries
            )
            
            # Step 4: Handle retrieval errors
            if not retrieval_result["success"]:
                return await self._handle_retrieval_error(
                    retrieval_result=retrieval_result,
                    user_query=user_query,  # Use original query for error messages
                    conversation_id=conversation_id,
                    user_id=user_id,
                    stream=stream
                )
            
            # Extract documents and their max security level
            documents = retrieval_result["context"]
            max_doc_level = retrieval_result.get("max_security_level")
            partial_context = retrieval_result.get("partial_context")
            
            logger.info(f"Retrieved {len(documents)} documents")
            if partial_context:
                logger.info(f"Partial context: {partial_context['type']}, {partial_context['satisfied_count']}/{partial_context['total_queries']} satisfied")

            # Step 5: Route to appropriate LLM and generate response
            # Use original query for LLM prompt (more natural for user)
            llm, llm_type = self.pipeline.select_llm(max_doc_level)
            
            if stream:
                return {
                    "success": True,
                    "streaming": True,
                    "generator": self.pipeline.stream_rag_response(
                        llm=llm,
                        llm_type=llm_type,
                        user_query=user_query,  # Original query for natural response
                        documents=documents,
                        conversation_id=conversation_id,
                        user_id=user_id,
                        partial_context=partial_context
                    )
                }
            else:
                # Non-streaming response
                response_text = await self.pipeline.generate_rag_response(
                    llm=llm,
                    llm_type=llm_type,
                    user_query=user_query,
                    documents=documents,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    partial_context=partial_context
                )
                
                sources = self.pipeline._build_sources_payload(documents)
                
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
        
        Args:
            retrieval_result: Failed retrieval result
            user_query: User's original query
            conversation_id: Conversation ID
            user_id: User ID
            stream: Whether streaming is enabled
            
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
        
        # Generate appropriate response
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
            response_text = await self.error_handler.generate_no_context_response(
                error_type=error_type,
                user_query=user_query,
                conversation_id=conversation_id,
                user_id=user_id
            )
            return {
                "success": True,
                "streaming": False,
                "response": response_text
            }
    

def get_conversation_response_service(session) -> ConversationResponseService:
    """Get conversation response service instance."""
    return ConversationResponseService(session)
