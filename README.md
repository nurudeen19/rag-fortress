# RAG Fortress

Enterprise-grade Retrieval-Augmented Generation (RAG) platform with role-based access control, multi-provider support, and adaptive retrieval strategies. Built with FastAPI and Vue.js.

## ✨ Key Features

- **Role-Based Access Control (RBAC)**: Department-based permissions with admin, manager, and user roles
- **Multi-Tier Invitation System**: Email invitations with organization and department assignment
- **Adaptive Retrieval**: Automatic fallback strategies (vector → hybrid → full-text → LLM-only)
- **Multi-Provider Support**: OpenAI, Google Gemini, HuggingFace, Llama.cpp with automatic fallback
- **4 Vector Databases**: Chroma (dev only), Qdrant, Pinecone, Weaviate
- **Document Management**: Upload tracking, folder-based organization, reprocessing jobs
- **Smart Caching**: Query result caching with configurable TTL
- **Reranking**: Cross-encoder rerankers for improved retrieval accuracy
- **Real-time Notifications**: In-app notification system with read/unread tracking
- **Database Migrations**: Alembic migrations with SQLite/PostgreSQL/MySQL support
- **Comprehensive Testing**: 93+ test cases covering all configurations
- **Production Ready**: Health checks, logging, exception handling, job queue system

## 🚀 Quick Start

See **[Installation Guide](backend/INSTALLATION.md)** for complete setup instructions.

### TL;DR

**Backend:**
```bash
cd backend
uv sync                    # Install dependencies
cp .env.example .env       # Configure your API keys and database

# Option 1: Using uv run (recommended - no activation needed)
uv run python setup.py     # Initialize database with migrations and seeders
uv run python run.py       # Start server on http://localhost:8000

# Option 2: Activate environment first
.venv\Scripts\Activate     # Windows
source .venv/bin/activate  # macOS/Linux
python setup.py
python run.py
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env       # Configure API URL
npm run dev                # Start on http://localhost:5173
```

**Default Credentials:**
- Admin: `admin@ragfortress.com` / `admin@Rag1`

## 📚 Documentation

- **[Installation Guide](backend/docs/INSTALLATION.md)** - Complete setup with uv, prerequisites, and troubleshooting
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