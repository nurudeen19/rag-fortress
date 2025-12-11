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

# Vector Database - FAISS (local storage, Python 3.14+ compatible)
VECTOR_DB_PROVIDER=faiss
VECTOR_STORE_PERSIST_DIRECTORY=./data/vector_store
VECTOR_STORE_COLLECTION_NAME=rag_fortress
```

**Note:** For Python 3.11-3.13 users who prefer Chroma, see the [Legacy Installation](#legacy-chroma-python-311-313-only) section below.

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

### 1. FAISS (Recommended for Development)

**✅ DEFAULT FOR PYTHON 3.14+**

**Best for:** Development, testing, local deployments, Python 3.14+ compatibility

**Configuration:**
```bash
VECTOR_DB_PROVIDER=faiss
VECTOR_STORE_PERSIST_DIRECTORY=./data/vector_store
VECTOR_STORE_COLLECTION_NAME=rag_fortress
```

**Features:**
- Facebook AI Similarity Search
- Fast and efficient similarity search
- Local file-based persistence
- No external dependencies
- Python 3.14+ compatible
- Production-grade algorithms (though not distributed)

**Pros:**
- Zero setup - works out of the box
- No external services required
- Fast local search
- Proven algorithms from Facebook AI Research
- Compatible with latest Python versions (3.14+)
- Automatic save/load from disk

**Cons:**
- Not suitable for distributed deployments
- Limited to single-machine scale
- Basic filtering capabilities
- Not recommended for production at scale
- No built-in replication or clustering

**When to Use:**
- Development and testing
- Small to medium datasets (< 100k documents)
- Single-server deployments
- Quick prototypes
- Python 3.14+ environments

### 2. Chroma (Currently Python 3.11-3.13 Only)

**⚠️ NOT YET COMPATIBLE WITH PYTHON 3.14+ (as of December 2025)**

**Important:** Chroma is **currently not compatible with Python 3.14 and higher** due to dependency conflicts with pydantic-core and related packages. 

**Current Status (December 2025):**
- ✅ **Python 3.11-3.13**: Fully supported via pip installation
- ❌ **Python 3.14+**: Not yet compatible
- 🔄 **Active Development**: The Chroma team is working on Python 3.14 support
- 📌 **Track Progress**: Check [Chroma GitHub Issues](https://github.com/chroma-core/chroma/issues/5996) for updates

**What This Means:**
- **For Python 3.14+ users:** Use FAISS (default) or migrate to Qdrant/Pinecone until Chroma is updated
- **For Python 3.11-3.13 users:** Chroma is still supported via pip installation (see [Legacy Installation Guide](INSTALLATION_LEGACY.md))
- **Future:** Once Chroma releases Python 3.14 support, it can be used again with all Python versions

**Configuration (Python 3.11-3.13 only):**
```bash
VECTOR_DB_PROVIDER=chroma
VECTOR_STORE_PERSIST_DIRECTORY=./data/vector_store
VECTOR_STORE_COLLECTION_NAME=rag_fortress
```

**Installation (requires pip, not uv):**
```bash
pip install langchain-chroma chromadb
```

**Pros:**
- Easy setup (on compatible Python versions)
- No external dependencies
- Good for development/testing

**Cons:**
- **❌ NOT compatible with Python 3.14+**
- Performance limitations
- No distributed deployment
- Not production-ready
- Blocked in production environment
- Limited to Python 3.11-3.13

**Migration Path (For Python 3.14+ Users):**
If you're using Chroma and upgrading to Python 3.14:
1. Export your existing documents from Chroma
2. Switch to FAISS (development) or Qdrant (production)
3. Re-import documents
4. Update your `.env`: `VECTOR_DB_PROVIDER=faiss`
5. **Future**: Once Chroma releases Python 3.14 support, you can migrate back to Chroma if desired

### 3. Qdrant (Recommended for Production)

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

### 4. Pinecone

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

### 5. Weaviate

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



## Vector Store Architecture

### Factory Pattern

The `vector_store_factory.py` provides provider-agnostic vector store creation using LangChain's native implementations:

```python
def get_vector_store(
    embeddings: Embeddings,
    provider: Optional[str] = None,
    collection_name: Optional[str] = None,
    **kwargs
) -> VectorStore:
    """Get or create a LangChain vector store instance."""
```

**Supported Providers:**
- **FAISS** - `langchain_community.vectorstores.FAISS` (default for Python 3.14+)
- **Chroma** - `langchain_chroma.Chroma` (legacy, Python 3.11-3.13 only)
- **Qdrant** - `langchain_qdrant.QdrantVectorStore`
- **Pinecone** - `langchain_pinecone.PineconeVectorStore`
- **Weaviate** - `langchain_weaviate.WeaviateVectorStore`

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

| Feature | FAISS | Chroma | Qdrant | Pinecone | Weaviate |
|---------|-------|--------|--------|----------|----------|
| **Python 3.14+** | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Deployment** | Local | Local | Self/Cloud | Cloud | Self/Cloud |
| **Production** | ⚠️ | ❌ | ✅ | ✅ | ✅ |
| **Cost** | Free | Free | $ | $$$ | $ |
| **Performance** | High | Medium | High | High | High |
| **Scalability** | Low | Low | High | Very High | High |
| **Setup Complexity** | Low | Low | Medium | Low | High |
| **Filtering** | Basic | Basic | Advanced | Advanced | Advanced |
| **Persistence** | File | File | DB | Cloud | DB |
| **gRPC Support** | ❌ | ❌ | ✅ | ❌ | ✅ |

## Best Practices

### Embedding Selection

1. **Development:** Use HuggingFace (free, no API key)
2. **Production:** Use OpenAI or Cohere (quality + reliability)
3. **Offline:** Use HuggingFace with downloaded models
4. **Multilingual:** Use Cohere or multilingual HuggingFace models

### Vector Database Selection

1. **Development:** Use FAISS (easy setup, Python 3.14+ compatible)
2. **Development (Legacy Python 3.11-3.13):** Use Chroma (requires pip installation)
3. **Production (self-hosted):** Use Qdrant (performance + cost)
4. **Production (managed):** Use Pinecone (simplicity + support)
5. **High-scale:** Use Pinecone (scalability + managed infrastructure)

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

---

## Legacy: Chroma (Python 3.11-3.13 Only)

For complete installation instructions, see the [Legacy Installation Guide](INSTALLATION_LEGACY.md).

### Python Version Compatibility

**Chroma is NOT compatible with Python 3.14+** due to dependency conflicts with chromadb's dependencies (notably pydantic-core and related packages that haven't been updated for Python 3.14).

### For Python 3.11-3.13 Users Only

If you're using Python 3.11, 3.12, or 3.13 and want to use Chroma instead of FAISS, see the complete [Legacy Installation Guide](INSTALLATION_LEGACY.md).

#### Quick Configuration

```bash
cd backend

# Create virtual environment with Python 3.11-3.13
python3.13 -m venv venv  # or python3.11, python3.12

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# macOS/Linux:
source venv/bin/activate

# Install using pip with requirements.txt (includes Chroma)
pip install -r requirements.txt
```

#### Configuration

```bash
# In your .env file
VECTOR_DB_PROVIDER=chroma
VECTOR_STORE_PERSIST_DIRECTORY=./data/vector_store
VECTOR_STORE_COLLECTION_NAME=rag_fortress
```

#### Migration from FAISS to Chroma

If you've been using FAISS and want to migrate to Chroma (on Python 3.11-3.13):

```python
# 1. Export documents from FAISS
from app.core.vector_store_factory import get_vector_store
from app.core.embedding_factory import get_embedding_provider

embeddings = get_embedding_provider()

# Get FAISS store
faiss_store = get_vector_store(embeddings, provider="faiss")
# Export all documents (implement based on your document structure)

# 2. Switch provider in .env
# VECTOR_DB_PROVIDER=chroma

# 3. Import to Chroma
chroma_store = get_vector_store(embeddings, provider="chroma")
# Add documents to Chroma
```

### Why This Limitation Exists?

As of December 2025, the `chromadb` package and its dependencies have not yet been updated to support Python 3.14's changes to the C-API and internal module structures. The main affected packages are:
- `pydantic-core` (C-extensions not yet compatible)
- `hnswlib` (requires C-API updates)
- Other C-extension dependencies

**Current GitHub Issues:**
- [Issue #5996: Chroma import fails on python 3.14.2](https://github.com/chroma-core/chroma/issues/5996)
- [Issue #5983: Installation Fails on macOS M2 with Python 3.14](https://github.com/chroma-core/chroma/issues/5983)

**Expected Resolution:**
The Chroma team is aware of these issues and working on updates. Once their dependencies are updated for Python 3.14 compatibility, Chroma will work with Python 3.14+. Check the issues above for the latest status.

### Recommended Alternatives

For Python 3.14+ users:
1. **FAISS** - Default, local, fast, compatible (recommended for development)
2. **Qdrant** - Production-grade, self-hosted or cloud (recommended for production)
3. **Pinecone** - Fully managed, enterprise-grade
4. **Weaviate** - Open-source, feature-rich
5. **Milvus** - Scalable, cloud-native

All of these alternatives are fully compatible with Python 3.14+ and provide better performance and features than Chroma for production use cases.
