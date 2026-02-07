"""
Semantic Cache using RedisVL

Leverages RedisVL for vector-based semantic similarity caching.
Uses max_entries to control variations (max_entries=1 for single response, >1 for variations).

Distance Threshold (set in config):
- Lower values = more similar (0.1 = very similar, 0.5 = moderately similar, 1.0+ = dissimilar)
- Use as-is, no conversion needed
- Example: RESPONSE_CACHE_DISTANCE_THRESHOLD=0.1 means find very similar queries
"""

import json
import random
from typing import Optional, Dict, Any, Literal
from redisvl.extensions.cache.llm import SemanticCache as RedisVLSemanticCache

from app.core import get_logger
from app.config.settings import settings
from app.core.cache import get_cache
from app.core.embedding_factory import get_redisvl_vectorizer
from app.utils.encryption import encrypt, decrypt

logger = get_logger(__name__)

CacheType = Literal["response", "context"]


class SemanticCache:
    """
    Two-tier semantic cache using RedisVL.
    
    Features:
    - Vector similarity search via RedisVL
    - Configurable variations via max_entries (1=single, >1=variations)
    - Security-aware access control
    - Encryption at root level
    - TTL-based automatic expiration
    
    Cache Entry Structure:
    {
        "query": str,
        "is_encrypted": bool,
        "min_security_level": int,  # Minimum security level required to access
        "is_department_only": bool,  # Whether this is department-restricted
        "department_id": int | None,  # Department ID for department-restricted content
        "variations": [
            {"text": Any},  # Just the response/context text
            {"text": Any},
            {"text": Any}
        ]
    }
    """
    
    def __init__(self):
        """Initialize semantic cache with RedisVL."""
        self.config = settings.cache_settings.get_semantic_cache_config()
        self.response_cache: Optional[RedisVLSemanticCache] = None
        self.context_cache: Optional[RedisVLSemanticCache] = None
        
        # Initialize if at least one tier is enabled
        if self.config["response"]["enabled"] or self.config["context"]["enabled"]:
            self._initialize()
    
    def _initialize(self):
        """Initialize RedisVL semantic caches."""
        try:
            base_cache = get_cache()
            
            if not hasattr(base_cache, 'redis_client') or base_cache.redis_client is None:
                logger.warning("Redis not available, semantic cache disabled")
                return
            
            # Get RedisVL vectorizer from factory (reuses existing embedding config by default)
            vectorizer = get_redisvl_vectorizer()
            
            redis_url = settings.cache_settings.get_redis_url() or "redis://localhost:6379"
            
            # Initialize response cache
            if self.config["response"]["enabled"]:
                self.response_cache = RedisVLSemanticCache(
                    name="rag_response_cache",
                    redis_url=redis_url,
                    distance_threshold=self.config["response"]["distance_threshold"],
                    ttl=self.config["response"]["ttl_seconds"],
                    vectorizer=vectorizer
                )
                logger.info(
                    f"Response cache initialized (distance_threshold={self.config['response']['distance_threshold']}, "
                    f"TTL={self.config['response']['ttl_seconds']}s, encrypt={self.config['response']['encrypt']})"
                )
            
            # Initialize context cache
            if self.config["context"]["enabled"]:
                self.context_cache = RedisVLSemanticCache(
                    name="rag_context_cache",
                    redis_url=redis_url,
                    distance_threshold=self.config["context"]["distance_threshold"],
                    ttl=self.config["context"]["ttl_seconds"],
                    vectorizer=vectorizer
                )
                logger.info(
                    f"Context cache initialized (distance_threshold={self.config['context']['distance_threshold']}, "
                    f"TTL={self.config['context']['ttl_seconds']}s, encrypt={self.config['context']['encrypt']})"
                )
        
        except Exception as e:
            logger.error(f"Failed to initialize semantic cache: {e}", exc_info=True)
    
    async def get(
        self,
        cache_type: CacheType,
        query: str,
        min_security_level: int,
        is_department_only: bool = False,
        department_id: Optional[int] = None
    ) -> tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """
        Get entry from semantic cache with security filtering.
        
        Args:
            cache_type: "response" or "context"
            query: User query text
            min_security_level: User's minimum security clearance level
            is_department_only: Whether this is a department-scoped request
            department_id: User's department ID (if applicable)
        
        Returns:
            Tuple of (result, access_denied_info):
            - result: Cached entry or None
            - access_denied_info: None if cache miss/access granted, Dict if access denied
            
            Access Denied Info:
            {
                "access_denied": True,
                "is_departmental": bool  # True if department restriction, False if org-wide
            }
        """
        cache = self._get_cache(cache_type)
        if not cache:
            return None, None
        
        try:
            # Check cache
            results = cache.check(
                prompt=query,
                return_fields=["response", "metadata"],
                num_results=1
            )
            
            if not results:
                logger.debug(f"{cache_type.capitalize()} cache MISS for query: '{query[:50]}...'")
                return None, None
            
            # Parse cached entry
            cached = results[0]
            response_data = cached.get("response")
            
            if not response_data:
                return None, None
            
            try:
                cache_entry = json.loads(response_data)
            except Exception as e:
                logger.error(f"Error parsing cache entry: {e}")
                return None, None
            
            # Check security clearance
            has_access, is_departmental = self._check_clearance(
                cache_entry,
                min_security_level,
                is_department_only,
                department_id
            )
            
            if not has_access:
                logger.info(
                    f"{cache_type.capitalize()} cache HIT but ACCESS DENIED for query: '{query[:50]}...'"
                )
                return None, {
                    "access_denied": True,
                    "is_departmental": is_departmental
                }
            
            # User has access - get variations
            variations = cache_entry.get("variations", [])
            is_encrypted = cache_entry.get("is_encrypted", False)
            
            if not variations:
                logger.debug("Cache entry has no variations")
                return None, None
            
            # Check if at max capacity internally
            max_entries = self.config[cache_type].get("max_entries", 1)
            at_capacity = len(variations) >= max_entries
            
            # If not at capacity, return None (pipeline continues to add variation)
            if not at_capacity:
                logger.debug(f"Cache hit but below max_entries ({len(variations)}/{max_entries}), continuing pipeline")
                return None, None
            
            # At capacity - select random variation and return
            selected = random.choice(variations)
            text = selected.get("text")
            
            # Decrypt if needed (check root-level flag)
            if is_encrypted:
                text = self._decrypt_data(text, cache_type)
                if text is None:
                    logger.warning(f"Failed to decrypt {cache_type} cache, treating as miss")
                    return None, None
            
            logger.info(
                f"{cache_type.capitalize()} cache HIT (at capacity: {len(variations)}/{max_entries}) for query: '{query[:50]}...'"
            )
            
            return text, None
        
        except Exception as e:
            logger.error(f"Error retrieving from {cache_type} cache: {e}", exc_info=True)
            return None, None
    
    async def set(
        self,
        cache_type: CacheType,
        query: str,
        entry: Any,
        min_security_level: int,
        is_department_only: bool = False,
        department_id: Optional[int] = None
    ):
        """
        Store entry in semantic cache with security metadata.
        
        Args:
            cache_type: "response" or "context"
            query: User query text
            entry: Response or context data to cache
            min_security_level: Minimum security clearance required to access this entry
            is_department_only: Whether content is department-restricted
            department_id: Department ID for department-restricted content
        """
        cache = self._get_cache(cache_type)
        if not cache:
            return
        
        try:
            encrypt_enabled = self.config[cache_type].get("encrypt", False)
            max_entries = self.config[cache_type].get("max_entries", 1)
            
            # Encrypt if enabled (at root level)
            text = entry
            is_encrypted = False
            
            if encrypt_enabled:
                text = self._encrypt_data(entry, cache_type)
                is_encrypted = True
            
            # Check if entry exists
            results = cache.check(
                prompt=query,
                return_fields=["response"],
                num_results=1
            )
            
            if results and results[0].get("response"):
                # Entry exists, add variation
                try:
                    cache_entry = json.loads(results[0]["response"])
                    variations = cache_entry.get("variations", [])
                    
                    # Check if at max capacity
                    if len(variations) >= max_entries:
                        logger.debug(f"Max entries ({max_entries}) reached for query: '{query[:50]}...'")
                        return
                    
                    # Add new variation (just the text)
                    variations.append({"text": text})
                    
                    # Update cache entry
                    cache_entry["variations"] = variations
                    cache_entry["is_encrypted"] = is_encrypted
                    
                    cache.store(
                        prompt=query,
                        response=json.dumps(cache_entry)
                    )
                    
                    logger.debug(
                        f"Added variation to {cache_type} cache (total={len(variations)}/{max_entries}) for query: '{query[:50]}...'"
                    )
                except Exception as e:
                    logger.error(f"Error adding variation: {e}")
            else:
                # New entry with security metadata at root
                cache_entry = {
                    "query": query,
                    "is_encrypted": is_encrypted,
                    "min_security_level": min_security_level,
                    "is_department_only": is_department_only,
                    "department_id": department_id,
                    "variations": [{"text": text}]
                }
                
                cache.store(
                    prompt=query,
                    response=json.dumps(cache_entry)
                )
                
                logger.debug(
                    f"Stored new {cache_type} cache entry for query: '{query[:50]}...' "
                    f"(security={min_security_level}, dept_only={is_department_only}, encrypted={is_encrypted})"
                )
        
        except Exception as e:
            logger.error(f"Error storing in {cache_type} cache: {e}", exc_info=True)
    
    async def clear(self, cache_type: Optional[CacheType] = None):
        """
        Clear semantic cache entries.
        
        Purpose:
        - Development/testing: Clear cache to test fresh responses
        - Cache invalidation: Remove outdated entries when documents updated
        - Admin operations: Reset cache when needed
        - Troubleshooting: Clear corrupted cache entries
        
        Args:
            cache_type: Specific cache to clear ("response" or "context"), or None to clear both
        """
        try:
            if cache_type:
                cache = self._get_cache(cache_type)
                if cache:
                    cache.clear()
                    logger.info(f"Cleared {cache_type} semantic cache")
            else:
                if self.response_cache:
                    self.response_cache.clear()
                if self.context_cache:
                    self.context_cache.clear()
                logger.info("Cleared all semantic caches")
        
        except Exception as e:
            logger.error(f"Error clearing semantic cache: {e}", exc_info=True)
    
    def _get_cache(self, cache_type: CacheType) -> Optional[RedisVLSemanticCache]:
        """Get the appropriate cache instance."""
        if cache_type == "response":
            return self.response_cache
        elif cache_type == "context":
            return self.context_cache
        return None
    
    def _check_clearance(
        self,
        entry: Dict[str, Any],
        user_security_level: int,
        user_is_department: bool,
        user_department_id: Optional[int]
    ) -> tuple[bool, bool]:
        """
        Check if user has clearance to access cache entry.
        
        Returns:
            Tuple of (has_access, is_departmental):
            - has_access: True if user has sufficient clearance
            - is_departmental: True if this is a department restriction, False if org-wide
        """
        try:
            min_security = entry.get("min_security_level", 1)
            is_dept_only = entry.get("is_department_only", False)
            cache_dept_id = entry.get("department_id")
            
            if is_dept_only:
                # Department-only content - check department match and security level
                if user_department_id is None:
                    return False, True
                
                if cache_dept_id and user_department_id != cache_dept_id:
                    return False, True
                
                if user_security_level < min_security:
                    return False, True
                
                return True, True
            else:
                # Organization-wide content - check org security level
                if user_security_level < min_security:
                    return False, False
                
                return True, False
        
        except Exception as e:
            logger.warning(f"Error checking clearance: {e}")
            return False, entry.get("is_department_only", False)
    
    def _encrypt_data(self, data: Any, cache_type: CacheType) -> str:
        """Encrypt data for caching."""
        try:
            json_data = json.dumps(data) if not isinstance(data, str) else data
            purpose = f"semantic_cache_{cache_type}"
            return encrypt(json_data, purpose=purpose, version=1)
        except Exception as e:
            logger.error(f"Encryption failed for {cache_type}: {e}")
            return json.dumps(data) if not isinstance(data, str) else data
    
    def _decrypt_data(self, encrypted_data: str, cache_type: CacheType) -> Any:
        """Decrypt cached data."""
        try:
            if ":" in encrypted_data and encrypted_data.startswith("v"):
                purpose = f"semantic_cache_{cache_type}"
                decrypted = decrypt(encrypted_data, purpose=purpose)
                try:
                    return json.loads(decrypted)
                except:
                    return decrypted
            else:
                # Unencrypted data
                try:
                    return json.loads(encrypted_data)
                except:
                    return encrypted_data
        except Exception as e:
            logger.error(f"Decryption failed for {cache_type}: {e}")
            return None

# Singleton instance
_semantic_cache: Optional[SemanticCache] = None
_semantic_cache_supported: Optional[bool] = None
_semantic_cache_enabled: Optional[bool] = False  # Global enabled status: config + support verified 

async def verify_semantic_cache_support() -> bool:
    """
    Verify Redis supports RediSearch module for vector operations.
    
    The correct module name is 'search' (RediSearch module).    
    Returns:
        True if RediSearch module is available, False otherwise
    """
    global _semantic_cache_supported
    global _semantic_cache_enabled    
    
    # Return cached result if already checked
    if _semantic_cache_supported is not None:
        return _semantic_cache_supported
    
    try:
        cache = get_cache()
        redis_client = cache.redis_client
        
        if redis_client is None:
            logger.warning("✗ Redis not available (using in-memory cache)")
            _semantic_cache_supported = False
            _semantic_cache_enabled = False
            return False
        
        # Get all loaded modules (async call)
        modules = await redis_client.module_list()
        
        # Parse module names - redis.asyncio returns list of dicts
        module_names = []
        for module in modules:
            try:
                if isinstance(module, dict):
                    # Direct dict access
                    name = module.get('name', '')
                    if name:
                        module_names.append(str(name))
            except Exception as e:
                logger.debug(f"Error parsing module {module}: {e}")
        
        # Check for RediSearch module (name is 'search')
        has_search = any(name.lower() == 'search' for name in module_names)
        
        if has_search:
            logger.info("✓ Redis vector search supported (RediSearch module detected)")
            _semantic_cache_supported = True
            _semantic_cache_enabled = True
            return True
        else:
            logger.warning(
                f"✗ RediSearch module not detected. Found modules: {module_names}. "
                "Semantic cache requires RediSearch module (name: 'search'). "
                "Install Redis Stack or load RediSearch module. "
                "See: https://redis.io/docs/stack/"
            )
            _semantic_cache_supported = False
            _semantic_cache_enabled = False
            return False
    
    except AttributeError:
        # module_list() not available - old Redis version
        logger.warning(
            "✗ Cannot verify RediSearch module (Redis version too old). "
            "Semantic cache disabled. Upgrade to Redis Stack."
        )
        _semantic_cache_supported = False
        _semantic_cache_enabled = False
        return False
    
    except Exception as e:
        logger.warning(f"✗ Failed to verify RediSearch support: {e}")
        _semantic_cache_supported = False
        _semantic_cache_enabled = False
        return False

def is_semantic_cache_enabled() -> bool:
    """Check if semantic cache is enabled globally."""
    # If explicitly set to False, it's disabled
    if _semantic_cache_enabled is False:
        return False
    # If not yet initialized, default to False
    if _semantic_cache_enabled is None:
        return False
    return True

def get_semantic_cache() -> Optional[SemanticCache]:
    """Get semantic cache singleton instance if enabled."""
    global _semantic_cache
    
    # If semantic cache is not enabled, don't initialize
    if not is_semantic_cache_enabled():
        return None
    
    # Create instance if needed
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    
    return _semantic_cache