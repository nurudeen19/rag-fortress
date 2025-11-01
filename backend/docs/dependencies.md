# Dependencies Overview

## Complete Package List

RAG Fortress uses a comprehensive set of packages to support multiple providers and ensure maximum flexibility.

## Package Categories

### 1. FastAPI Core (4 packages)
Core framework for building the REST API.

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.104.1 | Web framework |
| `uvicorn[standard]` | 0.24.0 | ASGI server |
| `pydantic` | 2.5.0 | Data validation |
| `pydantic-settings` | 2.1.0 | Settings management |

### 2. HTTP & Async Operations (2 packages)
For async operations and HTTP requests.

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | 0.25.1 | Async HTTP client |
| `aiofiles` | 23.2.1 | Async file operations |

### 3. SQL Database (9 packages)
Support for PostgreSQL, MySQL, and SQLite.

| Package | Version | Purpose |
|---------|---------|---------|
| `sqlalchemy` | 2.0.23 | ORM framework |
| `alembic` | 1.12.1 | Database migrations |
| **PostgreSQL Drivers** |
| `psycopg2-binary` | 2.9.9 | Sync PostgreSQL driver |
| `asyncpg` | 0.29.0 | Async PostgreSQL driver |
| **MySQL Drivers** |
| `pymysql` | 1.1.0 | Sync MySQL driver |
| `aiomysql` | 0.2.0 | Async MySQL driver |
| `cryptography` | 41.0.7 | MySQL SSL support |
| **SQLite Driver** |
| `aiosqlite` | 0.19.0 | Async SQLite driver |

### 4. LangChain Core (3 packages)
Core LangChain framework.

| Package | Version | Purpose |
|---------|---------|---------|
| `langchain` | 0.1.0 | Main framework |
| `langchain-core` | 0.1.7 | Core components |
| `langchain-community` | 0.0.10 | Community integrations |

### 5. LangChain - LLM Providers (9 packages)
Support for OpenAI, Google Gemini, and HuggingFace.

| Package | Version | Purpose |
|---------|---------|---------|
| **OpenAI** |
| `langchain-openai` | 0.0.2 | LangChain OpenAI integration |
| `openai` | 1.3.5 | OpenAI SDK |
| **Google Gemini** |
| `langchain-google-genai` | 0.0.5 | LangChain Google integration |
| `google-generativeai` | 0.3.1 | Google Gemini SDK |
| **HuggingFace** |
| `langchain-huggingface` | 0.0.1 | LangChain HuggingFace integration |
| `huggingface-hub` | 0.19.4 | HuggingFace Hub SDK |
| `transformers` | 4.36.0 | Transformers library |
| `torch` | 2.1.0 | PyTorch (for local models) |

### 6. LangChain - Embedding Providers (5 packages)
Support for 5 embedding providers.

| Package | Version | Purpose |
|---------|---------|---------|
| `sentence-transformers` | 2.2.2 | HuggingFace embeddings (default) |
| `langchain-cohere` | 0.0.3 | Cohere integration |
| `cohere` | 4.37 | Cohere SDK |
| `voyageai` | 0.1.3 | Voyage AI SDK |

**Note**: OpenAI and Google embeddings use their LLM packages listed above.

### 7. LangChain - Vector Databases (10 packages)
Support for 5 vector database providers.

| Package | Version | Purpose |
|---------|---------|---------|
| **Chroma** |
| `langchain-chroma` | 0.0.1 | LangChain Chroma integration |
| `chromadb` | 0.4.18 | Chroma SDK |
| **Qdrant** |
| `langchain-qdrant` | 0.0.1 | LangChain Qdrant integration |
| `qdrant-client` | 1.7.0 | Qdrant SDK |
| **Pinecone** |
| `langchain-pinecone` | 0.0.1 | LangChain Pinecone integration |
| `pinecone-client` | 2.2.4 | Pinecone SDK |
| **Weaviate** |
| `langchain-weaviate` | 0.0.1 | LangChain Weaviate integration |
| `weaviate-client` | 3.25.3 | Weaviate SDK |
| **Milvus** |
| `langchain-milvus` | 0.0.1 | LangChain Milvus integration |
| `pymilvus` | 2.3.4 | Milvus SDK |

### 8. Document Processing (7 packages)
Support for multiple document formats.

| Package | Version | Purpose |
|---------|---------|---------|
| `pypdf2` | 3.0.1 | PDF processing |
| `unstructured` | 0.11.2 | Advanced document parsing |
| `tiktoken` | 0.5.2 | Token counting for chunking |
| `python-docx` | 1.1.0 | Word document processing |
| `openpyxl` | 3.1.2 | Excel file processing |
| `python-pptx` | 0.6.23 | PowerPoint processing |
| `python-multipart` | 0.0.6 | Form data parsing |

### 9. Security & Authentication (2 packages)

| Package | Version | Purpose |
|---------|---------|---------|
| `python-jose[cryptography]` | 3.3.0 | JWT tokens |
| `passlib[bcrypt]` | 1.7.4 | Password hashing |

### 10. Logging & Monitoring (2 packages)

| Package | Version | Purpose |
|---------|---------|---------|
| `python-json-logger` | 2.0.7 | JSON logging |
| `colorlog` | 6.8.0 | Colored console output |

### 11. Environment & Configuration (1 package)

| Package | Version | Purpose |
|---------|---------|---------|
| `python-dotenv` | 1.0.0 | Environment variable loading |

### 12. Testing (4 packages)

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | 7.4.3 | Testing framework |
| `pytest-asyncio` | 0.21.1 | Async test support |
| `pytest-cov` | 4.1.0 | Code coverage |
| `pytest-mock` | 3.12.0 | Mocking utilities |

## Total Package Count

| Category | Packages |
|----------|----------|
| FastAPI Core | 4 |
| HTTP & Async | 2 |
| SQL Database | 9 |
| LangChain Core | 3 |
| LLM Providers | 9 |
| Embedding Providers | 5 |
| Vector Databases | 10 |
| Document Processing | 7 |
| Security | 2 |
| Logging | 2 |
| Environment | 1 |
| Testing | 4 |
| **Total** | **58** |

## Provider Support Matrix

### LLM Providers
| Provider | LangChain Package | SDK Package | Status |
|----------|-------------------|-------------|--------|
| OpenAI | `langchain-openai` | `openai` | ✅ Ready |
| Google Gemini | `langchain-google-genai` | `google-generativeai` | ✅ Ready |
| HuggingFace | `langchain-huggingface` | `transformers`, `torch` | ✅ Ready |

### Embedding Providers
| Provider | LangChain Package | SDK Package | Status |
|----------|-------------------|-------------|--------|
| HuggingFace | N/A | `sentence-transformers` | ✅ Ready |
| OpenAI | `langchain-openai` | `openai` | ✅ Ready |
| Google Gemini | `langchain-google-genai` | `google-generativeai` | ✅ Ready |
| Cohere | `langchain-cohere` | `cohere` | ✅ Ready |
| Voyage AI | N/A | `voyageai` | ✅ Ready |

### Vector Databases
| Provider | LangChain Package | SDK Package | Status |
|----------|-------------------|-------------|--------|
| Chroma | `langchain-chroma` | `chromadb` | ✅ Ready |
| Qdrant | `langchain-qdrant` | `qdrant-client` | ✅ Ready |
| Pinecone | `langchain-pinecone` | `pinecone-client` | ✅ Ready |
| Weaviate | `langchain-weaviate` | `weaviate-client` | ✅ Ready |
| Milvus | `langchain-milvus` | `pymilvus` | ✅ Ready |

### SQL Databases
| Provider | Sync Driver | Async Driver | Status |
|----------|-------------|--------------|--------|
| PostgreSQL | `psycopg2-binary` | `asyncpg` | ✅ Ready |
| MySQL | `pymysql` | `aiomysql` | ✅ Ready |
| SQLite | Built-in | `aiosqlite` | ✅ Ready |

## Installation

### Full Installation
Install all dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Selective Installation
If you want to reduce dependencies, you can comment out providers you don't need in `requirements.txt`.

**Example: Only OpenAI + Qdrant**
```bash
# Comment out other LLM providers (Google, HuggingFace)
# Comment out other vector databases (Chroma, Pinecone, Weaviate, Milvus)
pip install -r requirements.txt
```

## Optional: CPU-Only PyTorch
If you don't need GPU support for HuggingFace models, you can use CPU-only PyTorch to reduce installation size:

```bash
# Replace torch==2.1.0 with:
pip install torch==2.1.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
```

## Size Considerations

### Installation Sizes (Approximate)
| Component | Size |
|-----------|------|
| FastAPI & Core | ~50 MB |
| LangChain Core | ~30 MB |
| All LLM Providers | ~2.5 GB (PyTorch is large) |
| All Vector DBs | ~200 MB |
| Document Processing | ~500 MB |
| Testing | ~50 MB |
| **Total** | **~3.3 GB** |

### Reducing Installation Size
1. **Skip PyTorch** if not using local HuggingFace models: Save ~2 GB
2. **Comment out unused vector databases**: Save ~150 MB
3. **Skip `unstructured`** if only using PDFs: Save ~400 MB

## Development vs Production

### Development
Install everything for testing all features:
```bash
pip install -r requirements.txt
```

### Production
Only install what you're actually using:
```bash
# Example: OpenAI + Qdrant + PostgreSQL
pip install fastapi uvicorn pydantic pydantic-settings \
    langchain langchain-openai openai \
    langchain-qdrant qdrant-client \
    sqlalchemy asyncpg \
    python-dotenv python-jose passlib
```

## Version Notes

- **LangChain**: Using latest stable versions (0.1.x)
- **PyTorch**: Version 2.1.0 for compatibility with transformers
- **Pydantic**: Version 2.5.0 (Pydantic v2)
- **SQLAlchemy**: Version 2.0.23 (SQLAlchemy 2.0)

## Compatibility

All packages are tested and compatible with:
- **Python**: 3.9, 3.10, 3.11
- **OS**: Linux, macOS, Windows

## Updates

To update all packages to latest compatible versions:
```bash
pip install -r requirements.txt --upgrade
```

To update specific packages:
```bash
pip install langchain --upgrade
pip install openai --upgrade
```

## Troubleshooting

### PyTorch Installation Issues
```bash
# CPU only (smaller)
pip install torch==2.1.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

# GPU (CUDA 11.8)
pip install torch==2.1.0+cu118 -f https://download.pytorch.org/whl/torch_stable.html
```

### Unstructured Installation Issues
```bash
# Install system dependencies first (Ubuntu/Debian)
sudo apt-get install libmagic1 poppler-utils tesseract-ocr

# Then install unstructured
pip install unstructured
```

### Chromadb Installation Issues
```bash
# If SQLite issues on Linux
sudo apt-get install libsqlite3-dev

# Then reinstall
pip install chromadb --force-reinstall
```

## License Compliance

All packages are open-source with permissive licenses:
- Most packages: MIT or Apache 2.0
- PyTorch: BSD-style license
- Transformers: Apache 2.0

Always check individual package licenses for production use.
