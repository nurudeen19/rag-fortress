#!/usr/bin/env python3
"""
Initialize Qdrant Collections

Creates the required Qdrant collections for RAG Fortress.
Reads configuration from app settings.

Usage:
    python init_qdrant.py
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, PayloadSchemaType

from app.config.settings import settings

def init_qdrant():
    """Initialize Qdrant collection with proper configuration."""
    
    # Get configuration from settings
    vectordb_config = settings.vectordb_settings.get_vector_db_config()
    embedding_dimensions = settings.embedding_settings.EMBEDDING_DIMENSIONS
    
    collection_name = vectordb_config.get("collection_name", "rag_fortress")
    enable_hybrid = vectordb_config.get("hybrid_search", False)
    dense_vector_name = vectordb_config.get("dense_vector_name", "dense")
    sparse_vector_name = vectordb_config.get("sparse_vector_name", "sparse")
    
    print("=" * 80)
    print("QDRANT COLLECTION INITIALIZATION")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Collection: {collection_name}")
    print(f"  Hybrid Search: {enable_hybrid}")
    print(f"  Embedding Dimensions: {embedding_dimensions}")
    print()
    
    try:
        # Connect to Qdrant using config (supports both URL and host-based)
        if vectordb_config.get("url"):
            # Cloud/URL-based connection
            client = QdrantClient(
                url=vectordb_config.get("url"),
                api_key=vectordb_config.get("api_key")
            )
            print(f"✓ Connected to Qdrant at {vectordb_config.get('url')}")
        else:
            # Host/port-based connection (Docker, local deployments)
            client = QdrantClient(
                host=vectordb_config.get("host", "localhost"),
                port=vectordb_config.get("port", 6333),
                grpc_port=vectordb_config.get("grpc_port", 6334),
                prefer_grpc=vectordb_config.get("prefer_grpc", False),
                api_key=vectordb_config.get("api_key")
            )
            print(f"✓ Connected to Qdrant at {vectordb_config.get('host')}:{vectordb_config.get('port')}")
        
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if collection_name in collection_names:
            print(f"\n⚠ Collection '{collection_name}' already exists")
            print("  Skipping creation. Delete it manually if you want to recreate it.")
            return
        
        # Create collection with appropriate configuration
        print(f"\nCreating collection '{collection_name}'...")
        
        if enable_hybrid:
            # Create collection with both dense and sparse vectors
            client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    dense_vector_name: VectorParams(
                        size=embedding_dimensions,
                        distance=Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    sparse_vector_name: SparseVectorParams()
                }
            )
            print(f"✓ Created collection with hybrid search enabled")
            print(f"  - Dense vector: {dense_vector_name} ({embedding_dimensions} dimensions, COSINE)")
            print(f"  - Sparse vector: {sparse_vector_name} (BM25)")
        else:
            # Create collection with dense vector only
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=embedding_dimensions,
                    distance=Distance.COSINE
                )
            )
            print(f"✓ Created collection with dense vectors only")
            print(f"  - Vector size: {embedding_dimensions} dimensions")
            print(f"  - Distance metric: COSINE")
        
        # Create payload indexes for security and department filtering
        print(f"\nCreating payload indexes for filtering...")
        
        client.create_payload_index(
            collection_name=collection_name,
            field_name="security_level",
            field_schema=PayloadSchemaType.INTEGER
        )
        print(f"  ✓ Created index: security_level (integer)")
        
        client.create_payload_index(
            collection_name=collection_name,
            field_name="is_department_only",
            field_schema=PayloadSchemaType.BOOL
        )
        print(f"  ✓ Created index: is_department_only (boolean)")
        
        client.create_payload_index(
            collection_name=collection_name,
            field_name="department_id",
            field_schema=PayloadSchemaType.INTEGER
        )
        print(f"  ✓ Created index: department_id (integer, nullable)")
        
        client.create_payload_index(
            collection_name=collection_name,
            field_name="department",
            field_schema=PayloadSchemaType.KEYWORD
        )
        print(f"  ✓ Created index: department (keyword, nullable)")
        
        print()
        print("=" * 80)
        print("✓ Qdrant initialization complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    init_qdrant()
