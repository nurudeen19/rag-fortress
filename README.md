# RAG Fortress

Enterprise-grade Retrieval-Augmented Generation (RAG) platform with role-based access control, multi-provider support, and adaptive retrieval strategies. Built with FastAPI and Vue.js.

## ✨ Key Features

### 🔌 Vendor-Agnostic Architecture
- **Multi-Provider Support**: OpenAI, Google Gemini, HuggingFace, Llama.cpp with automatic fallback
- **6 Vector Databases**: Qdrant, Milvus, Pinecone, Weaviate, Faiss, Chroma (dev only)
- **Flexible Embeddings**: HuggingFace, OpenAI, Google, Cohere, Voyage AI
- **Unified Configuration**: Switch providers effortlessly with environment variables

### 🔒 Enterprise-Grade Security
- **Role-Based Access Control (RBAC)**: Department-based permissions with multi-level security clearance
- **Message Encryption**: Conversation history encrypted at rest with optional cache encryption
- **HTTPOnly Cookie Auth**: Secure authentication with automatic log sanitization
- **Multi-Tier Invitations**: Email invitations with organization and department assignment
- **Document Approval Workflow**: Control document access and processing

### ⚡ Performance & Intelligence
- **Semantic Caching**: RedisVL-powered cache reduces LLM costs by up to 80%
- **Adaptive Retrieval**: Automatic fallback strategies (vector → hybrid → full-text → LLM-only)
- **Hybrid Search**: Vector + keyword search with configurable weights
- **Cross-Encoder Reranking**: Improved retrieval accuracy with reranking models

### 📄 Document Management
- **Multi-Format Support**: PDF, DOCX, TXT, Markdown, CSV, JSON, and more
- **Department Isolation**: Multi-tenant ready with department-level access control
- **Processing Pipeline**: Load → Chunk → Embed → Store with status tracking
- **Reprocessing Jobs**: Background job queue for document updates

### 🛠️ Developer Experience
- **RESTful API**: FastAPI backend with OpenAPI documentation
- **Modern Frontend**: Vue 3 + Vite + TailwindCSS
- **Database Flexibility**: SQLite, PostgreSQL, MySQL with Alembic migrations
- **Demo Mode**: Public showcase mode with restricted features

### 🚀 Production Ready
- **Health Monitoring**: System diagnostics and health checks
- **Admin Dashboard**: Centralized controls for LLM, embeddings, and vector store config
- **Real-time Notifications**: In-app notification system with read/unread tracking
- **Exception Handling**: Comprehensive error reporting and logging
- **Docker Support**: Multi-stage builds with resource limits and secrets management

## 🚀 Quick Start

**Prefer Docker?** See **[Docker Guide](backend/docs/DOCKER.md)** for containerized deployment.

Otherwise, see **[Installation Guide](backend/docs/INSTALLATION.md)** for complete setup instructions.

### TL;DR

**Backend:**
```bash
cd backend
# Install dependencies (choose based on your needs)
uv sync --extra cpu        # For HuggingFace embeddings (sentence transformers)
# uv sync --extra gpu      # For GPU support (large download ~2GB+)
# uv sync --extra llamacpp # For local LLM via llama.cpp (model path)
# uv sync                  # Base install (OpenAI, Google, Cohere only)

# Combine extras if needed:
# uv sync --extra cpu --extra llamacpp  # HuggingFace + local models

cp .env.example .env       # Configure your API keys and database

# Option 1: Using uv run (recommended - no activation needed)
uv run setup.py --all      # Initialize database with migrations and all seeders or
uv run setup.py --only-seeder admin #to run only the admin seeder
uv run startup.py          # Start server on http://localhost:8000

# Option 1a: Development with auto-reload
uv run startup.py --reload # Start with hot-reload

# Option 2: Activate environment first
.venv\Scripts\Activate     # Windows
source .venv/bin/activate  # macOS/Linux
python setup.py --all / python setup.py --only-seeder admin
python startup.py
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env       # Configure API URL
npm run dev                # Start on http://localhost:5173
```

**Default Credentials:**
- Admin: `admin@ragfortress.com` / `admin@RAGFortress123`

## 📚 Documentation

- **[Installation Guide](backend/docs/INSTALLATION.md)** - Complete setup with uv, prerequisites, and troubleshooting
- **[Docker Guide](backend/docs/DOCKER.md)** - Containerized deployment with Docker Compose
- **[Document Management](backend/docs/DOCUMENT_MANAGEMENT_GUIDE.md)** - Document upload workflow
- **[Settings Guide](backend/docs/SETTINGS_GUIDE.md)** - Configuration reference
- **[LLM Guide](backend/docs/LLM_GUIDE.md)** - Primary, Internal, and Fallback LLM configuration
- **[Adaptive Retrieval](backend/docs/RETRIEVAL_GUIDE.md)** - Fallback strategies and reranking
- **[Vector Stores Guide](backend/docs/VECTOR_STORES_GUIDE.md)** - Vector databases and embeddings
- **[Permissions Guide](backend/docs/PERMISSIONS_GUIDE.md)** - RBAC and security clearance
- **[Rate Limiting Guide](backend/docs/RATE_LIMITING_GUIDE.md)** - API rate limiting
- **[Jobs Guide](backend/docs/JOBS_GUIDE.md)** - Background job processing
- **[RBAC System](docs/ROLE_BASED_ACCESS_CONTROL.md)** - Role and permission management
- **API Docs**: `http://localhost:8000/docs` (Swagger) or `/redoc` (ReDoc)

## 🛠️ Tech Stack

**Backend:** FastAPI, SQLAlchemy, LangChain, Alembic, Pydantic, Pytest  
**Frontend:** Vue 3, Vite, Vue Router, Pinia, TailwindCSS, Axios  
**Databases:** PostgreSQL, MySQL, SQLite  
**Vector Stores:** Chroma, Qdrant, Pinecone, Weaviate  
**LLMs:** OpenAI (GPT-3.5/4/4o), Google Gemini, HuggingFace, Llama.cpp  
**Embeddings:** HuggingFace, OpenAI, Google, Cohere

## ⚙️ Configuration

RAG Fortress uses environment variables for all configuration. Key settings:

### Required
- `SECRET_KEY` - JWT secret
- `DATABASE_URL` - Database connection string
- `LLM_PROVIDER` - Primary LLM (openai/google/huggingface/llamacpp)
- `EMBEDDING_PROVIDER` - Embedding provider (huggingface/openai/google/cohere/voyage)
- `VECTOR_DB_PROVIDER` - Vector database (chroma/qdrant/pinecone/weaviate)
- Provider-specific API keys (OPENAI_API_KEY, GOOGLE_API_KEY, etc.)

### Optional
- `FALLBACK_LLM_PROVIDER` - Automatic LLM fallback
- `INTERNAL_LLM_PROVIDER` - Separate LLM for security-sensitive operations
- `ENABLE_RERANKER` - Cross-encoder reranking
- `ENABLE_CACHING` - Query result caching
- `CHUNK_SIZE` / `CHUNK_OVERLAP` - Document chunking parameters
- `TOP_K_RESULTS` / `SIMILARITY_THRESHOLD` - Retrieval parameters

See `.env.example` files for complete configuration options.

### Supported Providers

**LLMs:** OpenAI (GPT-4/GPT-4o), Google Gemini, HuggingFace, Llama.cpp  
**Embeddings:** HuggingFace (free), OpenAI, Google, Cohere, Voyage AI  
**Vector DBs:** Qdrant (recommended), Pinecone, Weaviate, Chroma (dev only)

> **⚠️ Python 3.14 Compatibility**  
> Chroma requires Python ≤3.13 due to pydantic v1 dependencies. Use Qdrant/Pinecone/Weaviate for Python 3.14+, or downgrade to Python 3.12. Fix pending in [chromadb PR #5555](https://github.com/chroma-core/chroma/pull/5555).

## 🧪 Testing

```bash
cd backend
pytest  # Run all tests (93+ test cases)
pytest tests/test_services/  # Specific test directory
pytest -v  # Verbose output
```

## 🚢 Deployment

**Database Migrations:**
```bash
cd backend
alembic upgrade head  # or python migrate.py upgrade to Apply migrations
alembic revision --autogenerate -m "description"  # Create new migration
```

**Production:**
```bash
# Backend
python run_production.py  # Uses Gunicorn with multiple workers

# Frontend
npm run build  # Creates dist/ folder for static hosting
```

**Environment:** Set `ENVIRONMENT=production` to enable production safeguards (blocks Chroma, enforces HTTPS, etc.)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the terms in the [LICENSE](LICENSE) file.

## 👨‍💻 Author

**Nurudeen Habibu**
- GitHub: [@nurudeen19](https://github.com/nurudeen19)
- Repository: [rag-fortress](https://github.com/nurudeen19/rag-fortress)
- Linkedin: [Nurudeen Habibu](https://www.linkedin.com/in/nurudeen-habibu)

## 📞 Support

- **Documentation**: See `backend/docs/` for detailed guides
- **API Reference**: `http://localhost:8000/docs`
- **Issues**: Submit via GitHub Issues

---

Built with ❤️ using FastAPI and Vue.js