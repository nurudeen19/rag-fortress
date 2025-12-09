# Document Management Guide

Complete guide to document upload, processing, and lifecycle management in RAG-Fortress.

## Overview

The document management system provides end-to-end handling of files from upload through vector storage, with:
- Complete lifecycle tracking (upload → approval → processing → storage)
- Department-based access control
- Security levels and metadata
- Status monitoring and error handling
- Automatic retry logic
- Data retention policies

## Architecture

### Document Flow

```
1. Upload → 2. Approval → 3. Processing → 4. Storage → 5. Retrieval
    ↓           ↓              ↓              ↓            ↓
 Track      Validate       Ingest         Vector DB    Query/Use
```

### Processing Pipeline

```
Document File
    ↓
1. LOAD (DocumentLoader)
   - Support: TXT, PDF, DOCX, MD, JSON, CSV, XLSX
   - Output: Document(content, doc_type, metadata, source)
    ↓
2. CHUNK (DocumentChunker)
   - Text: Character-based with overlap
   - JSON: Field/object-based
   - CSV/XLSX: Row-based with headers
   - Output: List[Chunk(content, metadata, chunk_index)]
    ↓
3. EMBED (EmbeddingProvider)
   - Providers: HuggingFace, OpenAI, Cohere
   - Output: List[List[float]] (embeddings)
    ↓
4. STORE (VectorStore)
   - Provider: Qdrant, Pinecone, ChromaDB
   - Output: Stored chunks with embeddings
    ↓
SUCCESS/FAILURE (tracked in database)
```

## File Upload System

### Database Schema

The `file_uploads` table tracks complete file lifecycle:

| Field | Type | Purpose |
|-------|------|---------|
| **Core Identifiers** |
| `id` | PK | Unique record ID |
| `upload_token` | Unique String | Unique token for API access (UUID) |
| **File Information** |
| `file_name` | String(500) | Original file name |
| `file_type` | String(50) | File extension (pdf, txt, csv, json, xlsx, docx, md, pptx) |
| `file_size` | Integer | File size in bytes |
| `file_path` | String(1000) | Full path to file on disk |
| `file_hash` | String(255) | SHA-256 hash for deduplication |
| **User Tracking** |
| `uploaded_by_id` | FK(users) | User who uploaded the file |
| `approved_by_id` | FK(users) | User who approved/rejected |
| `approval_reason` | Text | Reason for approval/rejection |
| **Department Association** |
| `department_id` | FK(departments) | Department that owns this file (nullable) |
| `is_department_only` | Boolean | If true, only dept members can access |
| **Processing Metadata** |
| `file_purpose` | Text | Why this file is being uploaded |
| `field_selection` | Text (JSON) | List of fields to extract |
| `extraction_config` | Text (JSON) | Custom extraction rules |
| **Security** |
| `security_level` | Enum | `public` \| `internal` \| `confidential` \| `restricted` |
| **Processing Status** |
| `status` | Enum | See File Status Lifecycle |
| `is_processed` | Boolean | Whether successfully processed |
| `chunks_created` | Integer | Number of chunks created |
| `processing_error` | Text | Error message if failed |
| **Performance** |
| `processing_time_ms` | Integer | Processing time (milliseconds) |
| `retry_count` | Integer | Number of retry attempts |
| `max_retries` | Integer | Maximum retries allowed (default: 3) |
| **Timestamps** |
| `created_at` | DateTime | When file was uploaded |
| `updated_at` | DateTime | Last update |
| `approved_at` | DateTime | When file was approved |
| `processing_started_at` | DateTime | When processing began |
| `processing_completed_at` | DateTime | When processing completed |
| **Data Retention** |
| `retention_until` | DateTime | Auto-delete after this date |
| `is_archived` | Boolean | Whether archived for long-term storage |

### File Status Lifecycle

```
UPLOADED (PENDING)
    ↓
APPROVAL REQUIRED
    ↓
    ├─→ APPROVED ──→ PROCESSING ──┬─→ PROCESSED (SUCCESS)
    │                              └─→ FAILED (→ PENDING if retries remain)
    │                                           └─→ FAILED (final if max retries)
    └─→ REJECTED (FINAL)
```

### Security Levels

| Level | Use Case | Access |
|-------|----------|--------|
| **PUBLIC** | Publicly available data | No restrictions |
| **INTERNAL** | Company internal documents | Internal users only |
| **CONFIDENTIAL** | Sensitive business data | Restricted group |
| **RESTRICTED** | Highly sensitive | Explicit approval required |

## Upload Workflow

### 1. Upload File

```python
from app.services.file_upload_service import FileUploadService

file_service = FileUploadService(db_session)

file_upload = await file_service.create_file_upload(
    file_path="/uploads/pending/report.pdf",
    file_name="report.pdf",
    file_type="pdf",
    file_size=2048000,
    uploaded_by_id=42,
    file_purpose="Quarterly financial report",
    security_level=SecurityLevel.CONFIDENTIAL,
    department_id=1,  # Finance department
    is_department_only=True,  # Only finance can access
    retention_days=365  # Keep for 1 year
)
# Status: PENDING
```

### 2. Approve File

```python
await file_service.approve_file(
    file_upload_id=file_upload.id,
    approved_by_id=admin_id,
    reason="Verified with source team"
)
# Status: APPROVED
```

### 3. Process File

Background job processes approved files:

```python
async def process_approved_files():
    """Background job to process approved files."""
    file_service = FileUploadService(session)
    
    # Get files ready to process
    approved_files = await file_service.get_approved_pending_processing()
    
    for file_upload in approved_files:
        try:
            # Start processing
            await file_service.start_processing(file_upload.id)
            
            # Use ingestion pipeline
            async with DocumentIngestionService() as ingestion:
                result = await ingestion.ingest_document(
                    file_path=file_upload.file_path,
                    metadata={
                        "file_id": file_upload.id,
                        "security_level": file_upload.security_level.value,
                        "department_id": file_upload.department_id
                    }
                )
            
            # Mark complete
            await file_service.mark_processing_complete(
                file_upload.id,
                chunks_created=result.chunks_count,
                processing_time_ms=elapsed_ms
            )
            # Status: PROCESSED
            
        except Exception as e:
            # Mark failed (will retry if possible)
            await file_service.mark_processing_failed(
                file_upload.id,
                error=str(e)
            )
            # Status: PENDING (if retries remain) or FAILED (if max exceeded)
```

## Document Ingestion Pipeline

### Single Document

```python
from app.services.document_ingestion import DocumentIngestionService

async with DocumentIngestionService() as ingestion:
    result = await ingestion.ingest_document(
        file_path="path/to/document.pdf",
        metadata={
            "organization": "my-org",
            "security_level": "confidential"
        }
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
        if result.success:
            print(f"✓ {result.document_path}: {result.chunks_count} chunks")
        else:
            print(f"✗ {result.document_path}: {result.error_message}")
```


## Configuration

### Environment Variables

```env
# Embedding Provider
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Vector Store
VECTOR_DB_PROVIDER=chroma
VECTOR_DB_COLLECTION_NAME=documents
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=8000
```

## Department-Based Access Control

Files can be associated with departments and marked as department-only or organization-wide.

### Access Control Model

```python
# Organization-wide file (accessible to everyone with clearance)
file = FileUpload(...)
file.is_department_only = False
# Any user can access if they have sufficient security clearance

# Department-only file (accessible only to department members)
file = FileUpload(...)
file.department_id = 3  # Sales department
file.is_department_only = True
# Only users in department 3 can access (with sufficient clearance)
```

### Checking Access

```python

Important: `get_user_clearance_cache` only returns user clearance information clearance cache is used to fetch the user's effective clearance (including overrides) and that information is then passed to the vector-store retriever or permission/service layer which enforces access to documents or other resources.

Example — retrieval flow (preferred):


from app.utils.user_clearance_cache import get_user_clearance_cache
from app.services.vector_store.retriever import get_retriever_service

async def retrieve_user_context(user: User, query_text: str, session):
    # 1) Get a cache instance and fetch clearance for the user
    clearance_cache = get_user_clearance_cache(session)
    clearance = await clearance_cache.get_clearance(user.id)
    if not clearance:
        # handle missing user / deny
        return {"success": False, "error": "user_not_found"}

    # 2) Pass numeric clearance and department info to the retriever
    retriever = get_retriever_service()
    retrieval_result = await retriever.query(
        query_text=query_text,
        user_security_level=clearance["org_clearance_value"],
        user_department_id=clearance.get("department_id"),
        user_department_security_level=clearance.get("dept_clearance_value"),
        user_id=user.id
    )

    # 3) The retriever enforces document-level filtering and returns only accessible context
    return retrieval_result
```

### Scenarios

**Organization-wide document (plain language flow)**

- An organization-wide document is uploaded with a security level (for example, CONFIDENTIAL) and marked as not `is_department_only`.
- When a user requests context related to that document, the service first obtains the user's effective clearance (including overrides) using `get_user_clearance_cache(...)`.
- The service converts the clearance to the numeric values the retriever expects and calls the vector-store retriever, supplying `user_security_level`, optional `user_department_id`, `user_department_security_level`, and `user_id`.
- The retriever applies document-level filters: it compares the numeric clearance thresholds against each stored chunk's required clearance and removes any chunks the user is not allowed to see.
- If the retriever returns one or more contexts, those are returned to the user; if it returns no contexts the service responds with an `insufficient_clearance` message informing the user they don't have the required clearance.

**Department-only document (plain language flow)**

- A department-only document is associated with a owning `department_id` and marked `is_department_only=True` in its metadata.
- On a retrieval request the service first fetches the user's effective clearance via `get_user_clearance_cache(...)`. The clearance also contains the user's department affiliation and role flags (for example, `is_department_manager`).
- Before calling the retriever many services perform a quick department-membership check: if the document is department-only and the user is not a member of the owning department (and not a department manager) the service will return an `insufficient_department_membership` response immediately.
- If the user passes the membership check, the service calls the retriever with the user's numeric clearance and department information. The retriever further filters returned contexts by numeric clearance and department scope.
- If the retriever yields no accessible contexts, the service returns an `insufficient_clearance` message explaining the user lacks the necessary clearance within that department.

These plain-language scenarios match the code-level example shown earlier in the "Checking Access" section: the cache fetches clearance, the service passes numeric values to the retriever, and the retriever enforces access, returning only permitted contexts.

## File Tracking and Status Management



### Statistics

```python
stats = await file_service.get_statistics()

# {
#   "total_files": 145,
#   "by_status": {
#       "pending": 5,
#       "approved": 3,
#       "processing": 1,
#       "processed": 130,
#       "failed": 6
#   },
#   "pending_approvals": 5,
#   "processed": 130,
#   "failed": 6
# }
```


## Duplicate Detection

Files are checked for duplicates using SHA-256 hash:

```python
# Check for existing file with same hash
existing = await file_service.get_file_by_hash(
    file_hash="abc123...",
    security_level=SecurityLevel.INTERNAL
)

if existing:
    logger.warning(f"Duplicate detected: {existing.file_name}")
    # Decision: Skip or process anyway based on business logic
```

## Data Extraction Configuration

### Simple Field Selection

```json
["name", "email", "phone_number"]
```

Extracts only these fields from CSV/JSON/XLSX.

### Advanced Extraction Rules

```json
{
  "strategy": "field-based",
  "fields": {
    "customer_name": {
      "source_column": "Name",
      "type": "string",
      "required": true
    },
    "contact_email": {
      "source_column": "Email",
      "type": "email",
      "required": false
    }
  }
}
```

## Data Retention and Cleanup

### Configure Retention

```python
# Keep for 30 days
file_upload = await file_service.create_file_upload(
    ...
    retention_days=30
)

# Indefinite retention
file_upload = await file_service.create_file_upload(
    ...
    retention_days=None
)
```


## Supported File Types

| Type | Extensions | Chunking Strategy |
|------|-----------|-------------------|
| Text | .txt, .md | Character-based with overlap |
| PDF | .pdf | Character-based with overlap |
| Office | .docx, .xlsx, .pptx | Type-specific |
| Data | .json, .csv | Field/row-based |

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
  - `ingest_from_pending()` - Folder-based workflow
- **Returns**: IngestionResult with success/failure


## Troubleshooting

### No documents found
```bash
# Check pending directory
ls data/knowledge_base/pending/

# Add test document
echo "Test content" > data/knowledge_base/pending/test.txt
```

### Document failed to process
- Check error message in file upload record
- Verify file is not corrupted
- Ensure file type is supported
- Document will remain in pending for retry


## Security Considerations

1. **File Hash Verification** - SHA-256 for duplicate detection and integrity
2. **User Tracking** - Complete audit trail of who uploaded/approved
3. **Approval Workflow** - Files require explicit approval before processing
4. **Security Levels** - Different access restrictions per file
5. **Department Isolation** - Department-only files for sensitive data

## File Structure

```
app/services/
├── document_ingestion.py        # DocumentIngestionService — orchestrator for ingestion & retrieval workflows
├── file_upload_service.py       # File lifecycle management (create/approve/process)
└── vector_store/
    ├── loader.py               # DocumentLoader implementations (PDF, DOCX, CSV, JSON, etc.)
    ├── chunker.py              # DocumentChunker and chunking strategies
    ├── storage.py              # Vector store adapters (Chroma/Qdrant/etc.)
    ├── retriever.py            # Retriever service (applies clearance filters and returns contexts)
    └── reranker.py             # Optional re-ranking / scoring logic

examples/
├── simple_ingestion.py         # Example using DocumentIngestionService
└── file_upload_examples.py     # Upload workflow examples

data/
├── files/                      # Sample source files and fixtures
├── uploads/                    # Uploaded/staging files
└── knowledge_base/             # Processed knowledge (chunks, embeddings, indexes)
```

## Future Enhancements

- [ ] File virus scanning before ingestion
- [ ] Encryption at rest for sensitive files
- [ ] File versioning support
- [ ] Batch approval operations
- [ ] Advanced retry strategies (exponential backoff)
- [ ] More vector store providers (Pinecone, Weaviate)
- [ ] Update/delete operations for stored documents
- [ ] Automated metadata extraction

---
