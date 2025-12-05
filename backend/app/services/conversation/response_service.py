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

from typing import Dict, Any, AsyncGenerator, Optional, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.services.vector_store.retriever import get_retriever_service
from app.services.llm_router_service import get_llm_router
from app.services.conversation.service import ConversationService
from app.services import activity_logger_service
from app.utils.user_clearance_cache import get_user_clearance_cache
from app.utils.text_processing import preprocess_query
from app.core.cache import get_cache
from app.models.user_permission import PermissionLevel
from app.models.message import MessageRole
from app.core import get_logger
import hashlib
import json

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
            
            # Preprocess query to remove stop words and noise
            cleaned_query = preprocess_query(user_query)
            
            # Step 2: Retrieve context with user credentials
            # Check cache first
            cache_key_data = {
                "query": cleaned_query,
                "user_clearance": user_clearance.value,
                "user_department_id": user_department_id,
                "user_dept_clearance": user_dept_clearance.value if user_dept_clearance else None
            }
            cache_key = f"retrieval:{hashlib.md5(json.dumps(cache_key_data, sort_keys=True).encode()).hexdigest()}"
            
            cache = get_cache()
            retrieval_result = await cache.get(cache_key)
            
            if not retrieval_result:
                dept_level_str = f", dept_level={user_dept_clearance.name}" if user_dept_clearance else ""
                logger.info(f"Retrieving context for user_id={user_id}, org_level={user_clearance.name}{dept_level_str}")
                
                # Use cleaned query for better retrieval
                retrieval_result = self.retriever.query(
                    query_text=cleaned_query,
                    top_k=5,
                    user_security_level=user_clearance.value,
                    user_department_id=user_department_id,
                    user_department_security_level=user_dept_clearance.value if user_dept_clearance else None,
                    user_id=user_id
                )
                
                # Cache successful results (TTL 5 minutes)
                if retrieval_result["success"]:
                    await cache.set(cache_key, retrieval_result, ttl=300)
            else:
                logger.info(f"Using cached context for user_id={user_id}")
            
            # Handle retrieval errors (access denied, etc.)
            if not retrieval_result["success"]:
                error_type = retrieval_result.get("error", "retrieval_error")
                logger.warning(f"Retrieval failed: {error_type}")
                
                # Log no-retrieval events to activity logs for analysis
                if error_type in ["no_documents", "low_quality_results", "reranker_no_quality"]:
                    try:
                        await activity_logger_service.log_activity(
                            db=self.db,
                            user_id=user_id,
                            incident_type="retrieval_no_context",
                            severity="info",
                            description=f"No context retrieved: {error_type}",
                            user_query=user_query[:500],  # Truncate long queries
                            details=retrieval_result.get("details")
                        )
                    except Exception as e:
                        logger.error(f"Failed to log no-retrieval event: {e}")
                
                return {
                    "success": False,
                    "error": error_type,
                    "message": retrieval_result.get("message", "Failed to retrieve context")
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
            llm = self.llm_router.select_llm(max_doc_level)
            
            # Step 4: Get conversation history
            history = await self.conversation_service.get_conversation_history(conversation_id, user_id)
            
            # Step 5: Generate streaming response using LangChain
            if stream:
                return {
                    "success": True,
                    "streaming": True,
                    "generator": self._stream_response(
                        llm=llm,
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
        user_query: str,
        documents: List[Any],
        history: List[Dict[str, str]],
        conversation_id: str,
        user_id: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming response using LangChain.
        
        Uses native LangChain modules: prompt template, message history, streaming.
        """
        try:
            # Build context from documents
            context_text = "\n\n".join([
                f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}"
                for doc in documents
            ])
            
            # Build prompt template with history placeholder
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="You are a helpful AI assistant. Use the provided context to answer questions accurately."),
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
            await self.conversation_service.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role=MessageRole.ASSISTANT,
                content=full_response,
                token_count=None,
                meta={"sources": sources} if sources else None
            )
            
            if sources:
                yield {"type": "metadata", "sources": sources}

            logger.info(f"Streaming completed for conversation {conversation_id}")
        
        except Exception as e:
            logger.error(f"Streaming failed: {e}", exc_info=True)
            yield {"type": "error", "message": str(e)}
    
    async def _generate_complete_response(
        self,
        llm: Any,
        user_query: str,
        documents: List[Any],
        history: List[Dict[str, str]]
    ) -> str:
        """Generate complete non-streaming response (if needed)."""
        # Build context
        context_text = "\n\n".join([
            f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}"
            for doc in documents
        ])
        
        # Build prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a helpful AI assistant."),
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
