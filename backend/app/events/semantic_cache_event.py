"""
Semantic Cache Event Handler

Handles semantic cache storage events asynchronously to avoid blocking
the main request/response flow. Processes both context and response caching.
"""

from typing import Dict, Any, List, Optional

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
    - Security metadata extraction
    
    Event data fields:
    - cache_type: str ("context" or "response") (required)
    - query: str (required)
    - entry: Any (required) - response text or retrieval result dict
    - min_security_level: Optional[int]
    - is_departmental: Optional[bool]
    - department_ids: Optional[List[int]]
    - documents: Optional[List] - for response cache metadata extraction
    
    Usage from services:
        from app.core.events import get_event_bus
        
        # Context cache
        bus = get_event_bus()
        await bus.emit("semantic_cache", {
            "cache_type": "context",
            "query": query_text,
            "entry": retrieval_result,  # Will serialize documents
            "min_security_level": max_security,
            "is_departmental": is_dept,
            "department_ids": dept_ids
        })
        
        # Response cache
        await bus.emit("semantic_cache", {
            "cache_type": "response",
            "query": user_query,
            "entry": response_text,
            "documents": documents  # For metadata extraction
        })
    """
    
    @property
    def event_type(self) -> str:
        return "semantic_cache"
    
    async def handle(self, event_data: Dict[str, Any]) -> None:
        """Process semantic cache storage event."""
        try:
            cache_type = event_data["cache_type"]
            query = event_data["query"]
            entry = event_data["entry"]
            
            if cache_type == "context":
                await self._handle_context_cache(event_data)
            elif cache_type == "response":
                await self._handle_response_cache(event_data)
            else:
                logger.error(f"Unknown cache_type: {cache_type}")
        
        except KeyError as e:
            logger.error(f"Missing required field in semantic_cache event: {e}")
        except Exception as e:
            logger.error(f"Failed to process semantic_cache event: {e}", exc_info=True)
    
    async def _handle_context_cache(self, event_data: Dict[str, Any]) -> None:
        """Handle context-level cache storage."""
        try:
            entry = event_data["entry"]
            
            # Serialize documents to dict format (Document objects are not JSON serializable)
            if entry.get("context"):
                documents = entry["context"]
                serialized_entry = {
                    "success": entry["success"],
                    "count": entry.get("count", 0),
                    "max_security_level": entry.get("max_security_level"),
                    "context": [
                        {
                            "page_content": doc.page_content,
                            "metadata": doc.metadata
                        }
                        for doc in documents
                    ]
                }
            else:
                serialized_entry = entry
            
            # Store in cache
            cache = get_semantic_cache()
            await cache.set(
                cache_type="context",
                query=event_data["query"],
                entry=serialized_entry,
                min_security_level=event_data.get("min_security_level"),
                is_departmental=event_data.get("is_departmental", False),
                department_ids=event_data.get("department_ids")
            )
            
            logger.debug(
                f"Context cached (docs={len(documents) if entry.get('context') else 0}, "
                f"query='{event_data['query'][:50]}...')"
            )
        
        except Exception as e:
            logger.error(f"Failed to cache context: {e}", exc_info=True)
    
    async def _handle_response_cache(self, event_data: Dict[str, Any]) -> None:
        """Handle response-level cache storage with validation."""
        try:
            response_text = event_data["entry"]
            user_query = event_data["query"]
            documents = event_data.get("documents", [])
            
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
            if len(response_text.strip()) < 20:
                logger.info(
                    f"Skipping cache for short response ({len(response_text)} chars): "
                    f"'{response_text[:50]}...' (query='{user_query[:50]}...')"
                )
                return
            
            # Extract security metadata from documents
            min_security_level = None
            is_departmental = False
            department_ids = set()
            
            for doc in documents:
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                
                # Track highest security level (minimum clearance to access this cache)
                sec_level = metadata.get('security_level')
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
            
            # Store in cache
            cache = get_semantic_cache()
            await cache.set(
                cache_type="response",
                query=user_query,
                entry=response_text,
                min_security_level=min_security_level,
                is_departmental=is_departmental,
                department_ids=list(department_ids) if department_ids else None
            )
            
            logger.debug(
                f"Response cached (min_clearance_required={min_security_level}, "
                f"dept={is_departmental}, query='{user_query[:50]}...')"
            )
        
        except Exception as e:
            logger.error(f"Failed to cache response: {e}", exc_info=True)
