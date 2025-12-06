# RAG Fortress

Enterprise-grade Retrieval-Augmented Generation (RAG) platform with role-based access control, multi-provider support, and adaptive retrieval strategies. Built with FastAPI and Vue.js.

## ✨ Key Features

- **Role-Based Access Control (RBAC)**: Department-based permissions with admin, manager, and user roles
- **Multi-Tier Invitation System**: Email invitations with organization and department assignment
- **Adaptive Retrieval**: Automatic fallback strategies (vector → hybrid → full-text → LLM-only)
- **Multi-Provider Support**: OpenAI, Google Gemini, HuggingFace, Llama.cpp with automatic fallback
- **5 Vector Databases**: Chroma, Qdrant, Pinecone, Weaviate, Milvus
- **Document Management**: Upload tracking, folder-based organization, reprocessing jobs
- **Smart Caching**: Query result caching with configurable TTL
- **Reranking**: Cohere/HuggingFace rerankers for improved retrieval accuracy
- **Real-time Notifications**: In-app notification system with read/unread tracking
- **Database Migrations**: Alembic migrations with SQLite/PostgreSQL/MySQL support
- **Comprehensive Testing**: 93+ test cases covering all configurations
- **Production Ready**: Health checks, logging, exception handling, job queue system

## 🚀 Quick Start

### Prerequisites

- Python 3.9-3.13 (3.14 not compatible with Chroma - see compatibility notice below)
- Node.js 18+
- PostgreSQL/MySQL/SQLite
- API key for at least one LLM provider (OpenAI, Google, or HuggingFace)

### Installation

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configure your API keys and database
python setup.py  # Initialize database with seeders
python run.py  # Start server on http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env  # Configure API URL
npm run dev  # Start on http://localhost:5173
```

**Default Credentials:**
- Super Admin: `superadmin@ragfortress.local` / `SuperAdmin123!`
- Admin: `admin@ragfortress.local` / `Admin123!`
- Manager: `manager@ragfortress.local` / `Manager123!`
- User: `user@ragfortress.local` / `User123!`

## 📚 Documentation

- **[Installation Guide](backend/docs/installation-guide.md)** - Detailed setup instructions
- **[Quick Start: Ingestion](backend/docs/quick-start-ingestion.md)** - Document upload workflow
- **[Settings Architecture](backend/docs/complete-settings-architecture.md)** - Configuration deep dive
- **[Migrations Guide](backend/docs/MIGRATIONS_GUIDE.md)** - Database migrations
- **[Adaptive Retrieval](backend/docs/ADAPTIVE_RETRIEVAL.md)** - Fallback strategies
- **[RBAC System](docs/ROLE_BASED_ACCESS_CONTROL.md)** - Role and permission management
- **[Email System](backend/docs/EMAIL_SYSTEM.md)** - Invitation system
- **[Job Manager](backend/docs/JOB_MANAGER.md)** - Background job processing
- **API Docs**: `http://localhost:8000/docs` (Swagger) or `/redoc` (ReDoc)

## 🛠️ Tech Stack

**Backend:** FastAPI, SQLAlchemy, LangChain, Alembic, Pydantic, Pytest  
**Frontend:** Vue 3, Vite, Vue Router, Pinia, TailwindCSS, Axios  
**Databases:** PostgreSQL, MySQL, SQLite  
**Vector Stores:** Chroma, Qdrant, Pinecone, Weaviate, Milvus  
**LLMs:** OpenAI (GPT-3.5/4), Google Gemini, HuggingFace, Llama.cpp  
**Embeddings:** HuggingFace, OpenAI, Google, Cohere, Voyage AI

## ⚙️ Configuration

RAG Fortress uses environment variables for all configuration. Key settings:

### Required
- `SECRET_KEY` - JWT secret
- `DATABASE_URL` - Database connection string
- `LLM_PROVIDER` - Primary LLM (openai/google/huggingface/llamacpp)
- `EMBEDDING_PROVIDER` - Embedding provider (huggingface/openai/google/cohere/voyage)
- `VECTOR_DB_PROVIDER` - Vector database (chroma/qdrant/pinecone/weaviate/milvus)
- Provider-specific API keys (OPENAI_API_KEY, GOOGLE_API_KEY, etc.)

### Optional
- `FALLBACK_LLM_PROVIDER` - Automatic LLM fallback
- `INTERNAL_LLM_PROVIDER` - Separate LLM for sensitive operations
- `RERANKER_PROVIDER` - Cohere/HuggingFace reranking
- `ENABLE_CACHING` - Query result caching
- `CHUNK_SIZE` / `CHUNK_OVERLAP` - Document chunking parameters
- `TOP_K_RESULTS` / `SIMILARITY_THRESHOLD` - Retrieval parameters

See `.env.example` files for complete configuration options.

### Supported Providers

**LLMs:** OpenAI (GPT-4/5), Google Gemini, HuggingFace, Llama.cpp  
**Embeddings:** HuggingFace (free), OpenAI, Google, Cohere, Voyage AI  
**Vector DBs:** Qdrant (recommended), Pinecone, Weaviate, Milvus, Chroma (dev only)

> **⚠️ Python 3.14 Compatibility**  
> Chroma requires Python ≤3.13 due to pydantic v1 dependencies. Use Qdrant/Pinecone/Weaviate for Python 3.14+, or downgrade to Python 3.12. Fix pending in [chromadb PR #5555](https://github.com/chroma-core/chroma/pull/5555).

## 🧪 Testing

```bash
cd backend
pytest  # Run all tests (93+ test cases)
pytest tests/test_services/  # Specific test directory
pytest -v  # Verbose output
pytest --cov=app  # Coverage report
```

## 🚢 Deployment

**Database Migrations:**
```bash
cd backend
alembic upgrade head  # Apply migrations
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

## 📞 Support

- **Documentation**: See `backend/docs/` for detailed guides
- **API Reference**: `http://localhost:8000/docs`
- **Issues**: Submit via GitHub Issues

---

Built with ❤️ using FastAPI and Vue.js