# Pending Documents

This directory contains documents waiting to be processed by the RAG ingestion pipeline.

## Workflow

1. **Add Documents**: Place any documents you want to process in this folder
2. **Run Ingestion**: The system will automatically process all documents in this folder
3. **Automatic Move**: Successfully processed documents are moved to the `processed/` folder
4. **Retry**: Failed documents remain here for retry

## Supported File Types

- Text files: `.txt`, `.md`
- PDFs: `.pdf`
- Microsoft Office: `.docx`, `.xlsx`, `.pptx`
- Data files: `.json`, `.csv`

## Organizing Documents

You can organize documents in subdirectories:

```
pending/
├── research/
│   ├── paper1.pdf
│   └── paper2.pdf
├── documentation/
│   └── guide.md
└── reports/
    └── quarterly.docx
```

The directory structure is preserved when documents are moved to `processed/`.

## Status

- **Documents in this folder**: Waiting to be processed
- **After successful processing**: Moved to `../processed/`
- **After failure**: Remain here with error logged in ingestion results

## Tips

- Keep original files backed up elsewhere
- Large batches may take time to process
- Check ingestion logs for any errors
- Remove or move files you don't want processed
