# File Upload System Architecture

## Overview

The File Upload system provides **complete lifecycle management** for files being ingested into the vector store. It tracks files from upload through processing, with support for approval workflows, security levels, performance monitoring, and data retention policies.

## Design Philosophy

- **Security First**: Tracks who uploaded what, when, and with what security level
- **Lifecycle Tracking**: Complete audit trail from upload → approval → processing → storage
- **Error Resilience**: Automatic retry logic with configurable max retries
- **Performance Monitoring**: Track processing time and chunk counts
- **Data Retention**: Configurable retention policies with automatic cleanup
- **Audit Ready**: Complete metadata for compliance and debugging

## Database Schema

### file_uploads Table

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
| `approved_by_id` | FK(users) | User who approved/rejected the file |
| `approval_reason` | Text | Reason for approval/rejection |
| **Department Association** |
| `department_id` | FK(departments) | Department that owns this file (nullable) |
| `is_department_only` | Boolean | If true, only dept members can access; if false, org-wide |
| **Processing Metadata** |
| `file_purpose` | Text | Why this file is being uploaded (e.g., "Q4 financial data") |
| `field_selection` | Text (JSON) | List of fields to extract from file |
| `extraction_config` | Text (JSON) | Custom extraction rules |
| **Security** |
| `security_level` | Enum | `public` \| `internal` \| `confidential` \| `restricted` |
| **Processing Status** |
| `status` | Enum | See [File Status Lifecycle](#file-status-lifecycle) |
| `is_processed` | Boolean | Whether file has been successfully processed |
| **Processing Results** |
| `chunks_created` | Integer | Number of chunks created from this file |
| `processing_error` | Text | Error message if processing failed |
| **Performance** |
| `processing_time_ms` | Integer | Time to process file (milliseconds) |
| `retry_count` | Integer | Number of retry attempts made |
| `max_retries` | Integer | Maximum retry attempts allowed (default: 3) |
| **Timestamps** |
| `created_at` | DateTime | When file was uploaded |
| `updated_at` | DateTime | Last update timestamp |
| `approved_at` | DateTime | When file was approved |
| `processing_started_at` | DateTime | When processing began |
| `processing_completed_at` | DateTime | When processing completed |
| **Data Retention** |
| `retention_until` | DateTime | Auto-delete after this date |
| `is_archived` | Boolean | Whether file is archived for long-term storage |

### Indexes for Performance

```
PRIMARY: id
UNIQUE: upload_token, file_hash
INDEXES:
  - file_name, file_type
  - status (common queries)
  - security_level (access control)
  - is_processed (processing pipeline)
  - created_at (audit trail)
  - retention_until, is_archived (cleanup jobs)

COMPOSITE:
  - (status, created_at) → Get files by status in chronological order
  - (uploaded_by_id, status) → User-specific queries
  - (retention_until, is_archived) → Data retention queries
  - (department_id, is_department_only) → Department-scoped file queries
```

## File Status Lifecycle

```
                    ┌──────────────┐
                    │   UPLOADED   │
                    │   (PENDING)  │
                    └──────┬───────┘
                           │
                    ┌──────▼──────┐
                    │  APPROVAL   │
                    │  REQUIRED   │
                    └──────┬──────┘
                           │
                 ┌─────────┴─────────┐
                 │                   │
         ┌───────▼────────┐   ┌─────▼──────┐
         │   APPROVED     │   │  REJECTED  │
         │                │   │  (FINAL)   │
         └───────┬────────┘   └────────────┘
                 │
         ┌───────▼──────────┐
         │   PROCESSING    │
         │   (IN PROGRESS) │
         └───────┬──────────┘
                 │
        ┌────────┴────────┐
        │                 │
  ┌─────▼──────┐   ┌─────▼──────┐
  │ PROCESSED  │   │  FAILED    │
  │ (SUCCESS)  │   │ (ERROR)    │
  └────────────┘   └─────┬──────┘
                        │
                ┌───────┴────────┐
                │                │
           RETRY    MAX RETRIES   (FINAL)
          POSSIBLE   EXCEEDED
```

### Status Transitions

- **PENDING**: Initial state after upload (awaiting approval)
- **APPROVED**: Admin approved file for processing
- **REJECTED**: Admin rejected file (final state)
- **PROCESSING**: Currently being ingested into vector store
- **PROCESSED**: Successfully ingested (final state)
- **FAILED**: Processing error, retry count not exceeded → reverts to PENDING
- **FAILED** (final): Max retries exceeded (final state)
- **DELETED**: Marked for deletion/cleanup

## Security Levels

| Level | Use Case | Access |
|-------|----------|--------|
| **PUBLIC** | Publicly available data | No restrictions |
| **INTERNAL** | Company internal documents | Internal users only |
| **CONFIDENTIAL** | Sensitive business data | Restricted group |
| **RESTRICTED** | Highly sensitive (PII, secrets) | Explicit approval required |

## Processing Workflow

### 1. Upload Phase
```python
file_service = FileUploadService(db_session)
file_upload = await file_service.create_file_upload(
    file_path="/path/to/document.pdf",
    file_name="document.pdf",
    file_type="pdf",
    file_size=1024000,
    uploaded_by_id=user_id,
    file_purpose="Q4 financial analysis",
    security_level=SecurityLevel.CONFIDENTIAL,
    retention_days=365  # Keep for 1 year
)
# Status: PENDING
# Event: Notification sent to admins for approval
```

### 2. Approval Phase
```python
# Admin reviews file
await file_service.approve_file(
    file_upload_id=file_upload.id,
    approved_by_id=admin_id,
    reason="Verified source"
)
# Status: APPROVED
```

### 3. Processing Phase
```python
# Background job picks up approved file
file_uploads = await file_service.get_approved_pending_processing()

for file_upload in file_uploads:
    # Start processing
    await file_service.start_processing(file_upload.id)
    # Status: PROCESSING
    
    try:
        # Ingest file
        chunks = ingest_document(file_upload.file_path)
        
        # Mark complete
        await file_service.mark_processing_complete(
            file_upload.id,
            chunks_created=len(chunks),
            processing_time_ms=elapsed_ms
        )
        # Status: PROCESSED
        
    except Exception as e:
        # Mark failed
        await file_service.mark_processing_failed(
            file_upload.id,
            error=str(e)
        )
        # Status: PENDING (if can retry) or FAILED (if max retries exceeded)
```

### 4. Retention & Cleanup Phase
```python
# Periodic cleanup job
expired = await file_service.get_expired_files()

for file_upload in expired:
    await file_service.delete_file(
        file_upload.id,
        delete_physical_file=True
    )
    # Status: DELETED
    # Physical file removed from disk
```

## Error Handling & Retries

The system implements **automatic retry logic** with configurable max retries:

```python
# Scenario 1: First failure
await file_service.mark_processing_failed(file_id, "Network timeout")
# retry_count = 1, status = PENDING (ready for retry)

# Scenario 2: Second failure
await file_service.mark_processing_failed(file_id, "Out of memory")
# retry_count = 2, status = PENDING (ready for retry)

# Scenario 3: Third failure (max_retries=3)
await file_service.mark_processing_failed(file_id, "Corrupted PDF")
# retry_count = 3, status = FAILED (no more retries)
```

Background job checks:
```python
retryable = await file_service.get_failed_retryable(limit=50)
# Returns files where: status IN (PENDING, FAILED) AND retry_count < max_retries

for file in retryable:
    # Attempt retry
    pass
```

## Duplicate Detection

Files are checked for duplicates using SHA-256 hash:

```python
# Same file uploaded twice
existing = await file_service.get_file_by_hash(
    file_hash="abc123...",
    security_level=SecurityLevel.INTERNAL
)

if existing:
    logger.warning(f"Duplicate detected: {existing.file_name}")
    # Decision: Skip or process anyway based on business logic
```

## Data Extraction Configuration

### field_selection (Simple field list)
```json
["name", "email", "phone_number"]
```

Extracts only these fields from CSV/JSON/XLSX.

### extraction_config (Advanced rules)
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

## API Usage Examples

### Create & Upload File
```python
from app.services.file_upload_service import FileUploadService

# Upload file
file_upload = await file_service.create_file_upload(
    file_path="/uploads/pending/report.pdf",
    file_name="report.pdf",
    file_type="pdf",
    file_size=2048000,
    uploaded_by_id=42,
    file_purpose="Quarterly report",
    security_level=SecurityLevel.CONFIDENTIAL
)

# Response
# FileUpload(id=1, upload_token="uuid-xyz", status=PENDING)
```

### Retrieve Pending Approvals
```python
pending = await file_service.get_pending_approvals(limit=10)

for file in pending:
    print(f"Requires approval: {file.file_name} ({file.file_size} bytes)")
    print(f"Uploaded by: User {file.uploaded_by_id}")
    print(f"Security: {file.security_level.value}")
```

### Approve File
```python
await file_service.approve_file(
    file_upload_id=1,
    approved_by_id=99,
    reason="Verified with source team"
)

# File moves to APPROVED status and processing can begin
```

### Get User's Files
```python
my_files = await file_service.get_by_user(
    user_id=42,
    status=FileStatus.PROCESSED,
    limit=20
)

for file in my_files:
    print(f"{file.file_name}: {file.chunks_created} chunks in {file.processing_time_ms}ms")
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

## Integration with Ingestion Pipeline

The FileUploadService integrates seamlessly with the existing `DocumentStorageService`:

```python
# In background job or scheduled task

# 1. Get files ready to process
approved_files = await file_service.get_approved_pending_processing()

for file_upload in approved_files:
    try:
        # 2. Start processing
        await file_service.start_processing(file_upload.id)
        
        # 3. Use existing ingestion pipeline
        storage = DocumentStorageService()
        results = storage.ingest_from_pending(
            recursive=False,
            file_types=[file_upload.file_type]
        )
        
        # 4. Update file record with results
        chunks = results[0].chunks_count if results else 0
        await file_service.mark_processing_complete(
            file_upload.id,
            chunks_created=chunks,
            processing_time_ms=elapsed_time
        )
        
    except Exception as e:
        await file_service.mark_processing_failed(
            file_upload.id,
            error=str(e)
        )
```

## Retention Policies

### Configure Retention at Upload
```python
# Keep for 30 days
file_upload = await file_service.create_file_upload(
    ...
    retention_days=30
)

# Indefinite retention (no auto-delete)
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
            delete_physical_file=True
        )
```

## Department File Association

Files can be associated with specific departments and marked as department-only or organization-wide.

### Access Control Model

```python
from app.models.file_upload import FileUpload

# Organization-wide file (accessible to everyone)
file = FileUpload(...)
file.is_department_only = False
# Any user can access if they have sufficient security clearance

# Department-only file (accessible only to department members)
file = FileUpload(...)
file.department_id = 3  # Sales department
file.is_department_only = True
# Only users in department 3 can access if they have sufficient security clearance
```

### Checking Department Access

```python
# Check if user from department can access file
can_access = file.is_department_accessible(user_department_id=3)

# User from department 3: True
# User from department 2: False
# User with no department: False
```

### Scenario 1: Organization-Wide File

```python
# Financial report accessible to entire company
file = FileUpload(
    file_name="Q4_Financial_Report.pdf",
    department_id=1,  # Finance uploaded it
    is_department_only=False,  # But everyone can access
    security_level=SecurityLevel.CONFIDENTIAL
)

# Access check
can_access = file.is_department_accessible(user_department_id=2)  # Sales user
# Result: True (if user has CONFIDENTIAL clearance)

can_access = file.is_department_accessible(user_department_id=3)  # Marketing user
# Result: True (if user has CONFIDENTIAL clearance)
```

### Scenario 2: Department-Only File

```python
# Sales internal strategic plan - only for sales team
file = FileUpload(
    file_name="Sales_Strategy_2025.pdf",
    department_id=2,  # Sales department
    is_department_only=True,  # Only Sales can access
    security_level=SecurityLevel.RESTRICTED
)

# Access check
can_access = file.is_department_accessible(user_department_id=2)  # Sales user
# Result: True (if user has RESTRICTED clearance)

can_access = file.is_department_accessible(user_department_id=1)  # Finance user
# Result: False (different department)

can_access = file.is_department_accessible(user_department_id=3)  # Marketing user
# Result: False (different department)
```

### Scenario 3: Executive Department File

```python
# Board-level financial data - only for finance department
file = FileUpload(
    file_name="Board_Package_Q4.pdf",
    department_id=1,  # Finance
    is_department_only=True,  # Finance only
    security_level=SecurityLevel.HIGHLY_CONFIDENTIAL
)

# Access check
can_access = file.is_department_accessible(user_department_id=1)  # Finance user
# Result: True (if user has HIGHLY_CONFIDENTIAL clearance)

can_access = file.is_department_accessible(user_department_id=5)  # HR user
# Result: False (different department)
```

### Helper Methods

```python
# Mark file as department-only
file.set_department_only(department_id=2)
# Sets: department_id = 2, is_department_only = True

# Make file organization-wide
file.set_organization_wide()
# Sets: is_department_only = False
# Note: department_id remains for reference but not used for access control
```

### Access Control Query

```python
from sqlalchemy import select, and_

# Get all department-only files
dept_files = select(FileUpload).where(FileUpload.is_department_only == True)

# Get all organization-wide files
org_files = select(FileUpload).where(FileUpload.is_department_only == False)

# Get department-only files for specific department
sales_files = select(FileUpload).where(
    and_(
        FileUpload.department_id == 2,
        FileUpload.is_department_only == True
    )
)
```

### Full Access Control Logic

```python
async def can_user_access_file(user: User, file: FileUpload) -> bool:
    """
    Check if user can access file considering:
    1. Department membership and file scope
    2. User permission level vs file security level
    3. Permission overrides
    """
    # Check department access
    if not file.is_department_accessible(user.department_id):
        return False  # User is not in required department
    
    # Check security clearance
    if not user.permission:
        return False
    
    effective_level = user.permission.get_effective_permission()
    
    # Map SecurityLevel to PermissionLevel for comparison
    file_requires_level = {
        SecurityLevel.GENERAL: PermissionLevel.GENERAL,
        SecurityLevel.RESTRICTED: PermissionLevel.RESTRICTED,
        SecurityLevel.CONFIDENTIAL: PermissionLevel.CONFIDENTIAL,
        SecurityLevel.HIGHLY_CONFIDENTIAL: PermissionLevel.HIGHLY_CONFIDENTIAL,
    }[file.security_level]
    
    return effective_level >= file_requires_level
```

## Security Considerations

1. **File Hash Verification**: All files are hashed (SHA-256) for:
   - Duplicate detection
   - Integrity verification
   - Audit trail

2. **User Tracking**: Every file action is tracked:
   - Who uploaded it
   - Who approved it
   - When and why

3. **Approval Workflow**: Files cannot be processed without explicit approval

4. **Security Levels**: Different files can have different access restrictions

5. **Audit Trail**: Complete history of file lifecycle in database

## Performance Characteristics

### Query Performance
- `get_pending_approvals()`: O(1) with indexed status
- `get_by_user()`: O(1) with composite index on (user_id, status)
- `get_failed_retryable()`: O(1) with indexed retry_count
- `get_expired_files()`: O(1) with indexed retention_until

### Storage Efficiency
- SHA-256 hashes: 32 bytes per file
- Average file record: ~2KB
- Scales to millions of files efficiently

## Future Enhancements

- [ ] File virus scanning before ingestion
- [ ] Encryption at rest for sensitive files
- [ ] Audit log export
- [ ] Batch approval operations
- [ ] File versioning
- [ ] Advanced retry strategies (exponential backoff)
- [ ] Integration with document signing
- [ ] Automated metadata extraction
