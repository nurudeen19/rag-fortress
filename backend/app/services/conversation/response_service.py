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

from app.core.cache import get_cache
from app.services.vector_store.retriever import get_retriever_service
from app.services.llm_router_service import get_llm_router
from app.utils.user_clearance_cache import get_user_clearance_cache
from app.models.user_permission import PermissionLevel
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
        self.cache = get_cache()
    
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
            
            # Step 2: Retrieve context with user credentials
            logger.info(f"Retrieving context for user_id={user_id}, clearance={user_clearance.name}")
            retrieval_result = self.retriever.query(
                query_text=user_query,
                top_k=5,
                user_security_level=user_clearance.value,
                user_department_id=user_department_id
            )
            
            # Handle retrieval errors (access denied, etc.)
            if not retrieval_result["success"]:
                logger.warning(f"Retrieval failed: {retrieval_result.get('error')}")
                return {
                    "success": False,
                    "error": retrieval_result.get("error", "retrieval_error"),
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
            history = await self._get_history(conversation_id)
            
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
                        conversation_id=conversation_id
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
            
            # Convert security level string to PermissionLevel enum
            return {
                "clearance": PermissionLevel[clearance["security_level"]],
                "department_id": clearance["department_id"]
            }
        
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    

    
    async def _get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history from cache.
        
        Returns list of {'role': 'user'|'assistant', 'content': '...'} dicts.
        """
        try:
            import json
            
            cache_key = f"conversation:history:{conversation_id}"
            cached_data = await self.cache.get(cache_key)
            
            if cached_data:
                history = json.loads(cached_data)
                logger.info(f"Retrieved {len(history)} history messages")
                return history
            
            return []
        
        except Exception as e:
            logger.warning(f"Failed to get history: {e}")
            return []
    
    async def _stream_response(
        self,
        llm: Any,
        user_query: str,
        documents: List[Any],
        history: List[Dict[str, str]],
        conversation_id: str
    ) -> AsyncGenerator[str, None]:
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
                yield content
            
            # Cache the exchange after streaming completes
            await self._cache_exchange(conversation_id, user_query, full_response)
            
            logger.info(f"Streaming completed for conversation {conversation_id}")
        
        except Exception as e:
            logger.error(f"Streaming failed: {e}", exc_info=True)
            yield f"\n\n[Error: {str(e)}]"
    
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
        
        # Generate
        chain = prompt | llm
        response = await chain.ainvoke({
            "context": context_text if context_text else "No relevant context found.",
            "question": user_query,
            "history": history_messages
        })
        
        return response.content if hasattr(response, 'content') else str(response)
    
    async def _cache_exchange(self, conversation_id: str, user_msg: str, assistant_msg: str) -> None:
        """Cache the user-assistant exchange."""
        try:
            import json
            from datetime import timedelta
            
            # Get current history
            cache_key = f"conversation:history:{conversation_id}"
            cached_data = await self.cache.get(cache_key)
            history = json.loads(cached_data) if cached_data else []
            
            # Add new messages
            history.append({"role": "user", "content": user_msg})
            history.append({"role": "assistant", "content": assistant_msg})
            
            # Keep last 6 messages (3 exchanges)
            history = history[-6:]
            
            # Save to cache (24 hour TTL)
            await self.cache.set(
                cache_key,
                json.dumps(history),
                ttl=int(timedelta(hours=24).total_seconds())
            )
            
            logger.info(f"Cached exchange for {conversation_id}")
        
        except Exception as e:
            logger.error(f"Failed to cache exchange: {e}")


def get_conversation_response_service(session) -> ConversationResponseService:
    """Get conversation response service instance."""
    return ConversationResponseService(session)
