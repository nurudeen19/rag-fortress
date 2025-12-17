"""
Conversation Response Generation Service

Clean orchestration service that delegates to specialized components:
- IntentHandler: Template responses for simple queries
- ResponsePipeline: RAG response generation
- ErrorResponseHandler: Error response formatting
- ConversationActivityLogger: Activity logging
"""

from typing import Dict, Any, AsyncGenerator, Optional

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
from app.config.settings import settings
from app.models.message import MessageRole
from app.core import get_logger

logger = get_logger(__name__)


class ConversationResponseService:
    """
    Clean orchestrator for AI response generation.
    
    Delegates to specialized components for single-responsibility design.
    """
    
    def __init__(self, session):
        self.session = session
        
        # Core services
        self.conversation_service = ConversationService(session)
        self.user_service = UserAccountService(session)
        retriever = get_retriever_service()
        llm_router = get_llm_router()
        
        # Initialize specialized components
        self.pipeline = ResponsePipeline(retriever, llm_router, self.conversation_service)
        self.error_handler = ErrorResponseHandler(self.conversation_service)
        
        # Initialize intent classifier if enabled
        intent_classifier = None
        if settings.ENABLE_INTENT_CLASSIFIER:
            intent_classifier = get_intent_classifier(
                confidence_threshold=settings.INTENT_CONFIDENCE_THRESHOLD
            )
            logger.info("Intent classifier enabled")
        
        self.intent_handler = IntentHandler(intent_classifier, self.conversation_service)
    
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
        1. Check for template intent (greetings, pleasantries)
        2. Get user info (clearance, department)
        3. Retrieve context with security filtering
        4. Handle retrieval errors (no context, insufficient clearance)
        5. Select appropriate LLM and generate response
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            user_query: User's question
            stream: Whether to return streaming response
            
        Returns:
            Dict with success status and either generator or error
        """
        try:
            # Step 1: Intent Classification Interceptor
            # Check if this is a simple query that doesn't need RAG pipeline
            intent_result = self.intent_handler.should_use_template(user_query)
            if intent_result:
                logger.info(f"Using template response for intent: {intent_result.intent.value}")
                
                if stream:
                    return {
                        "success": True,
                        "streaming": True,
                        "generator": self.intent_handler.generate_template_response_streaming(
                            intent=intent_result.intent,
                            conversation_id=conversation_id,
                            user_id=user_id,
                            user_query=user_query
                        )
                    }
                else:
                    template_response = await self.intent_handler.generate_template_response(
                        intent=intent_result.intent,
                        conversation_id=conversation_id,
                        user_id=user_id,
                        user_query=user_query
                    )
                    
                    return {
                        "success": True,
                        "streaming": False,
                        "response": template_response
                    }
            
            # Step 2: Get user info from cache (clearance, department)
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
            
            # Step 3: Retrieve context with user credentials
            retrieval_result = await self.pipeline.retrieve_context(
                user_query=user_query,
                user_clearance=user_clearance,
                user_department_id=user_department_id,
                user_dept_clearance=user_dept_clearance,
                user_id=user_id
            )
            
            # Step 4: Handle retrieval errors
            if not retrieval_result["success"]:
                return await self._handle_retrieval_error(
                    retrieval_result=retrieval_result,
                    user_query=user_query,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    stream=stream
                )
            
            # Extract documents and their max security level
            documents = retrieval_result["context"]
            max_doc_level = retrieval_result.get("max_security_level")
            
            logger.info(f"Retrieved {len(documents)} documents")

            # Step 5: Route to appropriate LLM and generate response
            llm, llm_type = self.pipeline.select_llm(max_doc_level)
            
            if stream:
                return {
                    "success": True,
                    "streaming": True,
                    "generator": self.pipeline.stream_rag_response(
                        llm=llm,
                        llm_type=llm_type,
                        user_query=user_query,
                        documents=documents,
                        conversation_id=conversation_id,
                        user_id=user_id
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
                    user_id=user_id
                )
                
                sources = self.pipeline._build_sources_payload(documents)
                
                # Cache and persist response
                await self.conversation_service.cache_conversation_exchange(
                    conversation_id,
                    user_query,
                    response_text,
                    user_id=user_id,
                    persist_to_db=False,
                    assistant_meta={"sources": sources} if sources else None
                )
                
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
