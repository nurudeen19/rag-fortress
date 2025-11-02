# Vector Store Architecture

## Overview

RAG Fortress implements a **provider-agnostic vector store system** with a standardized document chunk format. This allows you to switch between different vector databases without changing your application code.

## Design Principles

### 1. **Abstract Base Class Pattern**
All vector stores inherit from `VectorStoreBase`, ensuring consistent interface across providers.

### 2. **Standardized Document Format**
Every chunk follows the same structure regardless of the underlying database:

```python
{
    "id": "uuid4",  # UUID for security and uniqueness
    "content": "Text chunk for embedding",
    "metadata": {
        "source": "document.pdf",
        "source_type": "pdf",
        "chunk_index": 0,
        "security_level": "confidential",  # Optional
        "organization": "CompanyX",        # Optional
        "version": "v1.0",
        "timestamp": "2025-11-02T12:00:00Z",
        "tags": ["contract", "legal"],
        "page_number": 1,                  # Optional
        "section": "Introduction",         # Optional
        "char_count": 150,                 # Optional
        "token_count": 35                  # Optional
    }
}
```

### 3. **Separation of Concerns**
- **Chunking**: Separate service handles text splitting
- **Embedding**: Separate service generates vectors
- **Storage**: Vector store only handles storage and retrieval

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Routes, Business Logic)                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  VectorStoreFactory                          │
│  (Creates appropriate store based on config)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ ChromaDB │   │  Qdrant  │   │ Pinecone │  ...
    └──────────┘   └──────────┘   └──────────┘
          │              │              │
          └──────────────┴──────────────┘
                         │
                   VectorStoreBase
                (Abstract Interface)
```

## Supported Providers

| Provider | Status | Use Case | Production Ready |
|----------|--------|----------|------------------|
| **ChromaDB** | ✅ Implemented | Development, Small datasets | ⚠️ Use with caution |
| **Qdrant** | 🚧 Planned | Production, High performance | ✅ Recommended |
| **Pinecone** | 🚧 Planned | Managed cloud service | ✅ Recommended |
| **Weaviate** | 🚧 Planned | GraphQL, Hybrid search | ✅ Yes |
| **Milvus** | 🚧 Planned | Large-scale deployments | ✅ Yes |

## UUID Strategy

### Why UUIDs?

**Security Benefits:**
- ✅ Prevents enumeration attacks (vs sequential IDs)
- ✅ No business logic leakage
- ✅ Unpredictable - harder to guess valid IDs
- ✅ Distributed system friendly

**Performance Considerations:**
- UUID4 (Random): Maximum security, minimal performance impact
- UUID7 (Time-ordered): Better DB indexing performance
- All major vector DBs handle UUIDs efficiently

**Recommendation:** Use UUID4 for security-first applications, UUID7 for performance-critical applications.

### Performance Impact
- **Minimal**: Modern vector DBs index UUIDs efficiently
- **Trade-off**: ~16 bytes vs ~8 bytes for int64
- **Benefit**: Security > minimal storage overhead

## Usage Examples

### Basic Usage

```python
from app.services.vector_store import get_vector_store
from app.schemas.document import DocumentChunkCreate, ChunkMetadata

# Get vector store (auto-configured from settings)
async with get_vector_store() as vector_store:
    # Create chunk
    chunk = DocumentChunkCreate(
        content="Your text content here",
        metadata=ChunkMetadata(
            source="document.pdf",
            source_type="pdf",
            chunk_index=0,
            tags=["example", "demo"]
        )
    )
    
    # Generate embedding (from embedding service)
    embedding = await embedding_service.embed(chunk.content)
    
    # Insert
    chunk_id = await vector_store.insert_chunk(chunk, embedding)
    
    # Search
    results = await vector_store.search(
        query_embedding,
        SearchQuery(query="search text", top_k=5)
    )
```

### Switching Providers

**No code changes needed!** Just update your `.env`:

```bash
# Development
VECTOR_DB_PROVIDER=chroma
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=8000

# Production
VECTOR_DB_PROVIDER=qdrant
VECTOR_DB_HOST=qdrant.example.com
VECTOR_DB_API_KEY=your-key
```

### Filtered Search

```python
from app.schemas.document import SearchQuery, SecurityLevel

# Search with filters
search_query = SearchQuery(
    query="legal contracts",
    top_k=10,
    security_levels=[SecurityLevel.CONFIDENTIAL],
    organizations=["LawFirm LLC"],
    tags=["contract", "2024"],
    min_score=0.7
)

results = await vector_store.search(query_embedding, search_query)
```

### Bulk Operations

```python
# Bulk insert
chunks = [...]  # List of DocumentChunkCreate
embeddings = [...]  # List of embedding vectors

result = await vector_store.insert_chunks(chunks, embeddings)
print(f"Inserted: {result.inserted_count}")

# Bulk delete by source
await vector_store.delete_by_source("old_document.pdf")

# Bulk delete by organization
await vector_store.delete_by_organization("Deprecated Dept")
```

## Metadata Schema

### Required Fields
- `source`: Original filename/URL
- `source_type`: Document type (pdf, docx, txt, etc.)
- `chunk_index`: Position in original document

### Optional Fields
- `security_level`: Access control (public, internal, confidential, restricted, secret)
- `organization`: Owning organization/department
- `version`: Document version
- `timestamp`: When indexed (auto-generated)
- `tags`: Categorization tags
- `page_number`: Page in source document
- `section`: Section/chapter name
- `char_count`: Number of characters
- `token_count`: Estimated tokens for LLM
- `custom_metadata`: Provider-specific fields

## Security Considerations

### Access Control
Use `security_level` and `organization` fields to implement:
- Multi-tenant isolation
- Role-based access control
- Department-level separation

### Data Privacy
```python
# Filter by security clearance
search_query = SearchQuery(
    query="sensitive data",
    security_levels=[SecurityLevel.CONFIDENTIAL, SecurityLevel.PUBLIC]
)
```

### Audit Trail
Every chunk includes:
- `timestamp`: When indexed
- `source`: Origin document
- `version`: Document version

## Performance Optimization

### Batch Operations
Always use bulk insert for multiple chunks:
```python
# ❌ Slow - Multiple DB calls
for chunk in chunks:
    await vector_store.insert_chunk(chunk, embedding)

# ✅ Fast - Single DB call
await vector_store.insert_chunks(chunks, embeddings)
```

### Embedding Dimension
- Smaller = Faster search, less storage
- Larger = Better accuracy
- Common sizes: 384 (MiniLM), 768 (BERT), 1536 (OpenAI)

### Indexing Strategy
- **Development**: In-memory (Chroma)
- **Production**: Persistent with replication (Qdrant, Pinecone)

## Testing

Run the examples:
```bash
cd backend
python examples/vector_store_examples.py
```

Run tests:
```bash
pytest tests/test_vector_store.py -v
```

## Provider-Specific Notes

### ChromaDB
- **Best for**: Development, prototyping
- **Deployment**: Embedded or client/server
- **Persistence**: Optional local directory
- **Limitations**: Single-node only

### Qdrant (Upcoming)
- **Best for**: Production deployments
- **Deployment**: Docker, Kubernetes, Cloud
- **Features**: Filtering, payload indexing
- **Scalability**: Horizontal scaling

### Pinecone (Upcoming)
- **Best for**: Managed cloud solution
- **Deployment**: Fully managed
- **Features**: Auto-scaling, high availability
- **Cost**: Pay-per-use

### Weaviate (Upcoming)
- **Best for**: Hybrid search (vector + keyword)
- **Deployment**: Docker, Kubernetes, Cloud
- **Features**: GraphQL API, multi-modal
- **Unique**: Built-in vectorization

### Milvus (Upcoming)
- **Best for**: Billion-scale datasets
- **Deployment**: Kubernetes, distributed
- **Features**: GPU acceleration
- **Scalability**: Massive scale

## Extending the System

### Adding a New Provider

1. **Create implementation**:
```python
# app/services/vector_store/newdb_store.py
from app.services.vector_store.base import VectorStoreBase

class NewDBVectorStore(VectorStoreBase):
    async def initialize(self):
        # Implementation
        pass
    
    # Implement all abstract methods...
```

2. **Register in factory**:
```python
# app/services/vector_store/factory.py
class VectorStoreType(str, Enum):
    NEWDB = "newdb"

class VectorStoreFactory:
    @staticmethod
    def _create_newdb(...):
        return NewDBVectorStore(...)
```

3. **Update settings**:
```python
# app/config/vector_db_settings.py
class VectorDBProvider(str, Enum):
    NEWDB = "newdb"
```

## Best Practices

1. **Always use async context manager**:
   ```python
   async with get_vector_store() as store:
       # Operations here
   ```

2. **Validate embeddings before insert**:
   - Dimension matches configuration
   - No NaN or Inf values

3. **Use bulk operations for efficiency**

4. **Implement proper error handling**:
   ```python
   try:
       await vector_store.insert_chunk(...)
   except VectorStoreError as e:
       logger.error(f"Insert failed: {e}")
   ```

5. **Clean up old data**:
   ```python
   # Delete old versions
   await vector_store.delete_by_source("old_v1.pdf")
   ```

## Troubleshooting

### Connection Issues
```python
# Check if collection exists
exists = await vector_store.collection_exists()
if not exists:
    await vector_store.create_collection()
```

### Embedding Dimension Mismatch
```python
# Validate before insert
assert len(embedding) == vector_store.embedding_dimension
```

### Search Returns No Results
- Check filters aren't too restrictive
- Verify embeddings are normalized
- Check minimum score threshold

## Future Enhancements

- [ ] Hybrid search (vector + keyword)
- [ ] Multi-modal embeddings (text + image)
- [ ] Automatic re-indexing on schema changes
- [ ] Vector compression for storage efficiency
- [ ] Distributed vector store with sharding
- [ ] Real-time embedding updates
- [ ] Built-in caching layer

## Resources

- [ChromaDB Docs](https://docs.trychroma.com/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Pinecone Docs](https://docs.pinecone.io/)
- [Weaviate Docs](https://weaviate.io/developers/weaviate)
- [Milvus Docs](https://milvus.io/docs)

---

**Note**: This is a living document. As new providers are implemented, this README will be updated with provider-specific details and best practices.
