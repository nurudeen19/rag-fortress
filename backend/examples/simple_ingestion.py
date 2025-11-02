"""
Simple Document Ingestion Example.
Demonstrates: Load → Chunk → Embed → Store → Move pipeline with folder-based tracking
"""

import asyncio
from pathlib import Path

from app.services.document_ingestion import DocumentIngestionService


async def main():
    """Demonstrate the ingestion pipeline with folder-based tracking."""
    
    print("=" * 60)
    print("Document Ingestion Pipeline Demo (Folder-Based)")
    print("=" * 60)
    
    # Initialize ingestion service
    async with DocumentIngestionService() as ingestion:
        
        # Show current status
        print("\n[Current Status]")
        pending_files = ingestion.get_pending_files()
        processed_files = ingestion.get_processed_files()
        print(f"Pending documents: {len(pending_files)}")
        print(f"Processed documents: {len(processed_files)}")
        
        if pending_files:
            print(f"\nPending files:")
            for file in pending_files[:5]:  # Show first 5
                print(f"  - {file}")
            if len(pending_files) > 5:
                print(f"  ... and {len(pending_files) - 5} more")
        else:
            print(f"\nNo documents in pending directory.")
            print(f"Add documents to: ./data/knowledge_base/pending/")
            print(f"\nExample:")
            print(f"  cp my-document.pdf data/knowledge_base/pending/")
            return
        
        # Example 1: Ingest ALL documents from pending directory
        print("\n[Ingesting all documents from pending directory...]")
        print("Note: Successfully processed documents will be moved to processed/")
        
        results = await ingestion.ingest_from_pending(
            recursive=True,  # Include subdirectories
            file_types=None,  # All supported types
            metadata={
                "organization": "demo-org",
                "batch": "auto-sync"
            }
        )
        
        # Print summary
        print(f"\n{'=' * 60}")
        print("Ingestion Summary:")
        print(f"{'=' * 60}")
        
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        total_chunks = sum(r.chunks_count for r in results if r.success)
        
        print(f"Total documents found: {total}")
        print(f"Successfully processed: {successful}")
        print(f"Failed: {failed}")
        print(f"Total chunks created: {total_chunks}")
        
        # Show details
        if results:
            print(f"\nDetails:")
            for result in results:
                status = "✓" if result.success else "✗"
                msg = f"{result.chunks_count} chunks" if result.success else (result.error_message or "")
                print(f"  {status} {result.document_path}: {msg}")
        
        # Show updated status
        print(f"\n[Status After Ingestion]")
        pending_files = ingestion.get_pending_files()
        processed_files = ingestion.get_processed_files()
        print(f"Pending documents: {len(pending_files)}")
        print(f"Processed documents: {len(processed_files)}")
        
        if failed > 0:
            print(f"\n⚠️  {failed} document(s) failed to process.")
            print(f"Failed documents remain in pending/ for retry.")
            print(f"Check the error messages above for details.")
        
        if successful > 0:
            print(f"\n✓ {successful} document(s) successfully processed and moved to processed/")
        
        # Example 2: Reprocess a specific document
        print(f"\n[Example: Reprocess a document]")
        print("To reprocess a document that's already been processed:")
        print("  ingestion.reprocess_document('my-document.pdf')")
        print("  # This moves it from processed/ back to pending/")


if __name__ == "__main__":
    asyncio.run(main())
