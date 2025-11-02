# Quick Start: Folder-Based Document Ingestion

## 1. Add Documents

Place documents in the pending folder:

```bash
cp my-document.pdf data/knowledge_base/pending/
```

Or organize in subdirectories:

```bash
data/knowledge_base/pending/
├── research/
│   └── paper.pdf
├── docs/
│   └── manual.docx
└── data/
    └── dataset.csv
```

## 2. Process Documents

```python
import asyncio
from app.services.document_ingestion import DocumentIngestionService

async def process():
    async with DocumentIngestionService() as ingestion:
        results = await ingestion.ingest_from_pending()
        
        for result in results:
            if result.success:
                print(f"✓ {result.document_path}: {result.chunks_count} chunks")
            else:
                print(f"✗ {result.document_path}: {result.error_message}")

asyncio.run(process())
```

## 3. Check Status

### See what's pending
```python
pending = ingestion.get_pending_files()
print(f"Pending: {len(pending)} files")
```

### See what's processed
```python
processed = ingestion.get_processed_files()
print(f"Processed: {len(processed)} files")
```

## 4. Reprocess Documents

### Using API
```python
ingestion.reprocess_document("my-document.pdf")
# Moves from processed/ back to pending/
```

### Manually
```bash
mv data/knowledge_base/processed/my-document.pdf data/knowledge_base/pending/
```

## 5. Handle Failures

Failed documents remain in `pending/` automatically.

Just run ingestion again to retry:
```python
results = await ingestion.ingest_from_pending()
# Only processes files still in pending/
```

## Common Patterns

### Process Only PDFs
```python
results = await ingestion.ingest_from_pending(file_types=['pdf'])
```

### Add Metadata
```python
results = await ingestion.ingest_from_pending(
    metadata={
        "department": "engineering",
        "batch_date": "2024-01-15"
    }
)
```

### Process Non-Recursively (no subdirectories)
```python
results = await ingestion.ingest_from_pending(recursive=False)
```

## Supported File Types

- Text: `.txt`, `.md`
- PDF: `.pdf`
- Office: `.docx`, `.xlsx`, `.pptx`
- Data: `.json`, `.csv`

## Troubleshooting

### No documents found
```bash
# Check pending directory
ls -la data/knowledge_base/pending/

# Add a test document
echo "Test" > data/knowledge_base/pending/test.txt
```

### Document failed to process
- Check error message in ingestion results
- Verify file is not corrupted
- Ensure file type is supported
- Document will remain in pending/ for retry

### Want to reprocess everything
```bash
# Move all from processed back to pending
mv data/knowledge_base/processed/* data/knowledge_base/pending/

# Optionally clear vector database
# Then run ingestion again
```

## Directory Structure

```
data/
└── knowledge_base/
    ├── pending/          # ← Add documents here
    │   ├── README.md
    │   └── [your files]
    └── processed/        # ← Successfully processed documents
        ├── README.md
        └── [completed files]
```

## That's It!

Simple workflow:
1. Drop files in `pending/`
2. Run `ingest_from_pending()`
3. Files move to `processed/`
4. Check vector database for queries

Need more details? See:
- `docs/folder-based-tracking.md` - Complete documentation
- `data/knowledge_base/README.md` - Workflow guide
- `examples/simple_ingestion.py` - Full example
