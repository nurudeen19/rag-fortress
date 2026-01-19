"""
Semantic Cache for Vector Store Queries

Two-tier caching system:
1. Response Cache: Caches final LLM responses
2. Context Cache: Caches retrieved documents before LLM

Each tier supports multiple variations and random selection.
"""

from typing import Optional, Dict, Any, List, Literal
import json
import hashlib
import random
from datetime import datetime
from langchain_core.documents import Document

from app.core import get_logger
from app.config.settings import settings
from app.core.security import encrypt_data, decrypt_data

logger = get_logger(__name__)

CacheType = Literal["response", "context"]


class SemanticCacheCluster:
    """
    Represents a semantic cluster with multiple variations (responses or contexts).
    
    Stores multiple variations for the same semantic query and returns random selections.
    """
    
    def __init__(
        self,
        cache_type: CacheType,
        query: str,
        query_embedding: List[float],
        entries: List[Any],  # List of responses or contexts
        is_encrypted: bool,
        min_security_level: Optional[int],
        is_departmental: bool,
        department_ids: Optional[List[int]],
        timestamp: datetime
    ):
        self.cache_type = cache_type
        self.query = query
        self.query_embedding = query_embedding
        self.entries = entries  # responses or contexts
        self.is_encrypted = is_encrypted
        self.min_security_level = min_security_level
        self.is_departmental = is_departmental
        self.department_ids = department_ids or []
        self.timestamp = timestamp
    
    def can_add_more(self, max_entries: int) -> bool:
        """Check if cluster can accept more entries."""
        return len(self.entries) < max_entries
    
    def add_entry(self, entry: Any):
        """Add a new variation to this cluster (FIFO if at max)."""
        self.entries.append(entry)
        self.timestamp = datetime.utcnow()
    
    def get_random_entry(self) -> Any:
        """Get a random entry from the cluster."""
        return random.choice(self.entries) if self.entries else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "cache_type": self.cache_type,
            "query": self.query,
            "entries": self.entries,
            "is_encrypted": self.is_encrypted,
            "min_security_level": self.min_security_level,
            "is_departmental": self.is_departmental,
            "department_ids": self.department_ids,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], query_embedding: List[float]) -> 'SemanticCacheCluster':
        """Deserialize from dictionary."""
        return cls(
            cache_type=data["cache_type"],
            query=data["query"],
            query_embedding=query_embedding,
            entries=data["entries"],
            is_encrypted=data["is_encrypted"],
            min_security_level=data.get("min_security_level"),
            is_departmental=data.get("is_departmental", False),
            department_ids=data.get("department_ids", []),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class SemanticCache:
    """
    Two-tier semantic cache system using Redis VL.
    
    Response Cache: Caches final LLM responses (lower threshold, shorter TTL)
    Context Cache: Caches retrieved documents (higher threshold, longer TTL)
    
    Features:
    - Multiple variations per semantic cluster
    - Random selection to avoid repetition
    - Security-aware (clearance + department)
    - Per-entry encryption flag
    - Independent enable/disable for each tier
    """
    
    def __init__(self):
        """Initialize semantic cache."""
        # Response cache config
        self.response_enabled = settings.cache_settings.ENABLE_RESPONSE_CACHE
        self.response_ttl = settings.cache_settings.RESPONSE_CACHE_TTL_MINUTES * 60  # Convert to seconds
        self.response_max_entries = settings.cache_settings.RESPONSE_CACHE_MAX_ENTRIES
        self.response_threshold = settings.cache_settings.RESPONSE_CACHE_SIMILARITY_THRESHOLD
        self.response_encrypt = settings.cache_settings.RESPONSE_CACHE_ENCRYPT
        
        # Context cache config
        self.context_enabled = settings.cache_settings.ENABLE_CONTEXT_CACHE
        self.context_ttl = settings.cache_settings.CONTEXT_CACHE_TTL_MINUTES * 60  # Convert to seconds
        self.context_max_entries = settings.cache_settings.CONTEXT_CACHE_MAX_ENTRIES
        self.context_threshold = settings.cache_settings.CONTEXT_CACHE_SIMILARITY_THRESHOLD
        self.context_encrypt = settings.cache_settings.CONTEXT_CACHE_ENCRYPT
        
        self.redis_client = None
        self.embedding_client = None
        
        # Initialize if at least one tier is enabled
        if self.response_enabled or self.context_enabled:
            self._initialize()
    
    def _initialize(self):
        """Initialize Redis VL connection and embedding client."""
        try:
            import redis
            from redis.commands.search.field import VectorField, TextField, NumericField, TagField
            from redis.commands.search.indexDefinition import IndexDefinition, IndexType
            
            # Get Redis connection
            from app.core.cache import get_cache
            base_cache = get_cache()
            
            if not hasattr(base_cache, 'redis_client') or base_cache.redis_client is None:
                logger.warning("Redis not available, semantic cache disabled")
                self.enabled = False
                return
            
            self.redis_client = base_cache.redis_client
            
            # Initialize embedding client
            from app.core.embedding_factory import get_embedding_client
            self.embedding_client = get_embedding_client()
            
            if not self.embedding_client:
                logger.warning("Embedding client not available, semantic cache disabled")
                self.enabled = False
                return
            
            # Create semantic cache index
            self._create_index()
            
            logger.info(
                f"Semantic cache initialized "
                f"(response={self.response_enabled}, context={self.context_enabled})"
            )
        
        except Exception as e:
            logger.error(f"Failed to initialize semantic cache: {e}", exc_info=True)
            self.enabled = False
    
    def _create_index(self):
        """Create Redis search index for semantic cache."""
        try:
            from redis.commands.search.field import VectorField, TextField, TagField, NumericField
            from redis.commands.search.indexDefinition import IndexDefinition, IndexType
            
            index_name = settings.cache_settings.SEMANTIC_CACHE_INDEX_NAME
            
            # Check if index exists
            try:
                self.redis_client.ft(index_name).info()
                logger.debug(f"Semantic cache index '{index_name}' already exists")
                return
            except Exception:
                pass
            
            # Define schema
            schema = [
                VectorField(
                    "query_embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": settings.cache_settings.SEMANTIC_CACHE_VECTOR_DIM,
                        "DISTANCE_METRIC": "COSINE"
                    }
                ),
                TagField("cache_type"),  # "response" or "context"
                TextField("query"),
                NumericField("min_security_level"),
                TagField("is_departmental"),
                TagField("department_ids", separator=","),
                NumericField("timestamp"),
            ]
            
            # Create index
            definition = IndexDefinition(
                prefix=[f"semantic_cache:"],
                index_type=IndexType.HASH
            )
            
            self.redis_client.ft(index_name).create_index(
                fields=schema,
                definition=definition
            )
            
            logger.info(f"Created semantic cache index '{index_name}'")
        
        except Exception as e:
            logger.error(f"Failed to create semantic cache index: {e}", exc_info=True)
            raise
    
    async def get(
        self,
        cache_type: CacheType,
        query: str,
        user_security_level: int,
        user_department_id: Optional[int] = None
    ) -> Optional[Any]:
        """
        Get random entry from semantically similar cluster.
        
        Flow:
        1. Check if cache type is enabled
        2. Generate query embedding
        3. Search for similar cluster with matching security
        4. If found, return random entry
        
        Args:
            cache_type: "response" or "context"
            query: Query text
            user_security_level: User's security clearance
            user_department_id: User's department ID
        
        Returns:
            Random entry from matching cluster, or None if no suitable cache hit
        """
        if cache_type == "response" and not self.response_enabled:
            return None
        if cache_type == "context" and not self.context_enabled:
            return None
        
        try:
            # Generate query embedding
            query_embedding = await self._get_embedding(query)
            if not query_embedding:
                return None
            
            # Search for similar cluster
            cluster = await self._find_similar(
                cache_type,
                query_embedding,
                user_security_level,
                user_department_id
            )
            
            if cluster:
                # Get random entry from cluster
                entry = cluster.get_random_entry()
                if entry:
                    # Decrypt if needed
                    if cluster.is_encrypted:
                        if isinstance(entry, str):
                            entry = json.loads(decrypt_data(entry))
                        elif isinstance(entry, dict) and "data" in entry:
                            entry["data"] = json.loads(decrypt_data(entry["data"]))
                    
                    logger.info(
                        f"{cache_type.capitalize()} cache HIT for query: '{query[:50]}...' "
                        f"(cluster has {len(cluster.entries)} variations)"
                    )
                    return entry
            
            logger.debug(f"{cache_type.capitalize()} cache MISS for query: '{query[:50]}...'")
            return None
        
        except Exception as e:
            logger.error(f"Error retrieving from {cache_type} cache: {e}", exc_info=True)
            return None
    
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
        Add entry to semantic cluster or create new cluster.
        
        Flow:
        1. Check if cache type is enabled
        2. Generate query embedding
        3. Search for existing compatible cluster
        4. If found AND below max_entries: Add to cluster
        5. If found AND at max_entries: Skip (already at capacity)
        6. If not found: Create new cluster
        
        Args:
            cache_type: "response" or "context"
            query: Query text
            entry: Response or context data
            min_security_level: Minimum security level required
            is_departmental: Whether this is department-specific
            department_ids: List of department IDs (if departmental)
        """
        if cache_type == "response" and not self.response_enabled:
            return
        if cache_type == "context" and not self.context_enabled:
            return
        
        try:
            # Generate query embedding
            query_embedding = await self._get_embedding(query)
            if not query_embedding:
                return
            
            # Determine encryption for this entry
            should_encrypt = (
                self.response_encrypt if cache_type == "response" else self.context_encrypt
            )
            
            # Encrypt entry if needed
            encrypted_entry = entry
            if should_encrypt:
                if isinstance(entry, (dict, list)):
                    encrypted_entry = encrypt_data(json.dumps(entry))
                elif isinstance(entry, str):
                    encrypted_entry = encrypt_data(entry)
            
            # Check if similar cluster exists
            existing_cluster = await self._find_cluster_for_new_entry(
                cache_type,
                query_embedding,
                min_security_level,
                is_departmental,
                department_ids or []
            )
            
            max_entries = (
                self.response_max_entries if cache_type == "response" else self.context_max_entries
            )
            
            if existing_cluster:
                # Check if cluster can accept more entries
                if existing_cluster.can_add_more(max_entries):
                    existing_cluster.add_entry(encrypted_entry)
                    await self._update_cluster(existing_cluster, cache_type)
                    logger.debug(
                        f"Added {cache_type} variation to existing cluster "
                        f"({len(existing_cluster.entries)}/{max_entries}): '{query[:50]}...'"
                    )
                else:
                    logger.debug(
                        f"Cluster at capacity ({max_entries}), skipping add: '{query[:50]}...'"
                    )
            else:
                # Create new cluster
                cluster = SemanticCacheCluster(
                    cache_type=cache_type,
                    query=query,
                    query_embedding=query_embedding,
                    entries=[encrypted_entry],
                    is_encrypted=should_encrypt,
                    min_security_level=min_security_level,
                    is_departmental=is_departmental,
                    department_ids=department_ids or [],
                    timestamp=datetime.utcnow()
                )
                await self._store_cluster(cluster, cache_type)
                logger.debug(f"Created new {cache_type} cluster for query: '{query[:50]}...'")
        
        except Exception as e:
            logger.error(f"Error storing in {cache_type} cache: {e}", exc_info=True)
    
    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for query text."""
        try:
            embeddings = await self.embedding_client.aembed_query(text)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}", exc_info=True)
            return None
    
    async def _find_similar(
        self,
        cache_type: CacheType,
        query_embedding: List[float],
        user_security_level: int,
        user_department_id: Optional[int]
    ) -> Optional[SemanticCacheCluster]:
        """
        Find semantically similar cluster that user can access.
        
        Args:
            cache_type: "response" or "context"
            query_embedding: Query vector
            user_security_level: User's security clearance
            user_department_id: User's department ID
        
        Returns:
            Cluster if found and accessible, None otherwise
        """
        try:
            from redis.commands.search.query import Query
            import numpy as np
            
            index_name = settings.cache_settings.SEMANTIC_CACHE_INDEX_NAME
            threshold = (
                self.response_threshold if cache_type == "response" else self.context_threshold
            )
            
            # Build KNN query filtering by cache type
            query_vector = np.array(query_embedding, dtype=np.float32).tobytes()
            
            query = (
                Query(f"@cache_type:{{{cache_type}}}=>[KNN 5 @query_embedding $vec AS score]")
                .return_fields("query", "min_security_level", "is_departmental", "department_ids", "timestamp", "score")
                .sort_by("score")
                .dialect(2)
            )
            
            results = self.redis_client.ft(index_name).search(
                query,
                query_params={"vec": query_vector}
            )
            
            # Find best match that user can access
            for doc in results.docs:
                score = float(doc.score)
                
                # Check similarity threshold
                if score < threshold:
                    continue
                
                # Check security clearance
                min_security = doc.min_security_level
                if min_security and int(min_security) > user_security_level:
                    logger.debug(f"Cache hit rejected: insufficient clearance ({user_security_level} < {min_security})")
                    continue
                
                # Check department access
                is_dept = doc.is_departmental == "true"
                if is_dept:
                    if not user_department_id:
                        logger.debug("Cache hit rejected: dept-only but user has no department")
                        continue
                    
                    dept_ids_str = doc.department_ids
                    if dept_ids_str:
                        dept_ids = [int(d) for d in dept_ids_str.split(",") if d]
                        if user_department_id not in dept_ids:
                            logger.debug(f"Cache hit rejected: dept mismatch ({user_department_id} not in {dept_ids})")
                            continue
                
                # Valid cache hit - retrieve full cluster
                cache_key = doc.id
                cluster_data = self.redis_client.hgetall(cache_key)
                
                if not cluster_data:
                    continue
                
                # Get embedding
                embedding_bytes = cluster_data.get(b"query_embedding", b"")
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
                
                # Get entries
                entries_data = cluster_data.get(b"entries", b"").decode("utf-8")
                entries = json.loads(entries_data)
                
                # Build cluster dict
                cluster_dict = {
                    "cache_type": cache_type,
                    "query": cluster_data.get(b"query", b"").decode("utf-8"),
                    "entries": entries,
                    "is_encrypted": cluster_data.get(b"is_encrypted", b"false").decode("utf-8") == "true",
                    "min_security_level": int(min_security) if min_security else None,
                    "is_departmental": is_dept,
                    "department_ids": dept_ids if is_dept else [],
                    "timestamp": datetime.fromtimestamp(float(doc.timestamp))
                }
                
                return SemanticCacheCluster.from_dict(cluster_dict, embedding)
            
            return None
        
        except Exception as e:
            logger.error(f"Error searching {cache_type} cache: {e}", exc_info=True)
            return None
    
    async def _find_cluster_for_new_entry(
        self,
        cache_type: CacheType,
        query_embedding: List[float],
        min_security_level: Optional[int],
        is_departmental: bool,
        department_ids: List[int]
    ) -> Optional[SemanticCacheCluster]:
        """
        Find existing cluster to add new entry to.
        
        Only returns cluster if security context matches exactly.
        """
        try:
            from redis.commands.search.query import Query
            import numpy as np
            
            index_name = settings.cache_settings.SEMANTIC_CACHE_INDEX_NAME
            threshold = (
                self.response_threshold if cache_type == "response" else self.context_threshold
            )
            
            query_vector = np.array(query_embedding, dtype=np.float32).tobytes()
            
            query = (
                Query(f"@cache_type:{{{cache_type}}}=>[KNN 3 @query_embedding $vec AS score]")
                .return_fields("query", "min_security_level", "is_departmental", "department_ids", "timestamp", "score")
                .sort_by("score")
                .dialect(2)
            )
            
            results = self.redis_client.ft(index_name).search(
                query,
                query_params={"vec": query_vector}
            )
            
            # Find cluster with matching security context
            for doc in results.docs:
                score = float(doc.score)
                
                if score < threshold:
                    continue
                
                # Security context must match exactly
                existing_min_security = int(doc.min_security_level) if doc.min_security_level else None
                if existing_min_security != min_security_level:
                    continue
                
                existing_is_dept = doc.is_departmental == "true"
                if existing_is_dept != is_departmental:
                    continue
                
                if is_departmental:
                    existing_dept_ids = [int(d) for d in doc.department_ids.split(",") if d] if doc.department_ids else []
                    if set(existing_dept_ids) != set(department_ids):
                        continue
                
                # Compatible cluster found
                cache_key = doc.id
                cluster_data = self.redis_client.hgetall(cache_key)
                
                if not cluster_data:
                    continue
                
                # Get embedding
                embedding_bytes = cluster_data.get(b"query_embedding", b"")
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
                
                # Get entries
                entries_data = cluster_data.get(b"entries", b"").decode("utf-8")
                entries = json.loads(entries_data)
                
                cluster_dict = {
                    "cache_type": cache_type,
                    "query": cluster_data.get(b"query", b"").decode("utf-8"),
                    "entries": entries,
                    "is_encrypted": cluster_data.get(b"is_encrypted", b"false").decode("utf-8") == "true",
                    "min_security_level": existing_min_security,
                    "is_departmental": existing_is_dept,
                    "department_ids": existing_dept_ids if existing_is_dept else [],
                    "timestamp": datetime.fromtimestamp(float(doc.timestamp))
                }
                
                cluster = SemanticCacheCluster.from_dict(cluster_dict, embedding)
                cluster.cache_key = cache_key  # Store for update
                return cluster
            
            return None
        
        except Exception as e:
            logger.error(f"Error finding cluster for new entry: {e}", exc_info=True)
            return None
    
    async def _store_cluster(self, cluster: SemanticCacheCluster, cache_type: CacheType):
        """Store new semantic cluster in Redis."""
        try:
            import numpy as np
            
            # Generate unique key from embedding
            embedding_hash = hashlib.md5(np.array(cluster.query_embedding, dtype=np.float32).tobytes()).hexdigest()
            cache_key = f"semantic_cache:{cache_type}:{embedding_hash}"
            
            # Convert embedding to bytes
            embedding_bytes = np.array(cluster.query_embedding, dtype=np.float32).tobytes()
            
            # Prepare entries
            entries_json = json.dumps(cluster.entries)
            
            # Store in Redis hash
            data = {
                "cache_type": cache_type,
                "query": cluster.query,
                "query_embedding": embedding_bytes,
                "entries": entries_json,
                "is_encrypted": "true" if cluster.is_encrypted else "false",
                "min_security_level": cluster.min_security_level or 0,
                "is_departmental": "true" if cluster.is_departmental else "false",
                "department_ids": ",".join(map(str, cluster.department_ids)),
                "timestamp": cluster.timestamp.timestamp(),
            }
            
            ttl = self.response_ttl if cache_type == "response" else self.context_ttl
            
            self.redis_client.hset(cache_key, mapping=data)
            self.redis_client.expire(cache_key, ttl)
            
        except Exception as e:
            logger.error(f"Error storing cache cluster: {e}", exc_info=True)
            raise
    
    async def _update_cluster(self, cluster: SemanticCacheCluster, cache_type: CacheType):
        """Update existing cluster with new entry."""
        try:
            import numpy as np
            
            # Use stored cache key if available
            if hasattr(cluster, 'cache_key'):
                cache_key = cluster.cache_key
            else:
                embedding_hash = hashlib.md5(np.array(cluster.query_embedding, dtype=np.float32).tobytes()).hexdigest()
                cache_key = f"semantic_cache:{cache_type}:{embedding_hash}"
            
            # Update entries and timestamp
            entries_json = json.dumps(cluster.entries)
            self.redis_client.hset(cache_key, "entries", entries_json)
            self.redis_client.hset(cache_key, "timestamp", cluster.timestamp.timestamp())
            
            # Refresh TTL
            ttl = self.response_ttl if cache_type == "response" else self.context_ttl
            self.redis_client.expire(cache_key, ttl)
            
        except Exception as e:
            logger.error(f"Error updating cache cluster: {e}", exc_info=True)
            raise
    
    async def clear(self, cache_type: Optional[CacheType] = None):
        """Clear semantic cache clusters."""
        try:
            if cache_type:
                pattern = f"semantic_cache:{cache_type}:*"
            else:
                pattern = "semantic_cache:*"
            
            cursor = 0
            deleted = 0
            
            while True:
                cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    self.redis_client.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
            
            cache_desc = f"{cache_type} " if cache_type else ""
            logger.info(f"Cleared {deleted} semantic {cache_desc}cache clusters")
        
        except Exception as e:
            logger.error(f"Error clearing semantic cache: {e}", exc_info=True)


# Singleton instance
_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache() -> SemanticCache:
    """Get semantic cache singleton instance."""
    global _semantic_cache
    
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    
    return _semantic_cache
