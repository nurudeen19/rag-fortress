# Processed Documents

This directory contains documents that have been successfully processed and embedded into the vector database.

## What This Means

Documents in this folder have been:
1. ✅ Loaded and parsed
2. ✅ Split into chunks
3. ✅ Embedded using the configured embedding model
4. ✅ Stored in the vector database

## Workflow

- **Automatic Movement**: Documents are moved here from `pending/` after successful processing
- **Preservation**: The original directory structure from `pending/` is maintained
- **Archive**: These files serve as a record of what's been processed

## If You Need to Reprocess

To reprocess a document that's already been processed:

1. **Option 1**: Use the `reprocess_document()` API method (recommended)
2. **Option 2**: Manually move the file from `processed/` back to `pending/`

## File Organization

The directory structure matches what you had in `pending/`:

```
processed/
├── research/
│   ├── paper1.pdf (processed on 2024-01-15)
│   └── paper2.pdf (processed on 2024-01-15)
├── documentation/
│   └── guide.md (processed on 2024-01-16)
└── reports/
    └── quarterly.docx (processed on 2024-01-17)
```

## Name Conflicts

If a file with the same name is processed multiple times, a timestamp is appended:
- `document.pdf`
- `document_20240115_143022.pdf` (reprocessed version)

## Safety

- **Backup**: Keep original files backed up in another location
- **Don't Delete**: These files serve as the source of truth for what's in your vector database
- **Version Control**: Consider using git or another VCS if you modify source documents

## Database Synchronization

Files in this folder correspond to embedded content in your vector database. If you:
- Delete files from here: The embeddings remain in the database
- Clear the database: Move files back to `pending/` to re-embed
