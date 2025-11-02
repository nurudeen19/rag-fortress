"""
JSON Field Filtering Example
Demonstrates how to ingest JSON files with selective field filtering
"""

import asyncio
import json
from pathlib import Path
from app.services.document_ingestion import DocumentIngestionService


async def demo_json_filtering():
    """Demonstrate JSON field filtering and flattening."""
    
    print("=" * 70)
    print("JSON Field Filtering and Flattening Demo")
    print("=" * 70)
    
    # Create sample JSON files for demo
    pending_dir = Path("./data/knowledge_base/pending")
    pending_dir.mkdir(parents=True, exist_ok=True)
    
    # Example 1: User profile with many fields
    user_data = {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com",
        "company": "OpenAI",
        "city": "San Francisco",
        "country": "USA",
        "occupation": "Researcher",
        "department": "AI Research",
        "employee_id": "EMP-12345",
        "salary": 150000,
        "address": {
            "street": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94102"
        },
        "skills": ["Python", "Machine Learning", "NLP"]
    }
    
    sample_file = pending_dir / "sample_user.json"
    with open(sample_file, 'w') as f:
        json.dump(user_data, f, indent=2)
    
    print(f"\n[Created Sample File: {sample_file.name}]")
    print(json.dumps(user_data, indent=2))
    
    # Example 2: Array of objects
    users_data = [
        {
            "name": "Alice Smith",
            "email": "alice@company.com",
            "company": "TechCorp",
            "role": "Engineer",
            "location": {"city": "New York", "country": "USA"},
            "internal_id": "INT-001",
            "ssn": "123-45-6789"
        },
        {
            "name": "Bob Johnson",
            "email": "bob@company.com",
            "company": "DataCo",
            "role": "Data Scientist",
            "location": {"city": "Boston", "country": "USA"},
            "internal_id": "INT-002",
            "ssn": "987-65-4321"
        }
    ]
    
    users_file = pending_dir / "users_list.json"
    with open(users_file, 'w') as f:
        json.dump(users_data, f, indent=2)
    
    print(f"\n[Created Sample File: {users_file.name}]")
    print(f"Array of {len(users_data)} user objects")
    
    # Initialize ingestion service
    async with DocumentIngestionService() as ingestion:
        
        # Scenario 1: Keep ALL fields (default behavior)
        print("\n" + "=" * 70)
        print("Scenario 1: Keep ALL fields (no filtering)")
        print("=" * 70)
        
        result = await ingestion.ingest_document(
            "sample_user.json",
            metadata={"scenario": "all_fields"}
        )
        print(f"\nResult: {result}")
        print(f"Chunks created: {result.chunks_count}")
        
        # Move back to pending for next scenario
        ingestion.reprocess_document("sample_user.json")
        
        # Scenario 2: Keep only specific fields
        print("\n" + "=" * 70)
        print("Scenario 2: Keep ONLY name, company, and city")
        print("=" * 70)
        
        fields_to_keep = ["name", "company", "city"]
        print(f"Fields to keep: {fields_to_keep}")
        
        result = await ingestion.ingest_document(
            "sample_user.json",
            json_fields_to_keep=fields_to_keep,
            metadata={"scenario": "filtered_fields"}
        )
        print(f"\nResult: {result}")
        print(f"Chunks created: {result.chunks_count}")
        print(f"\nFiltered content will only contain:")
        print(f"  - name: John Doe")
        print(f"  - company: OpenAI")
        print(f"  - city: San Francisco")
        print(f"\nNote: age, occupation, salary, etc. are excluded!")
        
        # Move back for next scenario
        ingestion.reprocess_document("sample_user.json")
        
        # Scenario 3: Keep nested fields
        print("\n" + "=" * 70)
        print("Scenario 3: Keep nested fields (address.city, address.state)")
        print("=" * 70)
        
        nested_fields = ["name", "email", "address.city", "address.state"]
        print(f"Fields to keep: {nested_fields}")
        
        result = await ingestion.ingest_document(
            "sample_user.json",
            json_fields_to_keep=nested_fields,
            json_flatten=True,
            metadata={"scenario": "nested_fields"}
        )
        print(f"\nResult: {result}")
        print(f"Chunks created: {result.chunks_count}")
        print(f"\nFlattened content will contain:")
        print(f"  - name: John Doe")
        print(f"  - email: john@example.com")
        print(f"  - address.city: San Francisco")
        print(f"  - address.state: CA")
        
        # Move back for next scenario
        ingestion.reprocess_document("sample_user.json")
        
        # Scenario 4: No flattening (keep JSON structure)
        print("\n" + "=" * 70)
        print("Scenario 4: Keep structure (no flattening)")
        print("=" * 70)
        
        result = await ingestion.ingest_document(
            "sample_user.json",
            json_fields_to_keep=["name", "company", "address"],
            json_flatten=False,
            metadata={"scenario": "no_flatten"}
        )
        print(f"\nResult: {result}")
        print(f"Chunks created: {result.chunks_count}")
        print(f"\nContent will preserve nested JSON structure:")
        print(f'  - name: John Doe')
        print(f'  - company: OpenAI')
        print(f'  - address: {{"street": "123 Main St", "city": "San Francisco", ...}}')
        
        # Move back for array processing
        ingestion.reprocess_document("sample_user.json")
        
        # Scenario 5: Process array of objects with filtering
        print("\n" + "=" * 70)
        print("Scenario 5: Array of objects with field filtering")
        print("=" * 70)
        print("Processing users_list.json (array of 2 users)")
        print("Keeping only: name, email, company, role, location.city")
        print("Excluding: internal_id, ssn (sensitive data)")
        
        result = await ingestion.ingest_document(
            "users_list.json",
            json_fields_to_keep=["name", "email", "company", "role", "location.city"],
            metadata={"scenario": "array_filtered"}
        )
        print(f"\nResult: {result}")
        print(f"Chunks created: {result.chunks_count} (1 chunk per user)")
        print(f"\nEach chunk contains:")
        print(f"  - name: <user name>")
        print(f"  - email: <user email>")
        print(f"  - company: <company name>")
        print(f"  - role: <job role>")
        print(f"  - location.city: <city name>")
        print(f"\n✓ Sensitive fields (internal_id, ssn) are excluded!")
        
        # Scenario 6: Batch process multiple JSON files
        print("\n" + "=" * 70)
        print("Scenario 6: Batch process all JSON files")
        print("=" * 70)
        
        results = await ingestion.ingest_from_pending(
            file_types=['json'],
            json_fields_to_keep=["name", "email", "company"],
            json_flatten=True
        )
        
        print(f"\nProcessed {len(results)} JSON files")
        for result in results:
            status = "✓" if result.success else "✗"
            print(f"  {status} {result.document_path}: {result.chunks_count} chunks")
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("1. Filter JSON fields to reduce embedding costs")
    print("2. Exclude sensitive data (SSN, internal IDs, passwords)")
    print("3. Focus on relevant business data only")
    print("4. Flatten nested objects for better searchability")
    print("5. Process arrays efficiently (1 chunk per object)")
    
    # Cleanup
    sample_file.unlink(missing_ok=True)
    users_file.unlink(missing_ok=True)
    print("\n✓ Sample files cleaned up")


if __name__ == "__main__":
    asyncio.run(demo_json_filtering())
