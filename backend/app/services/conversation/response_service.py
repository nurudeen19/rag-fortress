"""
Conversation Response Generation Service

Handles the complete flow for generating AI responses:
1. Retrieves relevant context from vector store
2. Manages conversation history in Redis cache (last 3 exchanges = 6 messages)
3. Routes to appropriate LLM based on security levels
4. Generates and streams response
5. Saves response to database as long-form history

This service separates LLM orchestration from message persistence,
keeping the conversation_service focused on CRUD operations.
"""

import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import timedelta

from app.core.cache import get_cache
from app.services.vector_store.retriever import get_retriever_service
from app.services.llm_router_service import get_llm_router
from app.services.conversation.service import ConversationService
from app.services import activity_logger_service
from app.models.message import MessageRole
from app.models.user_permission import PermissionLevel
from app.core import get_logger

logger = get_logger(__name__)


class ConversationResponseService:
    """
    Orchestrates AI response generation for conversations.
    
    Flow:
    1. Validate query (handled by conversation_service.add_message)
    2. Retrieve context from vector store
    3. Load conversation history from cache (last 3 exchanges)
    4. Route to appropriate LLM based on security
    5. Generate response (streaming)
    6. Cache user message and assistant response
    7. Save response to database
    """
    
    # Cache configuration
    HISTORY_MAX_EXCHANGES = 3  # Store last 3 exchanges (6 messages)
    HISTORY_TTL = timedelta(hours=24)  # Cache expires after 24 hours
    
    def __init__(self, session):
        """
        Initialize response service.
        
        Args:
            session: Database session for conversation operations
        """
        self.session = session
        self.conversation_service = ConversationService(session)
        self.retriever_service = get_retriever_service()
        self.llm_router = get_llm_router()
        self.cache = get_cache()
    
    # ==================== Cache Management ====================
    
    def _get_history_cache_key(self, conversation_id: str) -> str:
        """Generate cache key for conversation history."""
        return f"conversation:history:{conversation_id}"
    
    async def _get_cached_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Retrieve conversation history from cache.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of message dicts with 'role' and 'content'
        """
        try:
            cache_key = self._get_history_cache_key(conversation_id)
            cached_data = await self.cache.get(cache_key)
            
            if cached_data:
                history = json.loads(cached_data)
                logger.info(f"Retrieved {len(history)} messages from cache for conversation {conversation_id}")
                return history
            
            logger.info(f"No cached history found for conversation {conversation_id}")
            return []
        
        except Exception as e:
            logger.warning(f"Failed to retrieve cached history: {e}")
            return []
    
    async def _add_to_cache_history(
        self, 
        conversation_id: str, 
        role: str, 
        content: str
    ) -> None:
        """
        Add message to cached history, maintaining max exchanges limit.
        
        Args:
            conversation_id: Conversation ID
            role: Message role (USER, ASSISTANT, SYSTEM)
            content: Message content
        """
        try:
            # Get current history
            history = await self._get_cached_history(conversation_id)
            
            # Add new message
            history.append({
                "role": role,
                "content": content
            })
            
            # Keep only last N exchanges (2*N messages)
            max_messages = self.HISTORY_MAX_EXCHANGES * 2
            if len(history) > max_messages:
                history = history[-max_messages:]
            
            # Save back to cache
            cache_key = self._get_history_cache_key(conversation_id)
            ttl_seconds = int(self.HISTORY_TTL.total_seconds())
            await self.cache.set(
                cache_key,
                json.dumps(history),
                ttl=ttl_seconds
            )
            
            logger.info(
                f"Added {role} message to cache for conversation {conversation_id} "
                f"(total: {len(history)} messages)"
            )
        
        except Exception as e:
            logger.error(f"Failed to cache message: {e}")
            # Don't fail the request if caching fails
    
    async def _clear_cache_history(self, conversation_id: str) -> None:
        """Clear cached history for conversation."""
        try:
            cache_key = self._get_history_cache_key(conversation_id)
            await self.cache.delete(cache_key)
            logger.info(f"Cleared cached history for conversation {conversation_id}")
        except Exception as e:
            logger.warning(f"Failed to clear cached history: {e}")
    
    # ==================== Activity Logging ====================
    
    async def _log_clearance_violation(
        self,
        user_id: int,
        user_clearance: PermissionLevel,
        max_doc_level: PermissionLevel,
        query: str,
        doc_count: int,
        conversation_id: Optional[str] = None
    ) -> None:
        """
        Log activity when user accesses documents above their clearance level.
        
        Args:
            user_id: User ID
            user_clearance: User's clearance level
            max_doc_level: Maximum security level in retrieved documents
            query: User's query text
            doc_count: Number of documents retrieved
            conversation_id: Optional conversation ID
        """
        try:
            severity = "warning" if max_doc_level == user_clearance.next_level() else "critical"
            
            await activity_logger_service.log_activity(
                db=self.session,
                user_id=user_id,
                incident_type="insufficient_clearance",
                severity=severity,
                description=f"User accessed {doc_count} document(s) above clearance level",
                details={
                    "user_clearance_level": user_clearance.name,
                    "max_document_level": max_doc_level.name,
                    "document_count": doc_count,
                    "conversation_id": conversation_id,
                    "clearance_gap": max_doc_level.value - user_clearance.value
                },
                user_clearance_level=user_clearance.name,
                required_clearance_level=max_doc_level.name,
                access_granted=True,  # Documents were retrieved but flagged
                user_query=query[:500]  # Truncate long queries
            )
            
            logger.warning(
                f"Clearance violation logged: user_id={user_id}, "
                f"user_level={user_clearance.name}, "
                f"doc_level={max_doc_level.name}, "
                f"docs={doc_count}"
            )
        
        except Exception as e:
            logger.error(f"Failed to log clearance violation: {e}", exc_info=True)
            # Don't fail request if logging fails
    
    # ==================== Context Retrieval ====================
    
    async def _retrieve_context(
        self, 
        query: str, 
        top_k: int = 5,
        user_clearance: Optional[PermissionLevel] = None,
        user_id: Optional[int] = None,
        conversation_id: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], List[PermissionLevel], bool]:
        """
        Retrieve relevant context from vector store.
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            user_clearance: User's clearance level for filtering
            user_id: User ID for activity logging
            conversation_id: Conversation ID for activity logging
            
        Returns:
            Tuple of (formatted_docs, security_levels, clearance_violation)
        """
        try:
            # Retrieve documents
            documents = self.retriever_service.query(
                query_text=query,
                top_k=top_k
            )
            
            # Extract security levels and format documents
            security_levels = []
            formatted_docs = []
            clearance_violation = False
            
            for doc in documents:
                # Extract security level from metadata
                security_level_str = doc.metadata.get("security_level", "GENERAL")
                try:
                    security_level = PermissionLevel[security_level_str]
                except KeyError:
                    security_level = PermissionLevel.GENERAL
                
                security_levels.append(security_level)
                
                # Check for clearance violations
                if user_clearance and security_level > user_clearance:
                    clearance_violation = True
                
                # Format document for LLM
                formatted_docs.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Unknown"),
                    "security_level": security_level_str
                })
            
            max_security_level = max(security_levels) if security_levels else None
            
            logger.info(
                f"Retrieved {len(documents)} documents for query. "
                f"Max security level: {max_security_level.name if max_security_level else 'NONE'}, "
                f"User clearance: {user_clearance.name if user_clearance else 'NONE'}"
            )
            
            # Log activity if clearance violation detected
            if clearance_violation and user_id:
                await self._log_clearance_violation(
                    user_id=user_id,
                    user_clearance=user_clearance,
                    max_doc_level=max_security_level,
                    query=query,
                    doc_count=len(documents),
                    conversation_id=conversation_id
                )
            
            return formatted_docs, security_levels, clearance_violation
        
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}", exc_info=True)
            return [], [], False
    
    # ==================== Response Generation ====================
    
    async def generate_response(
        self,
        conversation_id: str,
        user_id: int,
        user_query: str,
        user_clearance: PermissionLevel,
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        Generate AI response for user query.
        
        Complete flow:
        1. Save user message to database
        2. Retrieve context from vector store
        3. Load conversation history from cache
        4. Route to appropriate LLM
        5. Generate response (streaming or non-streaming)
        6. Cache user message and response
        7. Save response to database
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            user_query: User's query text
            user_clearance: User's effective clearance level
            stream: Whether to stream the response
            
        Returns:
            Dict with success status, response data, and optional stream generator
        """
        try:
            # Step 1: Save user message to database (includes validation)
            logger.info(f"Saving user message for conversation {conversation_id}")
            user_message_result = await self.conversation_service.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role=MessageRole.USER,
                content=user_query,
                token_count=None,
                meta=None
            )
            
            # Check if message was blocked (malicious query)
            if not user_message_result["success"]:
                logger.warning(f"User message blocked: {user_message_result.get('error')}")
                return user_message_result
            
            # Step 2: Retrieve context from vector store
            logger.info(f"Retrieving context for query: {user_query[:50]}...")
            context_docs, security_levels, clearance_violation = await self._retrieve_context(
                query=user_query,
                top_k=5,
                user_clearance=user_clearance,
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            # Step 3: Load conversation history from cache
            logger.info(f"Loading conversation history from cache")
            cached_history = await self._get_cached_history(conversation_id)
            
            # Step 4: Route to appropriate LLM
            logger.info(f"Routing LLM based on security levels")
            routing_decision = await self.llm_router.route_llm(
                document_security_levels=security_levels,
                user_clearance=user_clearance,
                metadata={
                    "conversation_id": conversation_id,
                    "user_id": user_id
                }
            )
            
            llm = routing_decision.llm
            
            # Step 5: Generate response
            if stream:
                # Return streaming generator
                return {
                    "success": True,
                    "streaming": True,
                    "generator": self._generate_streaming_response(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        user_query=user_query,
                        context_docs=context_docs,
                        cached_history=cached_history,
                        llm=llm,
                        routing_decision=routing_decision
                    ),
                    "user_message": user_message_result["message"]
                }
            else:
                # Generate complete response
                response_text = await self._generate_complete_response(
                    user_query=user_query,
                    context_docs=context_docs,
                    cached_history=cached_history,
                    llm=llm
                )
                
                # Step 6: Cache messages
                await self._add_to_cache_history(conversation_id, "USER", user_query)
                await self._add_to_cache_history(conversation_id, "ASSISTANT", response_text)
                
                # Step 7: Save response to database
                response_message_result = await self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role=MessageRole.ASSISTANT,
                    content=response_text,
                    token_count=None,
                    meta={
                        "sources": [doc["source"] for doc in context_docs],
                        "llm_type": routing_decision.llm_type,
                        "security_levels": [level.name for level in security_levels]
                    }
                )
                
                return {
                    "success": True,
                    "streaming": False,
                    "user_message": user_message_result["message"],
                    "assistant_message": response_message_result["message"],
                    "context_count": len(context_docs),
                    "llm_type": routing_decision.llm_type
                }
        
        except Exception as e:
            logger.error(f"Response generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_streaming_response(
        self,
        conversation_id: str,
        user_id: int,
        user_query: str,
        context_docs: List[Dict[str, Any]],
        cached_history: List[Dict[str, str]],
        llm: Any,
        routing_decision: Any
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response.
        
        Yields response chunks and handles caching/saving after completion.
        """
        try:
            # Build prompt
            prompt = self._build_prompt(user_query, context_docs, cached_history)
            
            # Stream response
            full_response = ""
            async for chunk in llm.astream(prompt):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                full_response += content
                yield content
            
            # After streaming completes, cache and save
            await self._add_to_cache_history(conversation_id, "USER", user_query)
            await self._add_to_cache_history(conversation_id, "ASSISTANT", full_response)
            
            # Save response to database
            await self.conversation_service.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role=MessageRole.ASSISTANT,
                content=full_response,
                token_count=None,
                meta={
                    "sources": [doc["source"] for doc in context_docs],
                    "llm_type": routing_decision.llm_type,
                    "security_levels": [level.name for level in routing_decision.document_security_levels] if hasattr(routing_decision, 'document_security_levels') else []
                }
            )
            
            logger.info(f"Streaming response completed and saved for conversation {conversation_id}")
        
        except Exception as e:
            logger.error(f"Streaming response failed: {e}", exc_info=True)
            yield f"\n\n[Error generating response: {str(e)}]"
    
    async def _generate_complete_response(
        self,
        user_query: str,
        context_docs: List[Dict[str, Any]],
        cached_history: List[Dict[str, str]],
        llm: Any
    ) -> str:
        """
        Generate complete (non-streaming) response.
        
        Args:
            user_query: User's query
            context_docs: Retrieved context documents
            cached_history: Cached conversation history
            llm: Language model instance
            
        Returns:
            Generated response text
        """
        # Build prompt
        prompt = self._build_prompt(user_query, context_docs, cached_history)
        
        # Generate response
        response = await llm.ainvoke(prompt)
        
        return response.content if hasattr(response, 'content') else str(response)
    
    def _build_prompt(
        self,
        user_query: str,
        context_docs: List[Dict[str, Any]],
        cached_history: List[Dict[str, str]]
    ) -> str:
        """
        Build prompt for LLM with context and history.
        
        Args:
            user_query: Current user query
            context_docs: Retrieved context documents
            cached_history: Previous conversation messages
            
        Returns:
            Formatted prompt string
        """
        # Format context
        context_text = "\n\n".join([
            f"[Source: {doc['source']}]\n{doc['content']}"
            for doc in context_docs
        ])
        
        # Format history
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in cached_history
        ])
        
        # Build prompt
        prompt = f"""You are a helpful AI assistant with access to a knowledge base. Use the provided context to answer the user's question accurately.

Context from knowledge base:
{context_text if context_text else "No relevant context found."}

Previous conversation:
{history_text if history_text else "No previous messages."}

User Question: {user_query}

Assistant Response:"""
        
        return prompt


# Singleton instance
_response_service_factory: Optional[ConversationResponseService] = None


def get_conversation_response_service(session) -> ConversationResponseService:
    """
    Get conversation response service instance.
    
    Args:
        session: Database session
        
    Returns:
        ConversationResponseService instance
    """
    # Note: Not using singleton pattern here since service needs session
    return ConversationResponseService(session)
