# Knowledge Base Directory

This directory is the centralized location for all documents that will be ingested into the RAG system.

## Purpose

- **Single Source of Truth**: All knowledge base documents should be placed here
- **Upload Destination**: API file uploads will save documents here
- **Terminal Access**: Users can manually add documents by placing them in this folder
- **Organized Storage**: Supports subdirectories for better organization

## Supported File Types

- **Text**: `.txt`, `.md` (Markdown)
- **Documents**: `.pdf`, `.docx`, `.pptx`
- **Data**: `.json`, `.csv`, `.xlsx`

## Directory Structure

```
knowledge_base/
├── docs/           # General documentation
├── manuals/        # User manuals, guides
├── policies/       # Company policies
├── data/           # Datasets, exports
└── ...             # Any custom organization
```

## Usage

### For API Users

Files uploaded via the API will automatically be saved here.

### For Terminal/CLI Users

Simply place your documents in this directory:

```bash
# Copy documents to knowledge base
cp /path/to/document.pdf data/knowledge_base/

# Or organize in subdirectories
cp /path/to/manual.pdf data/knowledge_base/manuals/

# Run ingestion
python scripts/ingest_documents.py
```

### For Developers

```python
from app.services.document_loader import DocumentLoader

loader = DocumentLoader()

# Load specific file
document = loader.load("manual.pdf")

# Load all documents
documents = loader.load_all(recursive=True)

# Load only PDFs from a subdirectory
documents = loader.load_all(recursive=False, file_types=['pdf'])
```

## Security

- Documents must be within this directory (path traversal protection)
- File type validation is enforced
- Only supported file types will be processed

## Best Practices

1. **Organize**: Use subdirectories to organize documents by category
2. **Name Clearly**: Use descriptive filenames
3. **Clean Up**: Remove outdated documents regularly
4. **Backup**: Keep backups of important documents elsewhere
