"""
Semantic Cache Event Handler

Handles semantic cache storage events asynchronously to avoid blocking
the main request/response flow. Processes both context and response caching.
"""

from typing import Dict, Any

from app.events.base import BaseEventHandler
from app.core import get_logger
from app.core.semantic_cache import get_semantic_cache


logger = get_logger(__name__)


class SemanticCacheEvent(BaseEventHandler):
    """
    Semantic cache event handler.
    
    Processes cache storage requests in the background, including:
    - Document serialization for context cache
    - Response validation (generic negatives, length checks)
    - Uses complete pre-computed security metadata (no document iteration)
    
    Event data fields:
    - cache_type: str ("context" or "response") (required)
    - query: str (required)
    
    For context cache:
    - documents: List (required) - raw documents to format and cache
    - security_metadata: Dict (required) - complete pre-computed security info
      - max_security_level: int - highest security level among documents
      - is_department_only: bool - whether security applies to department
      - department_id: Optional[int] - department ID when is_department_only is True
    
    For response cache:
    - entry: str (required) - response text to cache
    - security_metadata: Dict (required) - complete pre-computed security info
      - max_security_level: int - highest security level among documents
      - is_department_only: bool - whether security applies to department
      - department_id: Optional[int] - department ID when is_department_only is True
    
    Usage from services:
        from app.core.events import get_event_bus
        
        # Context cache with complete security metadata
        bus = get_event_bus()
        await bus.emit("semantic_cache", {
            "cache_type": "context",
            "query": query_text,
            "documents": documents,
            "security_metadata": {
                "max_security_level": 2,
                "is_department_only": False,
                "department_id": None
            }
        })
        
        # Response cache with complete security metadata
        await bus.emit("semantic_cache", {
            "cache_type": "response",
            "query": user_query,
            "entry": response_text,
            "security_metadata": {
                "max_security_level": 3,
                "is_department_only": True,
                "department_id": 5
            }
        })
    """
    
    @property
    def event_type(self) -> str:
        return "semantic_cache"
    
    async def handle(self, event_data: Dict[str, Any]) -> None:
        """Process semantic cache storage event."""
        try:
            cache_type = event_data["cache_type"]
            event_data["query"]  # Validate query exists
            
            # Validate cache-type-specific required fields
            if cache_type == "context":
                event_data["documents"]  # Context cache requires documents
                await self._handle_context_cache(event_data)
            elif cache_type == "response":
                event_data["entry"]  # Response cache requires entry
                await self._handle_response_cache(event_data)
            else:
                logger.error(f"Unknown cache_type: {cache_type}")
        
        except KeyError as e:
            logger.error(f"Missing required field in semantic_cache event: {e}")
        except Exception as e:
            logger.error(f"Failed to process semantic_cache event: {e}", exc_info=True)
    
    async def _handle_context_cache(self, event_data: Dict[str, Any]) -> None:
        """Handle context-level cache storage with formatting."""
        try:
            documents = event_data["documents"]
            
            # Format context text from documents
            context_text = "\n\n".join([
                doc.page_content for doc in documents
            ])
            
            # Use pre-computed complete security metadata (no document iteration)
            # Ensure it's a dict, not None
            security_metadata = event_data.get("security_metadata", {}) or {}
            max_security_level = security_metadata.get("max_security_level", 1)
            is_department_only = security_metadata.get("is_department_only", False)
            department_id = security_metadata.get("department_id")
            
          
            
            # Build cache entry with formatted text
            entry = {
                "context_text": context_text,
                "source_count": len(documents)
            }
            
            # Store in cache
            cache = get_semantic_cache()
            await cache.set(
                cache_type="context",
                query=event_data["query"],
                entry=entry,
                min_security_level=max_security_level,
                is_department_only=is_department_only,
                department_id=department_id
            )
            
            logger.debug(
                f"Context cached (source_count={len(documents)}, "
                f"text_length={len(context_text)}, query='{event_data['query'][:50]}...')"
            )
        
        except Exception as e:
            logger.error(f"Failed to cache context: {e}", exc_info=True)
    
    async def _handle_response_cache(self, event_data: Dict[str, Any]) -> None:
        """Handle response-level cache storage with validation."""
        try:
            response_text = event_data["entry"]
            user_query = event_data["query"]
            
            # Validation: Skip generic negative responses
            generic_negative_responses = [
                "i don't have",
                "i don't know",
                "no information",
                "not mentioned",
                "not provided",
                "not available in the documents",
                "not found in the context",
                "i'm not sure",
                "i cannot answer"
            ]
            
            response_lower = response_text.lower().strip()
            
            if any(generic in response_lower for generic in generic_negative_responses):
                logger.info(
                    f"Skipping cache for generic negative response: '{response_text[:100]}...' "
                    f"(query='{user_query[:50]}...')"
                )
                return
            
            # Validation: Don't cache very short responses (likely incomplete)
            # to monitor for potential issues as some valid responses can be short.
            if len(response_text.strip()) < 20:
                logger.info(
                    f"Skipping cache for short response ({len(response_text)} chars): "
                    f"'{response_text[:50]}...' (query='{user_query[:50]}...')"
                )
                return
            
            # Use pre-computed complete security metadata (no document iteration)
            security_metadata = event_data.get("security_metadata", {})
            max_security_level = security_metadata.get("max_security_level", 1)
            is_department_only = security_metadata.get("is_department_only", False)
            department_id = security_metadata.get("department_id")
            
            logger.debug(
                f"Using pre-computed security metadata: max_security_level={max_security_level}, "
                f"dept_only={is_department_only}, dept_id={department_id}"
            )
            
            # Store in cache
            cache = get_semantic_cache()
            await cache.set(
                cache_type="response",
                query=user_query,
                entry=response_text,
                min_security_level=max_security_level,
                is_department_only=is_department_only,
                department_id=department_id
            )
            
            logger.debug(
                f"Response cached (max_security_level={max_security_level}, "
                f"dept_only={is_department_only}, query='{user_query[:50]}...')"
            )
        
        except Exception as e:
            logger.error(f"Failed to cache response: {e}", exc_info=True)
