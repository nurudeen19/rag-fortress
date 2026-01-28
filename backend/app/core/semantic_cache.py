"""
Semantic Cache - Manual Implementation

Manual semantic caching with proper threshold control and per-variation metadata.
Each cache entry stores a list of variations with individual metadata.
"""

import json
import hashlib
from typing import Optional, Dict, Any, List, Literal
import numpy as np

from app.core import get_logger
from app.config.settings import settings
from app.core.cache import get_cache
from app.core.embedding_factory import get_embedding_provider

logger = get_logger(__name__)

CacheType = Literal["response", "context"]


class SemanticCache:
    """
    Manual semantic cache with variation clustering and per-variation metadata.
    
    Structure:
    - Each unique semantic query creates a cache entry
    - Entry contains list of variations: [{"data": ..., "metadata": {...}}, ...]
    - Each variation has its own security metadata
    - Strict similarity threshold enforcement on retrieval
    
    Cache Entry Format:
    {
        "query_embedding": [0.1, 0.2, ...],
        "query_text": "original query",
        "variations": [
            {
                "data": "response or context text",
                "metadata": {
                    "min_security_level": 0,
                    "is_departmental": False,
                    "department_ids": []
                }
            },
            ...
        ]
    }
    """
    
    def __init__(self):
        """Initialize semantic cache with manual implementation."""
        self.config = settings.cache_settings.get_semantic_cache_config()
        self.redis_client = None
        self.embedding_provider = None
        
        # Initialize if at least one tier is enabled
        if self.config["response"]["enabled"] or self.config["context"]["enabled"]:
            self._initialize()
    
    def _initialize(self):
        """Initialize cache and embedding provider."""
        try:
            base_cache = get_cache()
            
            if not hasattr(base_cache, 'redis_client') or base_cache.redis_client is None:
                logger.warning("Redis not available, semantic cache disabled")
                return
            
            self.redis_client = base_cache.redis_client
            self.embedding_provider = get_embedding_provider()
            
            logger.info(
                f"Semantic cache initialized - "
                f"Response (enabled={self.config['response']['enabled']}, "
                f"threshold={self.config['response']['similarity_threshold']}), "
                f"Context (enabled={self.config['context']['enabled']}, "
                f"threshold={self.config['context']['similarity_threshold']})"
            )
        
        except Exception as e:
            logger.error(f"Failed to initialize semantic cache: {e}", exc_info=True)
    
    def _get_cache_key_prefix(self, cache_type: CacheType) -> str:
        """Get Redis key prefix for cache type."""
        return f"semantic_cache:{cache_type}:"
    
    def _compute_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    async def _get_all_cache_entries(self, cache_type: CacheType) -> List[Dict[str, Any]]:
        """Get all cache entries for a given type."""
        if not self.redis_client:
            return []
        
        try:
            prefix = self._get_cache_key_prefix(cache_type)
            keys = self.redis_client.keys(f"{prefix}*")
            
            entries = []
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    entry = json.loads(data)
                    entry["_redis_key"] = key
                    entries.append(entry)
            
            return entries
        except Exception as e:
            logger.error(f"Error fetching cache entries: {e}", exc_info=True)
            return []
    
    async def get(
        self,
        cache_type: CacheType,
        query: str,
        user_security_level: int,
        user_department_id: Optional[int] = None,
        user_department_security_level: Optional[int] = None
    ) -> tuple[Optional[Any], bool]:
        """
        Get entry from semantic cache with strict similarity threshold and per-variation metadata.
        
        Flow:
        1. Generate embedding for query
        2. Find all cached entries for this cache type
        3. Compute similarity scores and filter by threshold
        4. Find best match (highest similarity)
        5. Filter variations by user security permissions
        6. Return random accessible variation
        7. Signal should_continue if variations < max_entries
        
        Args:
            cache_type: "response" or "context"
            query: Query text
            user_security_level: User's organization-level security clearance
            user_department_id: User's department ID
            user_department_security_level: User's department-level security clearance
        
        Returns:
            Tuple of (data, should_continue_pipeline)
            - data: Random variation's data or None if no cache hit
            - should_continue_pipeline: True if variations < max_entries
        """
        if not self.redis_client or not self.embedding_provider:
            return None, False
        
        # Check if this cache type is enabled
        if not self.config[cache_type]["enabled"]:
            return None, False
        
        try:
            # Get configuration
            similarity_threshold = self.config[cache_type]["similarity_threshold"]
            max_entries = self.config[cache_type].get("max_entries", 10)
            
            # Generate embedding for query
            query_embedding = self.embedding_provider.embed_query(query)
            
            # Get all cache entries for this type
            all_entries = await self._get_all_cache_entries(cache_type)
            
            if not all_entries:
                logger.debug(f"{cache_type.capitalize()} cache MISS (no entries) for query: '{query[:50]}...'")
                return None, False
            
            # Find best matching entry above threshold
            best_match = None
            best_score = -1.0
            
            for entry in all_entries:
                cached_embedding = entry.get("query_embedding", [])
                if not cached_embedding:
                    continue
                
                similarity = self._compute_cosine_similarity(query_embedding, cached_embedding)
                
                logger.debug(
                    f"Cache similarity: {similarity:.4f} (threshold={similarity_threshold}) "
                    f"for cached query: '{entry.get('query_text', '')[:50]}...'"
                )
                
                if similarity >= similarity_threshold and similarity > best_score:
                    best_match = entry
                    best_score = similarity
            
            if not best_match:
                logger.debug(
                    f"{cache_type.capitalize()} cache MISS (no match above threshold={similarity_threshold}) "
                    f"for query: '{query[:50]}...'"
                )
                return None, False
            
            # Get variations list from best match
            variations = best_match.get("variations", [])
            
            if not variations:
                logger.warning(f"Cache entry has no variations, treating as miss")
                return None, False
            
            # Filter variations by security access
            accessible_variations = []
            for variation in variations:
                var_metadata = variation.get("metadata", {})
                if self._validate_security_access(
                    var_metadata,
                    user_security_level,
                    user_department_id,
                    user_department_security_level
                ):
                    accessible_variations.append(variation)
            
            if not accessible_variations:
                logger.debug(
                    f"Cache hit but no accessible variations (security mismatch) "
                    f"for query: '{query[:50]}...'"
                )
                return None, False
            
            # Determine if we should continue generating variations
            total_variations = len(variations)
            should_continue = total_variations < max_entries
            
            # Select random accessible variation
            import random
            selected_variation = random.choice(accessible_variations)
            data = selected_variation.get("data")
            
            logger.info(
                f"{cache_type.capitalize()} cache HIT (similarity={best_score:.4f}) "
                f"for query: '{query[:50]}...' "
                f"(variations={total_variations}/{max_entries}, "
                f"accessible={len(accessible_variations)}, "
                f"should_continue={should_continue})"
            )
            
            return data, should_continue
        
        except Exception as e:
            logger.error(f"Error retrieving from {cache_type} cache: {e}", exc_info=True)
            return None, False
    
    async def set(
        self,
        cache_type: CacheType,
        query: str,
        entry: Any,
        min_security_level: Optional[int],
        is_departmental: bool,
        department_ids: Optional[List[int]] = None
    ):
        """
        Store entry in semantic cache with per-variation metadata.
        
        Flow:
        1. Generate embedding for query
        2. Find if a semantically similar entry exists (above threshold)
        3. If exists: Append variation to existing entry (if not at max)
        4. If not exists: Create new cache entry
        5. Each variation stores its own security metadata
        
        Args:
            cache_type: "response" or "context"
            query: Query text
            entry: Response or context data to cache
            min_security_level: Minimum security level for this variation
            is_departmental: Whether this variation is department-specific
            department_ids: List of department IDs for this variation
        """
        if not self.redis_client or not self.embedding_provider:
            return
        
        # Check if this cache type is enabled
        if not self.config[cache_type]["enabled"]:
            return
        
        try:
            similarity_threshold = self.config[cache_type]["similarity_threshold"]
            max_entries = self.config[cache_type].get("max_entries", 10)
            ttl_seconds = self.config[cache_type]["ttl_seconds"]
            
            # Generate embedding for query
            query_embedding = self.embedding_provider.embed_query(query)
            
            # Find existing semantically similar entry
            all_entries = await self._get_all_cache_entries(cache_type)
            
            existing_entry = None
            existing_key = None
            best_score = -1.0
            
            for entry_data in all_entries:
                cached_embedding = entry_data.get("query_embedding", [])
                if not cached_embedding:
                    continue
                
                similarity = self._compute_cosine_similarity(query_embedding, cached_embedding)
                
                if similarity >= similarity_threshold and similarity > best_score:
                    existing_entry = entry_data
                    existing_key = entry_data.get("_redis_key")
                    best_score = similarity
            
            # Build variation metadata
            variation_metadata = {
                "min_security_level": min_security_level or 0,
                "is_departmental": is_departmental,
                "department_ids": department_ids or []
            }
            
            # Create variation object
            new_variation = {
                "data": entry,
                "metadata": variation_metadata
            }
            
            if existing_entry and existing_key:
                # Append to existing entry
                variations = existing_entry.get("variations", [])
                
                if len(variations) >= max_entries:
                    logger.debug(
                        f"Cache entry at max capacity ({len(variations)}/{max_entries}), "
                        f"not adding variation for: '{query[:50]}...'"
                    )
                    return
                
                variations.append(new_variation)
                
                cache_entry = {
                    "query_embedding": existing_entry["query_embedding"],
                    "query_text": existing_entry["query_text"],
                    "variations": variations
                }
                
                logger.info(
                    f"Appending variation to {cache_type} cache "
                    f"({len(variations)}/{max_entries}, similarity={best_score:.4f}) "
                    f"for query: '{query[:50]}...'"
                )
                
                # Update existing key
                self.redis_client.setex(
                    existing_key,
                    ttl_seconds,
                    json.dumps(cache_entry)
                )
            else:
                # Create new cache entry
                cache_entry = {
                    "query_embedding": query_embedding,
                    "query_text": query,
                    "variations": [new_variation]
                }
                
                # Generate unique key
                key_hash = hashlib.md5(f"{query}{cache_type}".encode()).hexdigest()
                cache_key = f"{self._get_cache_key_prefix(cache_type)}{key_hash}"
                
                logger.info(
                    f"Creating new {cache_type} cache entry (1/{max_entries}) "
                    f"for query: '{query[:50]}...'"
                )
                
                self.redis_client.setex(
                    cache_key,
                    ttl_seconds,
                    json.dumps(cache_entry)
                )
            
            logger.debug(f"Successfully stored {cache_type} cache variation")
        
        except Exception as e:
            logger.error(f"Error storing in {cache_type} cache: {e}", exc_info=True)
    
    async def clear(self, cache_type: Optional[CacheType] = None):
        """Clear semantic cache entries."""
        if not self.redis_client:
            return
        
        try:
            if cache_type:
                prefix = self._get_cache_key_prefix(cache_type)
                keys = self.redis_client.keys(f"{prefix}*")
                if keys:
                    self.redis_client.delete(*keys)
                logger.info(f"Cleared {cache_type} semantic cache ({len(keys)} entries)")
            else:
                # Clear both caches
                for ct in ["response", "context"]:
                    prefix = self._get_cache_key_prefix(ct)
                    keys = self.redis_client.keys(f"{prefix}*")
                    if keys:
                        self.redis_client.delete(*keys)
                logger.info("Cleared all semantic caches")
        
        except Exception as e:
            logger.error(f"Error clearing semantic cache: {e}", exc_info=True)
    
    def _validate_security_access(
        self,
        metadata: Dict[str, Any],
        user_security_level: int,
        user_department_id: Optional[int],
        user_department_security_level: Optional[int]
    ) -> bool:
        """Validate if user can access cached variation based on security metadata."""
        try:
            min_security = int(metadata.get("min_security_level", 0))
            is_departmental = metadata.get("is_departmental", False)
            
            # Check security clearance
            if is_departmental:
                # Departmental content - check department clearance
                if user_department_security_level is None:
                    return False
                if user_department_security_level < min_security:
                    return False
                
                # Check department access
                if user_department_id:
                    dept_ids = metadata.get("department_ids", [])
                    if dept_ids and user_department_id not in dept_ids:
                        return False
            else:
                # Organization-level content - check org clearance
                if user_security_level < min_security:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating security access: {e}", exc_info=True)
            return False


# Singleton instance
_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache() -> SemanticCache:
    """Get semantic cache singleton instance."""
    global _semantic_cache
    
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    
    return _semantic_cache
