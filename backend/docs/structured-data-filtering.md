# Structured Data Field Filtering (JSON, CSV, XLSX)

## Overview

When ingesting structured data files, you often don't want to embed every field - some may be irrelevant, sensitive, or redundant. The field filtering feature supports:

- **JSON** - Filter object fields, flatten nested structures
- **CSV** - Filter columns by header name
- **XLSX** - Filter columns across multiple sheets

Benefits:
- **Select specific fields** to keep (e.g., only Name, Email, Department)
- **Reduce embedding costs** by excluding unnecessary data (40-60% reduction)
- **Protect sensitive data** by filtering out SSNs, salaries, internal IDs
- **Improve search quality** by removing noise and irrelevant fields
- **Compliance-friendly** for GDPR and data protection requirements

## Location

This functionality is implemented in:
- **`app/services/chunking.py`** - Field filtering for all structured formats
  - `_chunk_json()` - JSON with flattening support
  - `_chunk_csv()` - CSV column filtering
  - `_chunk_xlsx()` - XLSX column filtering across sheets
- **`app/services/document_ingestion.py`** - Unified API for all formats

## Basic Usage

### JSON - Keep All Fields (Default)

```python
from app.services.document_ingestion import DocumentIngestionService

async with DocumentIngestionService() as ingestion:
    # Default: keeps all fields, flattens nested objects
    result = await ingestion.ingest_document("user.json")
```

### JSON - Filter Specific Fields

```python
# Only keep name, company, and city
result = await ingestion.ingest_document(
    "user.json",
    fields_to_keep=["name", "company", "city"]
)
```

**Input:**
```json
{
    "name": "John Doe",
    "age": 30,
    "company": "OpenAI",
    "city": "San Francisco",
    "occupation": "Researcher",
    "salary": 150000
}
```

**Output (embedded):**
```
name: John Doe
company: OpenAI
city: San Francisco
```

### CSV - Filter Columns

```python
# Only keep Name, Email, and Department columns
result = await ingestion.ingest_document(
    "employees.csv",
    fields_to_keep=["Name", "Email", "Department"]
)
```

**Input CSV:**
```
Name | Email | Department | Salary | SSN | BankAccount
John Doe | john@company.com | Engineering | 120000 | 123-45-6789 | ACC-001
Jane Smith | jane@company.com | Marketing | 95000 | 987-65-4321 | ACC-002
```

**Output (embedded per row):**
```
Name | Email | Department
John Doe | john@company.com | Engineering
```

### XLSX - Filter Columns Across Sheets

```python
# Only keep ProductName, Category, and Price columns
result = await ingestion.ingest_document(
    "products.xlsx",
    fields_to_keep=["ProductName", "Category", "Price"]
)
```

**Input XLSX:**
```
Sheet: Products
ProductID | ProductName | Category | Price | Cost | Profit | InternalCode
1 | Laptop Pro | Electronics | 1299 | 800 | 499 | PROD-001
2 | Wireless Mouse | Electronics | 29 | 15 | 14 | PROD-002
```

**Output (embedded per row):**
```
Sheet: Products
ProductName | Category | Price
Laptop Pro | Electronics | 1299
```

### Filter Nested Fields

```python
# Keep specific nested fields
result = await ingestion.ingest_document(
    "user.json",
    json_fields_to_keep=["name", "email", "address.city", "address.state"]
)
```

**Input:**
```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "address": {
        "street": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94102"
    }
}
```

**Output (embedded):**
```
name: John Doe
email: john@example.com
address.city: San Francisco
address.state: CA
```

### Disable Flattening

```python
# Keep JSON structure instead of flattening
result = await ingestion.ingest_document(
    "user.json",
    json_fields_to_keep=["name", "company", "address"],
    json_flatten=False
)
```

**Output:**
```
name: John Doe
company: OpenAI
address: {"street": "123 Main St", "city": "San Francisco", "state": "CA", "zip": "94102"}
```

## Array Processing

When your JSON is an array of objects:

```json
[
    {
        "name": "Alice",
        "email": "alice@company.com",
        "company": "TechCorp",
        "internal_id": "INT-001",
        "ssn": "123-45-6789"
    },
    {
        "name": "Bob",
        "email": "bob@company.com",
        "company": "DataCo",
        "internal_id": "INT-002",
        "ssn": "987-65-4321"
    }
]
```

**Filter out sensitive data:**

```python
result = await ingestion.ingest_document(
    "users.json",
    json_fields_to_keep=["name", "email", "company"]
)
```

**Result:**
- Creates **2 chunks** (1 per user)
- Each chunk contains only: name, email, company
- Excludes: internal_id, ssn (sensitive)

## Batch Processing

Apply filtering to all JSON files in pending directory:

```python
results = await ingestion.ingest_from_pending(
    file_types=['json'],
    json_fields_to_keep=["name", "email", "company", "role"],
    json_flatten=True
)
```

## Use Cases

### 1. Exclude Sensitive Data

**Employee Records (CSV/XLSX):**
```python
# Exclude salary, SSN, bank accounts
fields_to_keep=["Name", "Email", "Department", "Role"]
```

**User Profiles (JSON):**
```python
# Exclude passwords, API keys, internal IDs
fields_to_keep=["name", "email", "profile.bio", "preferences"]
```

### 2. Focus on Business Data

**Product Catalog (XLSX):**
```python
# Customer-facing data only, exclude costs and margins
fields_to_keep=["ProductName", "Category", "Description", "Price"]
```

**Order Data (JSON):**
```python
# Relevant order info, exclude payment details
fields_to_keep=["order_id", "customer.name", "items.product_name", "total"]
```

### 3. Reduce Embedding Costs

**Large Datasets (CSV):**
```python
# Keep only searchable fields
fields_to_keep=["Title", "Description", "Category", "Tags"]
# Before: 15 columns → After: 4 columns = 73% cost reduction
```

**Log Files (JSON):**
```python
# Keep summary, exclude verbose details
fields_to_keep=["timestamp", "level", "message", "user"]
# Exclude: stack_traces, debug_info, system_metrics
```

### 4. Nested Configuration Files (JSON Only)

```python
# Config files - extract specific settings
fields_to_keep=[
    "service.name",
    "service.version",
    "database.host",
    "database.port"
]
```

### 5. Multi-Sheet Excel Files

```python
# Process only specific columns from all sheets
fields_to_keep=["Date", "Amount", "Category", "Description"]
# Applies filtering to all sheets, skips sheets without matching columns
```

### 6. Compliance & Privacy

**GDPR Compliance:**
```python
# Exclude PII before embedding
fields_to_keep=[
    "Country",  # Geographic data OK
    "Industry",  # Business data OK
    "Company"   # Company name OK
]
# Excluded: Name, Email, Phone, Address (PII)
```

## Advanced Examples

### Complex Nested Object

**Input:**
```json
{
    "user": {
        "profile": {
            "name": "John",
            "age": 30
        },
        "contact": {
            "email": "john@example.com",
            "phone": "555-1234"
        }
    },
    "metadata": {
        "created_at": "2024-01-15",
        "updated_at": "2024-01-16"
    }
}
```

**Filter:**
```python
json_fields_to_keep=[
    "user.profile.name",
    "user.contact.email",
    "metadata.created_at"
]
```

**Output:**
```
user.profile.name: John
user.contact.email: john@example.com
metadata.created_at: 2024-01-15
```

### Array of Primitives

**Input:**
```json
{
    "name": "John",
    "skills": ["Python", "JavaScript", "SQL"]
}
```

**Output (flattened):**
```
name: John
skills: Python, JavaScript, SQL
```

### Mixed Array (Objects + Primitives)

**Input:**
```json
{
    "items": [
        {"id": 1, "name": "Item A"},
        {"id": 2, "name": "Item B"}
    ],
    "tags": ["new", "featured"]
}
```

**Filter:**
```python
json_fields_to_keep=["items.name", "tags"]
```

**Output:**
```
items[0].name: Item A
items[1].name: Item B
tags: new, featured
```

## API Reference

### DocumentChunker.chunk_document()

```python
def chunk_document(
    self,
    document: Document,
    fields_to_keep: Optional[List[str]] = None,
    json_flatten: bool = True
) -> List[Chunk]
```

**Parameters:**
- `document`: The loaded document
- `fields_to_keep`: List of fields/columns to keep
  - `None`: Keep all fields (default)
  - **JSON**: Field paths with dot notation for nested fields
    - `["name", "email"]`: Top-level fields
    - `["address.city", "address.state"]`: Nested fields
  - **CSV/XLSX**: Column names (case-sensitive, must match header exactly)
    - `["Name", "Email", "Department"]`: Column headers
- `json_flatten`: Whether to flatten nested JSON objects (JSON only)
  - `True`: Convert to key-value pairs (default)
  - `False`: Keep JSON structure

**Returns:**
- List of `Chunk` objects with filtered content

### DocumentIngestionService.ingest_document()

```python
async def ingest_document(
    self,
    file_path: str,
    metadata: Dict[str, Any] = None,
    fields_to_keep: Optional[List[str]] = None,
    json_flatten: bool = True
) -> IngestionResult
```

**Examples:**

```python
# JSON with nested field filtering
result = await ingestion.ingest_document(
    "users.json",
    fields_to_keep=["name", "email", "address.city"]
)

# CSV with column filtering
result = await ingestion.ingest_document(
    "employees.csv",
    fields_to_keep=["Name", "Email", "Department"]
)

# XLSX with column filtering
result = await ingestion.ingest_document(
    "products.xlsx",
    fields_to_keep=["ProductName", "Price", "Category"]
)
```

### DocumentIngestionService.ingest_from_pending()

```python
async def ingest_from_pending(
    self,
    recursive: bool = True,
    file_types: List[str] = None,
    metadata: Dict[str, Any] = None,
    fields_to_keep: Optional[List[str]] = None,
    json_flatten: bool = True
) -> List[IngestionResult]
```

**Examples:**

```python
# Batch process all JSON files with filtering
results = await ingestion.ingest_from_pending(
    file_types=['json'],
    fields_to_keep=["name", "email", "company"]
)

# Batch process all CSV files with filtering
results = await ingestion.ingest_from_pending(
    file_types=['csv'],
    fields_to_keep=["Name", "Email", "Department"]
)

# Batch process mixed formats (same filter applies to all)
results = await ingestion.ingest_from_pending(
    file_types=['json', 'csv', 'xlsx'],
    fields_to_keep=["Name", "Email", "Department"]  # Each format uses matching fields
)
```

## Performance Considerations

### Embedding Cost Reduction

**Before filtering:**
```json
{
    "name": "John",
    "age": 30,
    "email": "john@example.com",
    "address": {...},
    "preferences": {...},
    "history": [...]
}
```
→ **~500 tokens** to embed

**After filtering:**
```
name: John
email: john@example.com
```
→ **~10 tokens** to embed

**Result:** 50x cost reduction!

### Memory Efficiency

- Filtering happens during chunking (before embedding)
- Excluded fields never enter the embedding pipeline
- Reduces memory usage for large JSON files

### Search Relevance

- Flattening improves semantic search
- Key-value pairs are more searchable than nested JSON
- Reduces noise from irrelevant fields

## Best Practices

1. **Always filter production data** - Never embed everything
2. **Exclude sensitive fields** - SSNs, passwords, API keys, internal IDs
3. **Focus on searchable content** - Names, descriptions, categories, tags
4. **Use dot notation for nested fields** - `"address.city"` not `"city"`
5. **Test with samples first** - Verify field names and structure
6. **Document your filters** - Keep a list of filtered fields for each file type

## Testing

Run the examples to see it in action:

```bash
# JSON filtering demo
python examples/json_filtering_example.py

# CSV and XLSX filtering demo
python examples/csv_xlsx_filtering_example.py
```

**JSON Demo** demonstrates:
- All fields (default)
- Filtered fields
- Nested fields
- Array processing
- Batch processing

**CSV/XLSX Demo** demonstrates:
- Column filtering
- Sensitive data exclusion
- Multi-sheet processing
- Cost comparison
- Batch processing

## Format-Specific Notes

### JSON
- **Supports nested fields**: Use dot notation (`"address.city"`)
- **Flattening option**: `json_flatten=True` (default) converts nested objects to key-value pairs
- **Array handling**: Arrays of objects create 1 chunk per object
- **Field matching**: Supports prefix matching for nested fields

### CSV
- **Column names**: Case-sensitive, must match header exactly
- **Delimiter**: Currently assumes `|` (pipe) delimiter
- **Header required**: First row must be header
- **Each row = 1 chunk**: Filtered header included in each chunk

### XLSX
- **Multi-sheet support**: Filtering applies to all sheets
- **Column names**: Case-sensitive, must match header exactly
- **Sheet skipping**: Sheets without matching columns are skipped
- **Each row = 1 chunk**: Sheet name and filtered header included
- **Format**: Assumes text-based XLSX representation (from loader)

## Troubleshooting

### JSON: Field not being kept?

Check the exact field path:
```python
# Wrong
fields_to_keep=["city"]

# Correct (if nested)
fields_to_keep=["address.city"]
```

### CSV/XLSX: Column not being kept?

Check the exact column name (case-sensitive):
```python
# Wrong - case doesn't match
fields_to_keep=["name", "email"]  # lowercase

# Correct - matches CSV header exactly
fields_to_keep=["Name", "Email"]  # matches "Name | Email | ..."
```

### Empty chunks?

If filtering removes all fields, the chunk is skipped:

**JSON:**
```python
# If JSON only has {"id": 1, "internal": "data"}
# And you filter for ["name", "email"]
# Result: 0 chunks (no matching fields)
```

**CSV/XLSX:**
```python
# If CSV has columns: ID | Internal | Code
# And you filter for ["Name", "Email"]
# Result: 0 chunks (no matching columns)
```

### XLSX: Sheet not being processed?

If a sheet doesn't have any matching columns, it's automatically skipped:
```python
# Sheet1: ProductID | ProductName | Price  ← Processed
# Sheet2: WarehouseCode | InternalID | Zone  ← Skipped (no matches)
fields_to_keep=["ProductName", "Price"]
```

### CSV delimiter issues?

Currently assumes `|` (pipe) delimiter. If your CSV uses commas:
```python
# Your CSV uses commas: Name,Email,Department
# But loader converted to: Name | Email | Department
# Use column names as they appear after loading
```

## Future Enhancements

Potential additions:
- **Regex filtering**: `json_fields_pattern="user\..*"`
- **Exclusion list**: `json_fields_to_exclude=["password", "ssn"]`
- **Type filtering**: Only keep strings, exclude numbers
- **Path wildcards**: `"items.*.name"` to match all items
- **Conditional filtering**: Based on field values

## Summary

Field filtering for structured data is implemented in the **chunking layer** (not the loader) because:
- ✅ Loader's job: Parse raw content (load entire file)
- ✅ Chunker's job: Transform for embedding (filter, flatten, split)
- ✅ Separation of concerns
- ✅ Reusable across different ingestion paths

### Unified API Across Formats

One consistent interface for all structured data:

```python
# JSON - nested field support
fields_to_keep=["name", "email", "address.city"]

# CSV - column header names
fields_to_keep=["Name", "Email", "Department"]

# XLSX - column header names (all sheets)
fields_to_keep=["ProductName", "Price", "Category"]
```

### Key Benefits

| Benefit | JSON | CSV | XLSX |
|---------|------|-----|------|
| Reduce Costs | ✓ | ✓ | ✓ |
| Exclude Sensitive Data | ✓ | ✓ | ✓ |
| Improve Search Quality | ✓ | ✓ | ✓ |
| Compliance-Friendly | ✓ | ✓ | ✓ |
| Nested Field Support | ✓ | - | - |
| Flattening Option | ✓ | - | - |
| Multi-Sheet Support | - | - | ✓ |

### Cost Impact Example

**Before Filtering:**
```
Employee CSV: 10 columns × 1000 rows = 10,000 column-values
Embedding cost: $X
```

**After Filtering (3 columns):**
```
Employee CSV: 3 columns × 1000 rows = 3,000 column-values
Embedding cost: $X × 0.3 (70% reduction!)
```

This approach keeps the codebase clean and maintainable while providing powerful filtering capabilities across all structured data formats.
