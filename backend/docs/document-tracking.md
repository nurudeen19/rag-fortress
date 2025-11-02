# Document Tracking System

## Overview

The document tracking system prevents duplicate processing of documents by maintaining a record of what has been ingested.

## How It Works

### 1. **File Hash Tracking**
- Each document's content is hashed (SHA256)
- Hash is stored when document is processed
- On subsequent runs, content is compared

### 2. **Smart Processing Logic**

A document is processed if:
- ✅ It's **never been processed** before
- ✅ Its **content has changed** (different hash)
- ✅ Previous processing **failed** (allows retry)

A document is skipped if:
- ⏭️ Already processed **successfully** and **unchanged**

### 3. **Tracking Data**

Stored in: `data/ingestion_tracker.json`

Each tracked document includes:
```json
{
  "document.pdf": {
    "file_path": "document.pdf",
    "file_hash": "sha256_hash_here",
    "file_size": 12345,
    "status": "success",
    "chunks_count": 42,
    "last_processed": "2025-11-02T10:30:00",
    "error_message": null
  }
}
```

## Usage

### Automatic Tracking (Default)

```python
from app.services.document_ingestion import DocumentIngestionService

async with DocumentIngestionService() as ingestion:
    # Automatically skips already processed documents
    results = await ingestion.ingest_from_knowledge_base()
```

### Force Reprocessing

```python
# Force reprocess ALL documents
results = await ingestion.ingest_from_knowledge_base(force=True)

# Force reprocess specific document
ingestion.force_reprocess_document("document.pdf")
result = await ingestion.ingest_document("document.pdf", force=True)
```

### Disable Tracking

```python
# Disable automatic skipping (process everything)
ingestion = DocumentIngestionService(skip_processed=False)
```

### Management Operations

```python
# Get statistics
stats = ingestion.get_tracking_stats()
# Returns: {total_documents, successful, failed, total_chunks}

# Clear failed documents (allows retry)
cleared = ingestion.clear_failed_documents()

# Reset all tracking (WARNING: causes full reprocessing)
ingestion.reset_tracking()
```

## Benefits

### 💰 **Cost Savings**
- Avoid re-embedding unchanged documents
- Significant savings with API-based embeddings (OpenAI, Cohere, etc.)

### ⚡ **Performance**
- Skip processing of unchanged documents
- Faster ingestion runs
- Only process what's new or changed

### 🔄 **Smart Updates**
- Automatically detect content changes
- Update only modified documents
- Preserve embeddings for unchanged content

### 🛡️ **Reliability**
- Track failures for retry
- Clear separation of success vs failure
- Easy failure recovery

## Use Cases

### 1. Continuous Sync
```python
# Run regularly (cron, scheduler, etc.)
# Only new/changed documents are processed
async with DocumentIngestionService() as ingestion:
    results = await ingestion.ingest_from_knowledge_base()
```

### 2. Content Updates
```python
# User updates document.pdf
# System detects change and reprocesses automatically
result = await ingestion.ingest_document("document.pdf")
```

### 3. Failure Recovery
```python
# Clear failed documents and retry
ingestion.clear_failed_documents()
results = await ingestion.ingest_from_knowledge_base()
```

### 4. Fresh Start
```python
# Reset everything and start over
ingestion.reset_tracking()
results = await ingestion.ingest_from_knowledge_base()
```

## Example Output

```
[Tracking Stats Before Ingestion]
Total tracked documents: 10
Successfully processed: 8
Failed: 2
Total chunks: 420

[Ingesting all documents from knowledge base...]
Total documents found: 12
Newly processed: 2
Skipped (already processed): 8
Failed: 0
New chunks created: 84

Details:
  ✓ new_document.pdf: 42 chunks
  ✓ updated_file.txt: 42 chunks
  ⏭️ old_document.pdf: Skipped - already processed and unchanged
  ...
```

## Tracking File Location

- **File**: `data/ingestion_tracker.json`
- **Format**: JSON
- **Persistence**: Survives application restarts
- **Backup**: Recommended to include in backups

## Best Practices

1. **Don't Delete Tracking File** - Unless you want full reprocessing
2. **Backup Regularly** - Along with vector store data
3. **Monitor Failed Documents** - Clear and retry periodically
4. **Use `force=True` Sparingly** - Only when necessary (wastes resources)
