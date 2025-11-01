# Quick Installation Guide

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation Steps

### 1. Create Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2. Install All Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This will install ~58 packages including all providers. Installation may take 5-15 minutes depending on your internet connection.

### 3. Verify Installation

```bash
# Check Python version
python --version  # Should be 3.9+

# Check installed packages
pip list | grep langchain
pip list | grep openai
pip list | grep chromadb
```

## Alternative: Minimal Installation

If you want to start with minimal dependencies and add providers as needed:

### Step 1: Core Only
```bash
# Install core framework
pip install fastapi uvicorn pydantic pydantic-settings
pip install sqlalchemy alembic
pip install python-dotenv
pip install langchain langchain-core
```

### Step 2: Add Your Chosen Providers

**OpenAI + Qdrant + PostgreSQL** (Recommended for Production):
```bash
pip install langchain-openai openai
pip install langchain-qdrant qdrant-client
pip install asyncpg psycopg2-binary
```

**HuggingFace + Chroma + SQLite** (Good for Development):
```bash
pip install sentence-transformers
pip install langchain-chroma chromadb
pip install aiosqlite
```

**Google + Pinecone + MySQL**:
```bash
pip install langchain-google-genai google-generativeai
pip install langchain-pinecone pinecone-client
pip install aiomysql pymysql
```

## Installation by Category

### LLM Providers

**OpenAI**:
```bash
pip install langchain-openai openai
```

**Google Gemini**:
```bash
pip install langchain-google-genai google-generativeai
```

**HuggingFace**:
```bash
pip install langchain-huggingface huggingface-hub transformers torch
```

### Embedding Providers

**HuggingFace** (Default, no API key needed):
```bash
pip install sentence-transformers
```

**Cohere**:
```bash
pip install langchain-cohere cohere
```

**Voyage AI**:
```bash
pip install voyageai
```

### Vector Databases

**Chroma** (Development):
```bash
pip install langchain-chroma chromadb
```

**Qdrant** (Production Recommended):
```bash
pip install langchain-qdrant qdrant-client
```

**Pinecone** (Cloud):
```bash
pip install langchain-pinecone pinecone-client
```

**Weaviate**:
```bash
pip install langchain-weaviate weaviate-client
```

**Milvus**:
```bash
pip install langchain-milvus pymilvus
```

### SQL Databases

**PostgreSQL** (Production Recommended):
```bash
pip install asyncpg psycopg2-binary
```

**MySQL**:
```bash
pip install aiomysql pymysql cryptography
```

**SQLite** (Built-in, just need async driver):
```bash
pip install aiosqlite
```

## Common Installation Issues

### Issue 1: PyTorch Too Large

**Problem**: PyTorch installation is very large (~2 GB)

**Solution**: Install CPU-only version if you don't need GPU:
```bash
pip install torch==2.1.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
```

Or skip HuggingFace entirely if you're using OpenAI/Google:
```bash
# Comment out these lines in requirements.txt:
# transformers==4.36.0
# torch==2.1.0
```

### Issue 2: Unstructured Package Fails

**Problem**: `unstructured` package requires system dependencies

**Solution** (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install -y libmagic1 poppler-utils tesseract-ocr
pip install unstructured
```

**Solution** (macOS):
```bash
brew install libmagic poppler tesseract
pip install unstructured
```

### Issue 3: Chromadb SQLite Error

**Problem**: Chromadb fails with SQLite version error

**Solution** (Ubuntu/Debian):
```bash
sudo apt-get install libsqlite3-dev
pip install chromadb --force-reinstall
```

### Issue 4: Memory/Disk Space Issues

**Problem**: Not enough disk space or memory

**Solution**: Install selectively
```bash
# Only install what you need
pip install fastapi uvicorn pydantic
pip install langchain langchain-openai openai  # Just OpenAI
pip install langchain-qdrant qdrant-client  # Just Qdrant
# Skip the rest
```

### Issue 5: Conflicting Dependencies

**Problem**: Package version conflicts

**Solution**: Use a fresh virtual environment
```bash
deactivate  # Exit current venv
rm -rf venv  # Delete old venv
python -m venv venv  # Create fresh venv
source venv/bin/activate  # Activate it
pip install -r requirements.txt  # Reinstall
```

## Platform-Specific Notes

### Linux (Ubuntu/Debian)

Install system dependencies first:
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    libsqlite3-dev
```

### macOS

Use Homebrew for system dependencies:
```bash
brew install postgresql@14
brew install libmagic
```

### Windows

Some packages may require Microsoft C++ Build Tools:
1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"
3. Restart and try installation again

## Verification Commands

After installation, verify everything works:

```bash
# Test FastAPI
python -c "import fastapi; print(fastapi.__version__)"

# Test LangChain
python -c "import langchain; print(langchain.__version__)"

# Test OpenAI (if installed)
python -c "import openai; print(openai.__version__)"

# Test Qdrant (if installed)
python -c "import qdrant_client; print('Qdrant OK')"

# Test PostgreSQL driver (if installed)
python -c "import asyncpg; print('PostgreSQL OK')"
```

## Upgrade Packages

To upgrade all packages to latest versions:

```bash
pip install -r requirements.txt --upgrade
```

To upgrade specific packages:

```bash
pip install langchain --upgrade
pip install openai --upgrade
pip install chromadb --upgrade
```

## Freeze Current Environment

To save your current package versions:

```bash
pip freeze > requirements-locked.txt
```

This creates a locked version file that ensures reproducible installations.

## Development vs Production

### Development Setup (All Features)
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If you have dev dependencies
```

### Production Setup (Minimal)
```bash
# Only install what you're using in production
pip install fastapi uvicorn pydantic pydantic-settings
pip install langchain langchain-openai openai
pip install langchain-qdrant qdrant-client
pip install sqlalchemy asyncpg
pip install python-dotenv python-jose passlib
```

## Docker Installation

If using Docker, add to your Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Next Steps

After installation:

1. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

2. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

3. **Access API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Getting Help

If you encounter issues:

1. Check the error message carefully
2. Look for the issue in `docs/dependencies.md`
3. Search for the error online (often package-specific)
4. Check package documentation:
   - LangChain: https://python.langchain.com/
   - FastAPI: https://fastapi.tiangolo.com/
   - Specific providers: Check their official docs

## Summary

- ✅ **Full Installation**: `pip install -r requirements.txt` (all 58 packages)
- ✅ **Selective Installation**: Install only what you need
- ✅ **Verification**: Test imports after installation
- ✅ **Troubleshooting**: Follow platform-specific guides above

Happy coding! 🚀
