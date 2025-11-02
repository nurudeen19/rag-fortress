"""
Simple Document Ingestion Example.
Demonstrates: Load → Chunk → Embed → Store pipeline
"""

import asyncio
from pathlib import Path

from app.services.document_ingestion import DocumentIngestionService


async def main():
    """Demonstrate the ingestion pipeline."""
    
    print("=" * 60)
    print("Document Ingestion Pipeline Demo")
    print("=" * 60)
    
    # Initialize ingestion service
    async with DocumentIngestionService() as ingestion:
        
        # Example 1: Ingest a single document from knowledge base
        print("\n[Example 1] Ingesting single document from knowledge base...")
        print("Place your document in: ./data/knowledge_base/")
        result = await ingestion.ingest_document(
            file_path="sample.txt",  # Relative to knowledge_base directory
            metadata={
                "organization": "demo-org",
                "category": "example"
            }
        )
        print(f"Result: {result}")
        
        # Example 2: Ingest ALL documents from knowledge base
        print("\n[Example 2] Ingesting all documents from knowledge base...")
        results = await ingestion.ingest_from_knowledge_base(
            recursive=True,  # Include subdirectories
            file_types=None,  # All supported types (or specify: ['pdf', 'txt'])
            metadata={
                "organization": "demo-org",
                "batch": "knowledge-base-sync"
            }
        )
        
        # Print summary
        print(f"\n{'=' * 60}")
        print("Ingestion Summary:")
        print(f"{'=' * 60}")
        
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        total_chunks = sum(r.chunks_count for r in results if r.success)
        
        print(f"Total documents: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total chunks created: {total_chunks}")
        
        # Show details
        if results:
            print(f"\nDetails:")
            for result in results:
                print(f"  {result}")
        else:
            print(f"\nNo documents found in knowledge base.")
            print(f"Place documents in: ./data/knowledge_base/")


if __name__ == "__main__":
    asyncio.run(main())
