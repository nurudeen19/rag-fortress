#!/usr/bin/env python3
"""
Developer utility to test vector store wiring and ingestion without touching app startup.

Usage:
  # 1) Vector store smoke test (no ingestion)
  python3 examples/dev_vector_store_test.py --smoke

  # 2) Ingest from pending directory
  python3 examples/dev_vector_store_test.py --ingest --recursive --types pdf txt

  # 3) In-memory doc test (add a single doc)
  python3 examples/dev_vector_store_test.py --inmemory "Hello world" --metadata key=value

Notes:
- Uses the same services as the app (settings, embedding factory, DocumentStorageService)
- Respects .env configuration
- Does not require FastAPI to be running
"""

import argparse
import sys
import os
from typing import List, Optional

# Ensure project root (backend) is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core import get_logger
from app.core.embedding_factory import get_embedding_provider
from app.services.vector_store import DocumentStorageService, get_vector_store
from app.config.settings import settings


logger = get_logger(__name__)


def parse_kv_pairs(pairs: List[str]) -> dict:
    out = {}
    for p in pairs or []:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def smoke_test() -> int:
    logger.info("Starting vector store smoke test (no ingestion)...")
    try:
        embeddings = get_embedding_provider()
        store = get_vector_store(
            embeddings=embeddings,
            provider=getattr(settings, "VECTOR_DB_PROVIDER", None),
            collection_name=None,
        )
        if store is None:
            logger.info("✓ FAISS: ready (created on first from_documents call)")
        else:
            logger.info("✓ Vector store initialized successfully")
        return 0
    except Exception as e:
        logger.exception(f"Smoke test failed: {e}")
        return 1


def ingest_from_pending(recursive: bool, file_types: Optional[List[str]]) -> int:
    logger.info("Starting ingestion from pending directory...")
    try:
        storage = DocumentStorageService()
        results = storage.ingest_from_pending(recursive=recursive, file_types=file_types)
        total = len(results)
        ok = sum(1 for r in results if r.success)
        fail = total - ok
        logger.info(f"Ingestion summary: {ok}/{total} succeeded, {fail} failed")
        return 0 if fail == 0 else 2
    except Exception as e:
        logger.exception(f"Ingestion failed: {e}")
        return 1


def ingest_in_memory(text: str, metadata: dict) -> int:
    logger.info("Starting in-memory document add (single doc)...")
    try:
        from langchain_core.documents import Document
        embeddings = get_embedding_provider()
        store = get_vector_store(embeddings=embeddings, provider=settings.VECTOR_DB_PROVIDER)
        if store is None:
            # For FAISS, create from documents
            from langchain_community.vectorstores import FAISS
            doc = Document(page_content=text, metadata=metadata)
            _ = FAISS.from_documents([doc], embeddings)
            logger.info("✓ FAISS index created from in-memory document")
        else:
            doc = Document(page_content=text, metadata=metadata)
            store.add_documents([doc])
            logger.info("✓ Document added to vector store")
        return 0
    except Exception as e:
        logger.exception(f"In-memory doc test failed: {e}")
        return 1


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Vector store developer tests")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--smoke", action="store_true", help="Run vector store smoke test (no ingestion)")
    group.add_argument("--ingest", action="store_true", help="Ingest documents from pending directory")
    group.add_argument("--inmemory", type=str, help="Add a single in-memory document with this text")
    parser.add_argument("--recursive", action="store_true", help="Recurse into subdirectories for --ingest")
    parser.add_argument("--types", nargs="*", help="File types to include for --ingest (e.g., pdf txt json)")
    parser.add_argument("--metadata", nargs="*", help="key=value metadata for --inmemory")

    args = parser.parse_args(argv)

    if args.smoke:
        return smoke_test()
    if args.ingest:
        ftypes = [t.lower().lstrip(".") for t in (args.types or [])]
        return ingest_from_pending(recursive=args.recursive, file_types=ftypes or None)
    if args.inmemory is not None:
        md = parse_kv_pairs(args.metadata or [])
        return ingest_in_memory(args.inmemory, md)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
