# Document Ingestion Pipeline

Simple, focused pipeline for ingesting documents into a vector database.

## Architecture

```
Document → Load → Chunk → Embed → Store → Success/Failure
```

### Pipeline Steps

1. **Document Loader** - Load documents from various formats
   - Supported: TXT, PDF, DOCX, MD, JSON, CSV, XLSX, PPTX
   - Location: `app/services/document_loader.py`

2. **Chunking** - Type-aware document chunking
   - Text documents: Character-based with overlap
   - JSON: Field/object-based chunking
   - CSV/XLSX: Row-based with header context
   - Location: `app/services/chunking.py`

3. **Embedding** - Generate embeddings for chunks
   - Providers: HuggingFace, OpenAI, Cohere
   - Location: `app/services/embedding.py`

4. **Vector Store** - Store chunks with embeddings
   - Provider: ChromaDB (extendable)
   - Location: `app/services/vector_store/`

5. **Orchestrator** - Coordinates the entire pipeline
   - Location: `app/services/document_ingestion.py`

## Quick Start

### Single Document

```python
from app.services.document_ingestion import DocumentIngestionService

async with DocumentIngestionService() as ingestion:
    result = await ingestion.ingest_document(
        file_path="path/to/document.pdf",
        metadata={"organization": "my-org"}
    )
    print(result)  # IngestionResult(✓ document.pdf: 42 chunks)
```

### Directory of Documents

```python
async with DocumentIngestionService() as ingestion:
    results = await ingestion.ingest_directory(
        directory_path="data/documents",
        recursive=True,
        metadata={"batch": "initial-load"}
    )
    
    for result in results:
        print(result)
```

## Configuration

Configure via environment variables (`.env`):

```env
# Embedding Provider
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Vector Store
VECTOR_DB_PROVIDER=chroma
VECTOR_DB_COLLECTION_NAME=documents
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=8000
```

## Components

### DocumentLoader
- **Purpose**: Load documents from files
- **Supported Types**: 8 file formats
- **Output**: Document(content, doc_type, metadata, source)

### DocumentChunker
- **Purpose**: Chunk documents intelligently
- **Strategies**:
  - Text: Character-based with sentence/word boundaries
  - JSON: Per-field or per-object
  - CSV/XLSX: Per-row with headers
- **Output**: List[Chunk(content, metadata, chunk_index)]

### EmbeddingProvider
- **Purpose**: Generate vector embeddings
- **Providers**:
  - HuggingFace: Local sentence-transformers
  - OpenAI: API-based embeddings
  - Cohere: API-based embeddings
- **Output**: List[List[float]]

### VectorStoreBase
- **Purpose**: Store chunks with embeddings
- **Interface**:
  - `initialize()` - Setup connection
  - `insert_chunks()` - Store data
  - `close()` - Cleanup
- **Implementation**: ChromaDB (others can be added)

### DocumentIngestionService
- **Purpose**: Orchestrate the complete pipeline
- **Methods**:
  - `ingest_document()` - Single document
  - `ingest_directory()` - Multiple documents
- **Returns**: IngestionResult with success/failure

## Example

See `examples/simple_ingestion.py` for a complete working example.

```bash
python examples/simple_ingestion.py
```

## Design Philosophy

- **Simple**: Focus on core ingestion pipeline only
- **Type-aware**: Different chunking for different document types
- **Modular**: Each component is independent
- **Async**: Built for concurrent processing
- **Extensible**: Easy to add new providers

## Future Enhancements

- Search/retrieval functionality
- Update/delete operations
- More vector store providers (Pinecone, Weaviate, etc.)
- More embedding providers
- Batch processing optimization
- Metadata filtering
