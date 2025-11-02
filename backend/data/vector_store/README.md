# Vector Store Data Directory

This directory contains the persistent storage for the vector database.

## Purpose

- Stores ChromaDB vector embeddings and metadata
- Persists between application restarts
- Contains indexed document chunks and their embeddings

## Contents

When ChromaDB is running, this directory will contain:
- Collection metadata
- Vector indices
- Document chunks
- Embeddings

## Usage

This directory is automatically managed by the application. Do not manually modify its contents.

## Backup

To backup your vector database, copy this entire directory:

```bash
# Backup
cp -r data/vector_store data/vector_store.backup

# Restore
cp -r data/vector_store.backup data/vector_store
```

## Clean Start

To start fresh (delete all indexed documents):

```bash
rm -rf data/vector_store/*
```

The application will recreate the necessary files on next run.
