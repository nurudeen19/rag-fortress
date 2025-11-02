# Knowledge Base Directory

This directory manages document ingestion for the RAG system using a simple folder-based workflow.

## Directory Structure

```
knowledge_base/
├── pending/          # Documents waiting to be processed
│   └── README.md     # Instructions for adding documents
├── processed/        # Successfully processed documents
│   └── README.md     # Archive of processed documents
└── README.md         # This file
```

## Simple Workflow

The system uses a straightforward folder-based approach:

### 1. Add Documents (pending/)
Place any documents you want to process in the `pending/` directory:

```bash
cp my-document.pdf data/knowledge_base/pending/
```

### 2. Run Ingestion
Process all pending documents:

```python
from app.services.document_ingestion import DocumentIngestionService

async with DocumentIngestionService() as ingestion:
    results = await ingestion.ingest_from_pending()
    
for result in results:
    print(result)
```

### 3. Automatic Processing
- ✅ **Success**: Document is moved to `processed/`
- ❌ **Failure**: Document remains in `pending/` for retry

### 4. Results
Successfully processed documents are embedded in the vector database and moved to `processed/` as a record.

## Supported File Types

- **Text**: `.txt`, `.md` (Markdown)
- **PDF**: `.pdf`
- **Microsoft Office**: `.docx`, `.xlsx`, `.pptx`
- **Data**: `.json`, `.csv`

## Organizing Documents

You can organize documents in subdirectories within `pending/`:

```
pending/
├── research-papers/
├── documentation/
└── reports/
```

The directory structure is preserved when moved to `processed/`.

## Reprocessing Documents

If you need to reprocess a document:

**Option 1: Using the API** (recommended)
```python
ingestion.reprocess_document("my-document.pdf")
```

**Option 2: Manual Move**
```bash
mv data/knowledge_base/processed/my-document.pdf data/knowledge_base/pending/
```

## Processing Pipeline

Each document goes through:
1. **Load**: Parse the document based on file type
2. **Chunk**: Split into semantic chunks (type-aware)
3. **Embed**: Generate embeddings using configured provider
4. **Store**: Insert into vector database
5. **Move**: Transfer to `processed/` folder

## Best Practices

- **Backup**: Keep original files backed up elsewhere
- **Batch Processing**: Add multiple files at once for efficiency
- **Check Logs**: Review ingestion results for any errors
- **Clean Pending**: Remove files you don't want processed
- **Monitor Processed**: Archive shows what's in your vector database

## Configuration

Set custom directories in your `.env`:

```bash
PENDING_DIR=./data/knowledge_base/pending
PROCESSED_DIR=./data/knowledge_base/processed
```

## Troubleshooting

### Document Won't Process
- Check file format is supported
- Verify file isn't corrupted
- Check ingestion logs for specific error

### Want to Reprocess Everything
1. Move all files from `processed/` to `pending/`
2. Optionally clear vector database
3. Run ingestion again

### Duplicate Documents
- The system handles name conflicts by appending timestamps
- Example: `document.pdf` becomes `document_20240115_143022.pdf`
