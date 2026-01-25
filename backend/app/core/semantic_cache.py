"""
Semantic Cache using RedisVL

Simplified semantic caching implementation leveraging RedisVL's built-in SemanticCache.
Provides two-tier caching (response and context) with security-aware access control.
"""

import json
from typing import Optional, Dict, Any, List, Literal
from redisvl.extensions.cache.llm import SemanticCache as RedisVLSemanticCache

from app.core import get_logger
from app.config.settings import settings
from app.core.cache import get_cache
from app.utils.encryption import encrypt, decrypt, EncryptionError, DecryptionError

logger = get_logger(__name__)

CacheType = Literal["response", "context"]


class SemanticCache:
    """
    Two-tier semantic cache using RedisVL.
    
    Response Cache: Caches final LLM responses (lower threshold, shorter TTL)
    Context Cache: Caches retrieved documents (higher threshold, longer TTL)
    
    Features:
    - Simplified implementation using RedisVL
    - Security-aware caching with metadata filtering
    - Independent enable/disable for each tier
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
            
            redis_url = settings.cache_settings.REDIS_URL or "redis://localhost:6379"
            
            # Initialize response cache
            if self.config["response"]["enabled"]:
                self.response_cache = RedisVLSemanticCache(
                    name="rag_response_cache",
                    redis_url=redis_url,
                    distance_threshold=self.config["response"]["threshold"],
                    ttl=self.config["response"]["ttl_seconds"],
                    vectorizer=None  # Will use existing embeddings
                )
                logger.info(
                    f"Response cache initialized (threshold={self.config['response']['threshold']}, "
                    f"TTL={self.config['response']['ttl_seconds']}s)"
                )
            
            # Initialize context cache
            if self.config["context"]["enabled"]:
                self.context_cache = RedisVLSemanticCache(
                    name="rag_context_cache",
                    redis_url=redis_url,
                    distance_threshold=self.config["context"]["threshold"],
                    ttl=self.config["context"]["ttl_seconds"],
                    vectorizer=None  # Will use existing embeddings
                )
                logger.info(
                    f"Context cache initialized (threshold={self.config['context']['threshold']}, "
                    f"TTL={self.config['context']['ttl_seconds']}s)"
                )
        
        except Exception as e:
            logger.error(f"Failed to initialize semantic cache: {e}", exc_info=True)
    
    async def get(
        self,
        cache_type: CacheType,
        query: str,
        user_security_level: int,
        user_department_id: Optional[int] = None,
        user_department_security_level: Optional[int] = None
    ) -> tuple[Optional[Any], bool]:
        """
        Get entry from semantic cache with security filtering.
        
        Args:
            cache_type: "response" or "context"
            query: Query text
            user_security_level: User's organization-level security clearance
            user_department_id: User's department ID
            user_department_security_level: User's department-level security clearance
        
        Returns:
            Tuple of (entry, should_continue_pipeline)
            - entry: Cached entry or None if no cache hit
            - should_continue_pipeline: Always False for RedisVL (single entry per cache)
        """
        cache = self._get_cache(cache_type)
        if not cache:
            return None, False
        
        try:
            # Build filter metadata for security
            filters = self._build_security_filters(
                user_security_level,
                user_department_id,
                user_department_security_level
            )
            
            # Check cache with RedisVL
            results = cache.check(
                prompt=query,
                return_fields=["response", "metadata"],
                num_results=1
            )
            
            if results:
                result = results[0]
                metadata = result.get("metadata", {})
                
                # Validate security access
                if not self._validate_security_access(
                    metadata,
                    user_security_level,
                    user_department_id,
                    user_department_security_level
                ):
                    logger.debug(f"Cache hit rejected due to security mismatch for: '{query[:50]}...'")
                    return None, False
                
                # Get response and decrypt if encryption is enabled
                encrypted_response = result.get("response")
                
                if self.config[cache_type].get("encrypt", False):
                    # Encryption enabled - decrypt the data
                    response = self._decrypt_data(encrypted_response, cache_type)
                    if response is None:
                        logger.warning(f"Failed to decrypt {cache_type} cache data, treating as cache miss")
                        return None, False
                else:
                    # No encryption - parse JSON directly
                    try:
                        response = json.loads(encrypted_response)
                    except Exception as e:
                        logger.error(f"Error parsing {cache_type} cache data: {e}", exc_info=True)
                        return None, False
                
                logger.info(f"{cache_type.capitalize()} cache HIT for query: '{query[:50]}...'")
                return response, False
            
            logger.debug(f"{cache_type.capitalize()} cache MISS for query: '{query[:50]}...'")
            return None, False
        
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
        Store entry in semantic cache with security metadata.
        
        Args:
            cache_type: "response" or "context"
            query: Query text
            entry: Response or context data
            min_security_level: Minimum security level required
            is_departmental: Whether this is department-specific
            department_ids: List of department IDs (if departmental)
        """
        cache = self._get_cache(cache_type)
        if not cache:
            return
        
        try:
            # Build security metadata
            metadata = {
                "min_security_level": min_security_level or 0,
                "is_departmental": is_departmental,
                "department_ids": ",".join(map(str, department_ids)) if department_ids else ""
            }
            
            # Encrypt data if encryption is enabled
            if self.config[cache_type].get("encrypt", False):
                # Encryption enabled - encrypt the data
                encrypted_entry = self._encrypt_data(entry, cache_type)
            else:
                # No encryption - serialize to JSON directly
                encrypted_entry = json.dumps(entry)
            
            # Store in RedisVL cache
            cache.store(
                prompt=query,
                response=encrypted_entry,
                metadata=metadata
            )
            
            logger.debug(f"Stored {cache_type} cache entry for query: '{query[:50]}...'")
        
        except Exception as e:
            logger.error(f"Error storing in {cache_type} cache: {e}", exc_info=True)
    
    async def clear(self, cache_type: Optional[CacheType] = None):
        """Clear semantic cache entries."""
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
    
    def _build_security_filters(
        self,
        user_security_level: int,
        user_department_id: Optional[int],
        user_department_security_level: Optional[int]
    ) -> Dict[str, Any]:
        """Build security filter metadata."""
        return {
            "user_security_level": user_security_level,
            "user_department_id": user_department_id or 0,
            "user_department_security_level": user_department_security_level or 0
        }
    
    def _validate_security_access(
        self,
        metadata: Dict[str, Any],
        user_security_level: int,
        user_department_id: Optional[int],
        user_department_security_level: Optional[int]
    ) -> bool:
        """Validate if user can access cached entry based on security metadata."""
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
                    dept_ids_str = metadata.get("department_ids", "")
                    if dept_ids_str:
                        dept_ids = [int(d) for d in dept_ids_str.split(",") if d]
                        if user_department_id not in dept_ids:
                            return False
            else:
                # Organization-level content - check org clearance
                if user_security_level < min_security:
                    return False
            
            return True
        
        except Exception as e:
            logger.warning(f"Error validating security access: {e}")
            return False
    
    def _encrypt_data(self, data: Any, cache_type: CacheType) -> str:
        """Encrypt cache data. Only call this if encryption is enabled."""
        try:
            # Serialize data to JSON
            json_data = json.dumps(data)
            
            # Encrypt using purpose-specific key
            purpose = f"semantic_cache_{cache_type}"
            encrypted = encrypt(json_data, purpose=purpose, version=1)
            
            logger.debug(f"Encrypted {cache_type} cache data")
            return encrypted
        
        except EncryptionError as e:
            logger.error(f"Encryption failed for {cache_type} cache: {e}")
            # Fall back to unencrypted data
            return json.dumps(data)
        except Exception as e:
            logger.error(f"Error encrypting {cache_type} cache data: {e}", exc_info=True)
            return json.dumps(data)
    
    def _decrypt_data(self, encrypted_data: str, cache_type: CacheType) -> Any:
        """Decrypt cache data. Only call this if encryption is enabled."""
        try:
            # Check if data is encrypted (has version prefix)
            if ":" in encrypted_data and encrypted_data.startswith("v"):
                # Decrypt using purpose-specific key
                purpose = f"semantic_cache_{cache_type}"
                decrypted = decrypt(encrypted_data, purpose=purpose)
                return json.loads(decrypted)
            else:
                # Legacy unencrypted data (from before encryption was enabled)
                logger.debug(f"Reading legacy unencrypted {cache_type} cache data")
                return json.loads(encrypted_data)
        
        except DecryptionError as e:
            logger.error(f"Decryption failed for {cache_type} cache: {e}")
            # Try to parse as plain JSON (might be legacy data)
            try:
                return json.loads(encrypted_data)
            except:
                return None
        except Exception as e:
            logger.error(f"Error decrypting {cache_type} cache data: {e}", exc_info=True)
            return None


# Singleton instance
_semantic_cache: Optional[SemanticCache] = None


def verify_redis_vl_support() -> bool:
    """
    Verify Redis supports RediSearch module for vector operations.
    
    The correct module name is 'search' (RediSearch module).
    RedisVL requires this module for vector similarity search.
    
    Returns:
        True if RediSearch module is available, False otherwise
    """
    try:
        cache = get_cache()
        if not hasattr(cache, 'redis_client') or cache.redis_client is None:
            logger.warning("✗ Redis not available")
            return False
        
        redis_client = cache.redis_client
        
        # Get all loaded modules
        modules = redis_client.module_list()
        
        # Log available modules for debugging
        module_names = [
            module.get(b'name', b'').decode('utf-8') if isinstance(module.get(b'name', b''), bytes)
            else module.get('name', '')
            for module in modules
        ]
        logger.debug(f"Redis modules detected: {module_names}")
        
        # Check for RediSearch module (name is 'search')
        has_search = any(
            module.get(b'name', b'').decode('utf-8').lower() == 'search' if isinstance(module.get(b'name', b''), bytes)
            else module.get('name', '').lower() == 'search'
            for module in modules
        )
        
        if has_search:
            logger.info("✓ Redis vector search supported (RediSearch module detected)")
            return True
        else:
            logger.warning(
                f"✗ RediSearch module not detected. Found modules: {module_names}. "
                "Semantic cache requires RediSearch module (name: 'search'). "
                "Install Redis Stack or load RediSearch module. "
                "See: https://redis.io/docs/stack/"
            )
            return False
    
    except AttributeError:
        # module_list() not available - old Redis version
        logger.warning(
            "✗ Cannot verify RediSearch module (Redis version too old). "
            "Semantic cache disabled. Upgrade to Redis Stack."
        )
        return False
    
    except Exception as e:
        logger.warning(f"✗ Failed to verify RediSearch support: {e}")
        return False


def get_semantic_cache() -> SemanticCache:
    """Get semantic cache singleton instance."""
    global _semantic_cache
    
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    
    return _semantic_cache
