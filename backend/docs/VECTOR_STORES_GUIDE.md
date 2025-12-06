# Vector Stores & Embeddings Guide

## Overview

RAG Fortress supports multiple embedding providers and vector databases with a provider-agnostic architecture. Switch between providers using environment variables without code changes.

## Quick Start

### Development Setup (Free)

```bash
# Embeddings - HuggingFace (no API key needed)
EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HF_EMBEDDING_DEVICE=cpu

# Vector Database - Chroma (local storage)
VECTOR_DB_PROVIDER=chroma
CHROMA_PERSIST_DIRECTORY=./data/vector_store
CHROMA_COLLECTION_NAME=rag_fortress
```

### Production Setup

```bash
# Embeddings - OpenAI
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Vector Database - Qdrant (recommended)
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
QDRANT_COLLECTION_NAME=rag_fortress
```

## Embedding Providers

### 1. HuggingFace (Free)

**Best for:** Development, offline deployments, cost-conscious projects

**Configuration:**
```bash
EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HF_EMBEDDING_DEVICE=cpu  # or cuda
HF_API_TOKEN=  # Optional for public models
```

**Popular Models:**
- `sentence-transformers/all-MiniLM-L6-v2` - Fast, good quality (384 dims)
- `sentence-transformers/all-mpnet-base-v2` - Better quality (768 dims)
- `BAAI/bge-small-en-v1.5` - Optimized for retrieval (384 dims)

**Pros:**
- No API costs
- Works offline
- Fast local inference
- Many model options

**Cons:**
- Requires compute resources
- Slower than API providers
- Need GPU for large models

### 2. OpenAI

**Best for:** Production, high-quality embeddings, easy setup

**Configuration:**
```bash
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536  # Optional
```

**Models:**
- `text-embedding-3-small` - Fast, cost-effective (512-1536 dims)
- `text-embedding-3-large` - Highest quality (256-3072 dims)
- `text-embedding-ada-002` - Legacy model (1536 dims)

**Pros:**
- High quality
- Fast API
- Reliable uptime
- Flexible dimensions

**Cons:**
- API costs
- Requires internet
- Rate limits

### 3. Google Gemini

**Best for:** Google ecosystem integration

**Configuration:**
```bash
EMBEDDING_PROVIDER=google
GOOGLE_API_KEY=your-key
GOOGLE_EMBEDDING_MODEL=models/embedding-001
GOOGLE_EMBEDDING_TASK_TYPE=retrieval_document  # or retrieval_query
```

**Task Types:**
- `retrieval_document` - For document chunks
- `retrieval_query` - For queries
- `classification` - For classification tasks
- `clustering` - For clustering tasks

**Pros:**
- Competitive pricing
- Good quality
- Google ecosystem integration

**Cons:**
- Fewer model options
- Requires Google account

### 4. Cohere

**Best for:** Multilingual support, semantic search

**Configuration:**
```bash
EMBEDDING_PROVIDER=cohere
COHERE_API_KEY=your-key
COHERE_EMBEDDING_MODEL=embed-english-v3.0
COHERE_INPUT_TYPE=search_document  # or search_query
```

**Input Types:**
- `search_document` - For indexing documents
- `search_query` - For query embeddings
- `classification` - For classification
- `clustering` - For clustering

**Pros:**
- Strong multilingual support
- Optimized for search
- Competitive pricing

**Cons:**
- Less popular than OpenAI
- Fewer integration examples

### 5. Voyage AI

**Best for:** High-quality embeddings, specialized domains

**Configuration:**
```bash
EMBEDDING_PROVIDER=voyage
VOYAGE_API_KEY=your-key
VOYAGE_EMBEDDING_MODEL=voyage-2
```

**Pros:**
- Very high quality
- Good for specialized domains
- Competitive pricing

**Cons:**
- Newer provider
- Smaller ecosystem

## Vector Databases

### 1. Chroma (Development Only)

**⚠️ NOT RECOMMENDED FOR PRODUCTION**

**Configuration:**
```bash
VECTOR_DB_PROVIDER=chroma
CHROMA_PERSIST_DIRECTORY=./data/vector_store
CHROMA_COLLECTION_NAME=rag_fortress
```

**Pros:**
- Easy setup
- No external dependencies
- Good for development/testing

**Cons:**
- Performance limitations
- No distributed deployment
- Not production-ready
- Blocked in production environment

### 2. Qdrant (Recommended)

**✅ PRODUCTION RECOMMENDED**

**Local Deployment:**
```bash
VECTOR_DB_PROVIDER=qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=rag_fortress
QDRANT_PREFER_GRPC=false
```

**Cloud Deployment:**
```bash
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
QDRANT_COLLECTION_NAME=rag_fortress
```

**Pros:**
- Excellent performance
- Self-hosted or cloud
- Rich filtering capabilities
- Active development
- Affordable

**Cons:**
- Requires setup for self-hosted
- Less mature than Pinecone

### 3. Pinecone

**Fully managed cloud vector database**

**Configuration:**
```bash
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=us-east1-gcp
PINECONE_INDEX_NAME=rag-fortress
```

**Pros:**
- Fully managed
- Excellent performance
- Enterprise support
- Reliable uptime

**Cons:**
- More expensive
- Cloud-only
- Vendor lock-in

### 4. Weaviate

**Open-source vector search engine**

**Configuration:**
```bash
VECTOR_DB_PROVIDER=weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=optional-key
WEAVIATE_INDEX_NAME=RagFortress
```

**Pros:**
- Open-source
- Self-hosted or cloud
- GraphQL API
- Rich schema support

**Cons:**
- More complex setup
- Steeper learning curve
- Smaller community

### 5. Milvus

**High-performance vector database**

**Configuration:**
```bash
VECTOR_DB_PROVIDER=milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=rag_fortress
```

**Pros:**
- Excellent performance
- Scalable
- Open-source
- Enterprise features

**Cons:**
- Complex deployment
- Requires more resources
- Steeper learning curve

## Vector Store Architecture

### Abstract Base Class

All vector stores implement `VectorStoreBase`:

```python
class VectorStoreBase(ABC):
    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents and return IDs"""
        
    @abstractmethod
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[Document]:
        """Search for similar documents"""
        
    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        """Delete documents by IDs"""
        
    @abstractmethod
    async def get_collection_stats(self) -> Dict:
        """Get collection statistics"""
```

### Document Format

Standardized document chunk format:

```python
{
    "id": "uuid-v4",  # Unique identifier
    "content": "chunk text",
    "metadata": {
        # Required
        "file_id": 123,
        "file_name": "document.pdf",
        "chunk_index": 0,
        "source": "path/to/file",
        
        # Security
        "security_level": 2,  # 1-4
        "department_id": 5,
        "is_department_only": false,
        
        # Optional
        "page_number": 1,
        "section": "Introduction",
        "custom_field": "value"
    }
}
```

### Usage Examples

**Add Documents:**
```python
from app.services.vector_store import get_vector_store

vector_store = await get_vector_store()

documents = [
    Document(
        page_content="chunk text",
        metadata={
            "file_id": 123,
            "security_level": 2,
            "department_id": 5
        }
    )
]

ids = await vector_store.add_documents(documents)
```

**Search with Filters:**
```python
# Security-aware search
results = await vector_store.similarity_search(
    query="what is the revenue?",
    k=5,
    filter={
        "security_level": {"$lte": user_clearance},
        "department_id": user_department_id
    }
)
```

**Delete Documents:**
```python
await vector_store.delete(ids=["uuid1", "uuid2"])
```

**Get Stats:**
```python
stats = await vector_store.get_collection_stats()
# Returns: {"total_documents": 1000, "collection_name": "rag_fortress"}
```

## Metadata Filtering

### Supported Operators

- `$eq` - Equal to
- `$ne` - Not equal to
- `$gt` - Greater than
- `$gte` - Greater than or equal to
- `$lt` - Less than
- `$lte` - Less than or equal to
- `$in` - In array
- `$nin` - Not in array

### Examples

**Security-Based Filtering:**
```python
filter = {
    "security_level": {"$lte": 2},  # User clearance ≤ 2
    "is_department_only": False     # Org-wide documents only
}
```

**Department-Based Filtering:**
```python
filter = {
    "$or": [
        {"is_department_only": False},
        {"department_id": {"$in": [1, 2, 3]}}  # User's departments
    ]
}
```

**File-Based Filtering:**
```python
filter = {
    "file_id": {"$in": [10, 20, 30]},  # Specific files
    "security_level": {"$lte": 3}
}
```

## Provider Comparison

| Feature | Chroma | Qdrant | Pinecone | Weaviate | Milvus |
|---------|--------|--------|----------|----------|--------|
| **Deployment** | Local | Self/Cloud | Cloud | Self/Cloud | Self/Cloud |
| **Production** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Cost** | Free | $ | $$$ | $ | $ |
| **Performance** | Medium | High | High | High | Very High |
| **Scalability** | Low | High | Very High | High | Very High |
| **Setup Complexity** | Low | Medium | Low | High | High |
| **Filtering** | Basic | Advanced | Advanced | Advanced | Advanced |
| **gRPC Support** | ❌ | ✅ | ❌ | ✅ | ✅ |

## Best Practices

### Embedding Selection

1. **Development:** Use HuggingFace (free, no API key)
2. **Production:** Use OpenAI or Cohere (quality + reliability)
3. **Offline:** Use HuggingFace with downloaded models
4. **Multilingual:** Use Cohere or multilingual HuggingFace models

### Vector Database Selection

1. **Development:** Use Chroma (easy setup)
2. **Production (self-hosted):** Use Qdrant (performance + cost)
3. **Production (managed):** Use Pinecone (simplicity + support)
4. **High-scale:** Use Milvus or Pinecone (scalability)

### Performance Optimization

**Batch Operations:**
```python
# Good: Batch insert
await vector_store.add_documents(documents)  # 100 docs

# Bad: Individual inserts
for doc in documents:
    await vector_store.add_documents([doc])  # 100 calls
```

**Appropriate K Value:**
```python
# Start small, increase if needed
results = await vector_store.similarity_search(query, k=5)

# Don't retrieve too many
results = await vector_store.similarity_search(query, k=50)  # Slow
```

**Use Filters:**
```python
# Good: Filter early
results = await vector_store.similarity_search(
    query,
    k=5,
    filter={"department_id": 1}  # Reduces search space
)

# Bad: Filter after retrieval
results = await vector_store.similarity_search(query, k=100)
filtered = [r for r in results if r.metadata["department_id"] == 1]
```

## Troubleshooting

### Embeddings Not Loading

**Check provider configuration:**
```python
from app.config import settings
print(settings.EMBEDDING_PROVIDER)
print(settings.get_embedding_config())
```

**Verify API key:**
```bash
echo $OPENAI_API_KEY  # Should not be empty
```

### Vector Store Connection Failed

**Test connection:**
```python
from app.services.vector_store import get_vector_store

try:
    store = await get_vector_store()
    stats = await store.get_collection_stats()
    print(f"Connected! {stats}")
except Exception as e:
    print(f"Connection failed: {e}")
```

**Check service is running:**
```bash
# Qdrant
curl http://localhost:6333/collections

# Weaviate
curl http://localhost:8080/v1/schema
```

### Poor Search Quality

1. **Check embedding model** - Try better model
2. **Adjust chunk size** - Default 1000, try 500-1500
3. **Enable reranking** - Improves relevance
4. **Increase top-k** - Retrieve more candidates
5. **Check metadata filtering** - Might be too restrictive

## Migration Between Providers

### Export Documents

```python
# Export from current provider
documents = []
offset = 0
batch_size = 100

while True:
    batch = await vector_store.get_documents(
        offset=offset,
        limit=batch_size
    )
    if not batch:
        break
    documents.extend(batch)
    offset += batch_size
```

### Import to New Provider

```python
# Switch provider in .env
# VECTOR_DB_PROVIDER=qdrant

# Import documents
new_store = await get_vector_store()
await new_store.add_documents(documents)
```

## See Also

- [Settings Guide](SETTINGS_GUIDE.md) - Configuration details
- [Document Management](DOCUMENT_MANAGEMENT_GUIDE.md) - Document ingestion
- [Retrieval Guide](RETRIEVAL_GUIDE.md) - Search and retrieval
