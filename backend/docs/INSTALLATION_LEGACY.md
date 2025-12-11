# Legacy Installation Guide: pip + Chroma (Python 3.11-3.13)

## ⚠️ When to Use This Guide

Use this installation method **only if**:
- You are using Python 3.11, 3.12, or 3.13 (NOT 3.14+)
- You want to use Chroma vector database instead of FAISS
- You prefer traditional pip installation over uv

## Important Compatibility Information

**Python 3.14 Status (December 2025):**
- ❌ Chroma is **currently not compatible** with Python 3.14+ due to C-extension dependencies
- 🔄 Python 3.14 support is **being actively worked on** by the Chroma team
- 📌 Track progress: [GitHub Issue #5996](https://github.com/chroma-core/chroma/issues/5996)
- ⏳ This is a **temporary limitation** - once Chroma releases Python 3.14 support, it will work with all versions

**Recommendation:**
- ✅ **For Python 3.14+ users**: Use the [standard installation](INSTALLATION.md) with FAISS
- ✅ **For production deployments**: Use Qdrant, Pinecone, or other production-grade vector stores
- ⚠️ **For Python 3.11-3.13 users**: This legacy installation is still fully supported

---

## Prerequisites

- **Python 3.11, 3.12, or 3.13** (verify: `python --version`)
  - NOT compatible with Python 3.14+
- **pip** (comes with Python)
- **git** (for cloning the repository)

---

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/nurudeen19/rag-fortress.git
cd rag-fortress/backend
```

### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Verify activation:**
```bash
which python  # macOS/Linux
where python  # Windows
```
Should show the venv path.

### 3. Upgrade pip

```bash
python -m pip install --upgrade pip
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all dependencies including:
- FastAPI and core packages
- LangChain and LLM providers
- **langchain-chroma** and **chromadb** (Chroma vector database)
- All embedding providers (OpenAI, Google, HuggingFace, Cohere)
- Database drivers (PostgreSQL, MySQL, SQLite)
- Development tools (pytest, etc.)

**Installation time:** ~5-10 minutes depending on your connection.

### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration. **Key settings for Chroma:**

#### Vector Database Configuration (Chroma)

```bash
# Use Chroma vector database (Python 3.11-3.13 only)
VECTOR_DB_PROVIDER=chroma
VECTOR_STORE_PERSIST_DIRECTORY=./data/vector_store
VECTOR_STORE_COLLECTION_NAME=rag_fortress
```

#### Database Configuration

```bash
# For development/testing
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./data/rag_fortress.db

# For production (recommended)
# DATABASE_TYPE=postgresql
# DATABASE_URL=postgresql://user:password@localhost:5432/rag_fortress
```

#### LLM Configuration (choose one)

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Google Gemini
# GOOGLE_API_KEY=your-key

# Local Llama (no API key needed)
# LLM_PROVIDER=llama
# LLAMA_MODEL_PATH=./models/llama-2-7b-chat.gguf
```

#### Embeddings Configuration

```bash
# HuggingFace (free, no API key needed)
EMBEDDING_PROVIDER=huggingface
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HF_EMBEDDING_DEVICE=cpu  # or cuda if you have GPU

# OpenAI (paid, higher quality)
# EMBEDDING_PROVIDER=openai
# OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

#### Admin Account Configuration

```bash
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@ragfortress.local
ADMIN_PASSWORD=your-secure-password
ADMIN_FIRSTNAME=Admin
ADMIN_LASTNAME=User
```

### 6. Initialize Database and Load Seeders

**Important:** If using PostgreSQL or MySQL, ensure the database server is running and a database is created before running setup.

```bash
python setup.py
```

This single command will:
- Create database tables (run migrations)
- Load initial seed data (admin user, roles, permissions)
- Set up the complete database schema

**Expected output:**
```
✓ Running migrations...
✓ Migrations complete
✓ Running seeders...
✓ Admin user created
✓ Roles and permissions loaded
✓ Setup complete!
```

#### Optional: Run migrations and seeders separately

```bash
python migrate.py      # Run migrations only
python run_seeders.py  # Run seeders only
```

#### Selective Seeding

```bash
# Run specific seeders
python run_seeders.py admin roles_permissions

# Skip specific seeders
python setup.py --skip-seeder departments,jobs
```

### 7. Start the Server

```bash
python run.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000
```

The API will be available at `http://localhost:8000`

**API Documentation:**
- **Swagger UI**: http://localhost:8000/docs (interactive API testing)
- **ReDoc**: http://localhost:8000/redoc (API documentation)

---

## Post-Installation

### Default Credentials

Log in with the credentials you set in `.env`:
- **Username**: Value of `ADMIN_USERNAME`
- **Email**: Value of `ADMIN_EMAIL`
- **Password**: Value of `ADMIN_PASSWORD`

### Verify Installation

1. **Open Swagger UI**: http://localhost:8000/docs
2. **Test authentication**: Try the `/api/v1/auth/login` endpoint
3. **Upload a document**: Test document ingestion
4. **Ask a question**: Test the RAG chat endpoint

---

## Standard vs Legacy Installation Comparison

| Feature | Standard (uv + FAISS) | Legacy (pip + Chroma) |
|---------|----------------------|----------------------|
| **Python Version** | 3.11, 3.12, 3.13, **3.14+** | 3.11, 3.12, 3.13 only |
| **Package Manager** | uv (fast, modern) | pip (traditional) |
| **Install Speed** | ~1-2 minutes | ~5-10 minutes |
| **Vector Database** | FAISS (default) | Chroma |
| **Installation Command** | `uv sync` | `pip install -r requirements.txt` |
| **Lock File** | `uv.lock` (reproducible) | None |
| **Python 3.14+ Ready** | ✅ Yes | ❌ Not yet |
| **Production Ready** | ✅ (with Qdrant/Pinecone) | ⚠️ (Chroma not recommended) |

---

## Migrating from Legacy to Standard Installation

If you want to upgrade to Python 3.14+ and use the standard installation:

### Step 1: Backup Your Data

```bash
# Backup database
cp data/rag_fortress.db data/rag_fortress.db.backup

# Backup Chroma vector store
cp -r data/vector_store data/vector_store.backup
```

### Step 2: Export Documents (Optional)

If you have important documents in Chroma, export them before migrating:

```python
# Example export script (adapt to your needs)
from app.core.vector_store_factory import get_vector_store
from app.core.embedding_factory import get_embedding_provider

embeddings = get_embedding_provider()
chroma_store = get_vector_store(embeddings, provider="chroma")

# Export documents (implement based on your needs)
# Save to JSON, CSV, or other format
```

### Step 3: Install Python 3.14+

Download and install from [python.org](https://www.python.org/downloads/)

### Step 4: Install uv

**Windows:**
```powershell
powershell -ExecutionPolicy BypassCurrentUser -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 5: Run Standard Installation

```bash
cd backend

# Remove old venv
rm -rf venv  # macOS/Linux
# rmdir /s venv  # Windows

# Install with uv
uv sync

# Update .env to use FAISS
# Change: VECTOR_DB_PROVIDER=chroma
# To: VECTOR_DB_PROVIDER=faiss

# Activate new venv
source .venv/bin/activate  # macOS/Linux
# .\.venv\Scripts\Activate.ps1  # Windows PowerShell

# Start server
python run.py
```

### Step 6: Restore Data

```bash
# Restore database
cp data/rag_fortress.db.backup data/rag_fortress.db

# Re-import documents to FAISS (if needed)
# Use your document management API endpoints
```

---

## Troubleshooting

### "chromadb installation failed"

**Check Python version:**
```bash
python --version  # Must show 3.11.x, 3.12.x, or 3.13.x
```

**If Python 3.14+:**
- Chroma won't work yet
- Check [GitHub Issue #5996](https://github.com/chroma-core/chroma/issues/5996) for status
- Use [standard installation](INSTALLATION.md) with FAISS instead

**If Python 3.11-3.13:**
```bash
# Try installing chromadb separately
pip install chromadb
pip install langchain-chroma
```

### "No module named 'langchain_chroma'"

```bash
pip install langchain-chroma
```

### "Chroma collection not persisting"

**Check `.env` configuration:**
```bash
VECTOR_STORE_PERSIST_DIRECTORY=./data/vector_store
```

**Ensure directory exists:**
```bash
mkdir -p data/vector_store  # macOS/Linux
md data\vector_store  # Windows
```

**Check permissions:**
```bash
ls -la data/  # macOS/Linux - should show vector_store directory
dir data\  # Windows
```

### "uv: command not found" (wrong guide)

You're following the legacy guide. The `uv` command is for the [standard installation](INSTALLATION.md) only. Use `pip` commands instead.

### Database connection issues

**SQLite (default):**
- No setup needed, file created automatically

**PostgreSQL:**
```bash
# Verify PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Create database
createdb -U postgres rag_fortress
```

**MySQL:**
```bash
# Verify MySQL is running
mysql -u root -p -e "SELECT VERSION();"

# Create database
mysql -u root -p -e "CREATE DATABASE rag_fortress;"
```

### Migration errors

```bash
# Try running migrations manually
python migrate.py upgrade

# Check migration status
python migrate.py current

# Reset database (CAUTION: deletes all data)
python setup.py --clear-db
```

---

## Why Use Standard Installation Instead?

**Advantages of Standard (uv + FAISS):**

1. ✅ **Python 3.14+ Support** - Works with latest Python versions
2. ⚡ **10-100x Faster Installation** - uv is significantly faster than pip
3. 🔒 **Better Dependency Resolution** - uv's resolver is more reliable
4. 🚀 **Production-Ready Alternatives** - FAISS, Qdrant, Pinecone scale better
5. 🔮 **Future-Proof** - Not dependent on Chroma's Python 3.14 timeline
6. 📦 **Reproducible Builds** - `uv.lock` ensures consistent environments

**Only use legacy installation if:**
- ❌ You're stuck on Python 3.11-3.13 and can't upgrade
- ❌ You have existing Chroma data you can't easily migrate
- ❌ You specifically need Chroma features (rare use case)

---

## See Also

- [Standard Installation Guide](INSTALLATION.md) - Recommended for Python 3.14+ users
- [Vector Stores Guide](VECTOR_STORES_GUIDE.md) - All vector database options
- [Settings Guide](SETTINGS_GUIDE.md) - Configuration options
- [README](../README.md) - Project overview

---

## Support

- **Python 3.14+ issues**: Use [standard installation](INSTALLATION.md)
- **Chroma-specific issues**: Check [Vector Stores Guide](VECTOR_STORES_GUIDE.md#legacy-chroma-python-311-313-only)
- **General issues**: [GitHub Issues](https://github.com/nurudeen19/rag-fortress/issues)
- **Chroma Python 3.14 status**: [GitHub Issue #5996](https://github.com/chroma-core/chroma/issues/5996)

---

**Project:** RAG Fortress  
**Author:** Nurudeen Habibu  
**GitHub:** [nurudeen19/rag-fortress](https://github.com/nurudeen19/rag-fortress)  
**LinkedIn:** https://www.linkedin.com/in/nurudeen-habibu/  
**License:** MIT
