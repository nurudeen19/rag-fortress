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
   - Provider: ChromaDB (extensible)
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
| **RESTRICTED** | Highly sensitive (PII, secrets) | Explicit approval required |

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

### Folder-Based Ingestion

Quick workflow for processing files from a pending folder:

```bash
# Add documents to pending folder
cp my-document.pdf data/knowledge_base/pending/
```

```python
async with DocumentIngestionService() as ingestion:
    results = await ingestion.ingest_from_pending()
    
    for result in results:
        if result.success:
            print(f"✓ {result.document_path}: {result.chunks_count} chunks")
        else:
            print(f"✗ {result.document_path}: {result.error_message}")
```

Successfully processed files automatically move to `processed/` folder.

## Configuration

### Environment Variables

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
# Check if user's department can access file
can_access = file.is_department_accessible(user_department_id=3)

# Full access control check
async def can_user_access_file(user: User, file: FileUpload) -> bool:
    # 1. Check department membership
    if not file.is_department_accessible(user.department_id):
        return False  # User not in required department
    
    # 2. Check security clearance
    if not user.permission:
        return False
    
    effective_level = user.permission.get_effective_permission()
    
    # 3. Compare security levels
    file_requires_level = map_security_to_permission(file.security_level)
    return effective_level >= file_requires_level
```

### Scenarios

**Scenario 1: Organization-Wide File**
```python
# Financial report accessible to entire company
file = FileUpload(
    file_name="Q4_Financial_Report.pdf",
    department_id=1,  # Finance uploaded it
    is_department_only=False,  # Everyone can access
    security_level=SecurityLevel.CONFIDENTIAL
)

# Accessible to any user with CONFIDENTIAL clearance
```

**Scenario 2: Department-Only File**
```python
# Sales strategy - only for sales team
file = FileUpload(
    file_name="Sales_Strategy_2025.pdf",
    department_id=2,  # Sales department
    is_department_only=True,  # Only Sales can access
    security_level=SecurityLevel.RESTRICTED
)

# Only accessible to Sales users with RESTRICTED clearance
```

## File Tracking and Status Management

### Retrieve Files

```python
# Get pending approvals
pending = await file_service.get_pending_approvals(limit=10)

# Get user's files
my_files = await file_service.get_by_user(
    user_id=42,
    status=FileStatus.PROCESSED,
    limit=20
)

# Get files by security level
confidential = await file_service.get_by_security_level(
    SecurityLevel.CONFIDENTIAL
)

# Get department files
dept_files = await file_service.get_by_department(department_id=2)
```

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

## Error Handling and Retry Logic

### Automatic Retries

```python
# First failure: retry_count = 1, status = PENDING
await file_service.mark_processing_failed(file_id, "Network timeout")

# Second failure: retry_count = 2, status = PENDING
await file_service.mark_processing_failed(file_id, "Out of memory")

# Third failure (max_retries=3): status = FAILED (final)
await file_service.mark_processing_failed(file_id, "Corrupted PDF")
```

### Get Retryable Files

```python
retryable = await file_service.get_failed_retryable(limit=50)
# Returns files where: retry_count < max_retries

for file in retryable:
    # Retry processing
    await process_file(file)
```

## Reprocessing Documents

### Using API

```python
# Move file back to pending for reprocessing
ingestion.reprocess_document("my-document.pdf")
# Moves from processed/ back to pending/
```

### Manually

```bash
# Move from processed back to pending
mv data/knowledge_base/processed/my-document.pdf data/knowledge_base/pending/

# Then run ingestion again
python -c "
from app.services.document_ingestion import DocumentIngestionService
import asyncio

async def reprocess():
    async with DocumentIngestionService() as ing:
        await ing.ingest_from_pending()

asyncio.run(reprocess())
"
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

### Cleanup Task

```python
async def cleanup_expired_files():
    """Periodic task to delete expired files."""
    expired = await file_service.get_expired_files(limit=100)
    
    for file_upload in expired:
        await file_service.delete_file(
            file_upload.id,
            delete_physical_file=True  # Remove from disk
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

## Performance Characteristics

### Query Performance
- `get_pending_approvals()`: O(1) with indexed status
- `get_by_user()`: O(1) with composite index
- `get_expired_files()`: O(1) with indexed retention_until

### Storage Efficiency
- SHA-256 hashes: 32 bytes per file
- Average file record: ~2KB
- Scales to millions of files

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

### Want to reprocess everything
```bash
# Move all from processed back to pending
mv data/knowledge_base/processed/* data/knowledge_base/pending/

# Optionally clear vector database
# Then run ingestion again
```

## Security Considerations

1. **File Hash Verification** - SHA-256 for duplicate detection and integrity
2. **User Tracking** - Complete audit trail of who uploaded/approved
3. **Approval Workflow** - Files require explicit approval before processing
4. **Security Levels** - Different access restrictions per file
5. **Department Isolation** - Department-only files for sensitive data

## File Structure

```
app/services/
├── document_loader.py         # Load documents
├── chunking.py                # Type-aware chunking
├── embedding.py               # Generate embeddings
├── document_ingestion.py      # Orchestrate pipeline
├── file_upload_service.py     # File lifecycle management
└── vector_store/
    ├── base.py               # VectorStore interface
    └── chroma.py             # ChromaDB implementation

examples/
├── simple_ingestion.py        # Complete example
└── file_upload_examples.py    # Upload workflow examples

data/knowledge_base/
├── pending/                   # Drop files here
└── processed/                 # Successfully processed files
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

**Status:** ✅ Production Ready
