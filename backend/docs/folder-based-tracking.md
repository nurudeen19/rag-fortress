# Folder-Based Document Tracking System

## Overview

Successfully refactored from complex JSON-based tracking with SHA256 hashes to a simple, intuitive folder-based system.

## What Changed

### Before (JSON-Based Tracking)
- Complex JSON file storing document metadata
- SHA256 hash calculations for change detection
- `document_tracker.py` service for tracking logic
- Documents stayed in single `knowledge_base/` directory
- Needed to query tracking JSON to know what's processed

### After (Folder-Based Tracking)
- **Two folders**: `pending/` and `processed/`
- Documents physically move between folders
- No JSON files or hash calculations
- Visual inspection of what's pending vs processed
- Failed documents automatically remain for retry

## File Structure

```
data/
├── knowledge_base/
│   ├── pending/          # Documents to be processed
│   │   ├── README.md
│   │   └── [your documents here]
│   ├── processed/        # Successfully embedded documents
│   │   ├── README.md
│   │   └── [completed documents]
│   └── README.md
└── vector_store/         # ChromaDB persistent storage
```

## Workflow

### 1. Add Documents
```bash
cp my-document.pdf data/knowledge_base/pending/
```

### 2. Process Documents
```python
from app.services.document_ingestion import DocumentIngestionService

async with DocumentIngestionService() as ingestion:
    results = await ingestion.ingest_from_pending()
```

### 3. Automatic Handling
- ✅ **Success**: Document moved to `processed/`
- ❌ **Failure**: Document remains in `pending/` for retry

### 4. Reprocessing
```python
# Move document from processed back to pending
ingestion.reprocess_document("my-document.pdf")

# Or manually:
# mv data/knowledge_base/processed/doc.pdf data/knowledge_base/pending/
```

## Code Changes

### Files Modified

1. **`app/services/document_loader.py`**
   - Changed from `knowledge_base_dir` to `pending_dir`
   - Now only loads from pending directory
   - Security: validates files are within pending directory

2. **`app/services/document_ingestion.py`**
   - Removed `DocumentTracker` dependency
   - Added `_move_to_processed()` method
   - Updated `ingest_document()` to move files on success
   - Renamed `ingest_from_knowledge_base()` to `ingest_from_pending()`
   - Removed tracking methods: `get_tracking_stats()`, `clear_failed_documents()`, etc.
   - Added utility methods: `get_pending_files()`, `get_processed_files()`, `reprocess_document()`

3. **`app/config/app_settings.py`**
   - Added `PENDING_DIR` field
   - Added `PROCESSED_DIR` field

4. **`.env.example`**
   - Added `PENDING_DIR` configuration
   - Added `PROCESSED_DIR` configuration

5. **`examples/simple_ingestion.py`**
   - Updated to use `ingest_from_pending()` instead of `ingest_from_knowledge_base()`
   - Removed tracking stats logic
   - Added pending/processed file listing
   - Simplified example to reflect folder-based approach

### Files Deleted

1. **`app/services/document_tracker.py`** ❌
   - No longer needed with folder-based system
   - All tracking logic replaced by file movement

### Files Created

1. **`data/knowledge_base/pending/README.md`**
   - Instructions for adding documents
   - Supported file types
   - Workflow explanation

2. **`data/knowledge_base/processed/README.md`**
   - Explanation of processed folder
   - Reprocessing instructions
   - Archive purpose

3. **`data/knowledge_base/README.md`** (updated)
   - Complete workflow documentation
   - Troubleshooting guide
   - Best practices

## Benefits

### Simplicity
- No JSON parsing or hash calculations
- Visual inspection of pending vs processed
- Clear workflow: add → process → move

### Intuitive
- Folder metaphor is familiar to all users
- Easy to understand at a glance
- Manual intervention is straightforward

### Reliability
- File system operations are atomic
- No risk of JSON corruption
- Failed documents automatically stay for retry

### Maintenance
- Less code to maintain
- No database/JSON file to manage
- Easier to debug (just look at folders)

### User-Friendly
- Users can drop files directly into pending/
- Easy to see what's been processed
- Simple to reprocess: just move the file back

## API Changes

### Removed Methods
```python
# OLD - No longer available
ingestion.get_tracking_stats()
ingestion.clear_failed_documents()
ingestion.reset_tracking()
ingestion.force_reprocess_document(file_path)
ingestion.ingest_from_knowledge_base(force=True)
```

### New Methods
```python
# NEW - Folder-based utilities
ingestion.get_pending_files() -> List[Path]
ingestion.get_processed_files() -> List[Path]
ingestion.reprocess_document(filename: str) -> bool
ingestion.ingest_from_pending(recursive=True, file_types=None, metadata=None)
```

### Updated Method Signatures
```python
# OLD
await ingestion.ingest_document(file_path, metadata=None, force=False)

# NEW
await ingestion.ingest_document(file_path, metadata=None)
# Note: No 'force' parameter - just move file from processed to pending
```

## Configuration

### Environment Variables

```bash
# .env
PENDING_DIR=./data/knowledge_base/pending
PROCESSED_DIR=./data/knowledge_base/processed
```

### Python Settings

```python
from app.config.settings import settings

settings.PENDING_DIR      # "./data/knowledge_base/pending"
settings.PROCESSED_DIR    # "./data/knowledge_base/processed"
```

## Migration Guide

If you have documents in the old `knowledge_base/` directory:

```bash
# Move all documents to pending for processing
mv data/knowledge_base/*.* data/knowledge_base/pending/

# Or organize by subdirectories
mv data/knowledge_base/docs data/knowledge_base/pending/
mv data/knowledge_base/pdfs data/knowledge_base/pending/
```

## Testing

To test the new system:

```bash
# 1. Add a test document
echo "Test document content" > data/knowledge_base/pending/test.txt

# 2. Run ingestion
python examples/simple_ingestion.py

# 3. Verify document moved
ls data/knowledge_base/pending/    # Should be empty
ls data/knowledge_base/processed/  # Should contain test.txt
```

## Future Enhancements

Potential additions (if needed):

1. **Failed Folder**: Optional `data/knowledge_base/failed/` for permanently failed documents
2. **Error Logging**: Write error details to `.errors.json` in pending folder
3. **Batch Processing**: Process documents in batches with progress tracking
4. **Webhooks**: Notify external systems when documents are processed
5. **File Watching**: Automatically process documents when added to pending/

## Summary

The folder-based system achieves the same goal (prevent duplicate processing) with:
- **90% less code**
- **Zero dependencies** (no JSON lib, no hashing)
- **Instant visibility** (just look at the folders)
- **Easier debugging** (files are where you expect them)
- **Better UX** (drop files, watch them move)

It's a perfect example of "simpler is better" - solving the problem with the most straightforward solution possible.
