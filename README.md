# RAG Fortress

A modular Retrieval-Augmented Generation (RAG) platform built with FastAPI and Vue.js.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG FORTRESS                              │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐          ┌──────────────────────────────┐
│      Frontend        │          │         Backend              │
│      (Vue.js)        │◄────────►│        (FastAPI)             │
│                      │   HTTP   │                              │
│  ┌────────────────┐  │          │  ┌────────────────────────┐  │
│  │  Components    │  │          │  │  Routes/Handlers       │  │
│  │  - Home        │  │          │  │  - /api/chat           │  │
│  │  - Chat UI     │  │          │  │  - /api/documents      │  │
│  └────────────────┘  │          │  └────────────────────────┘  │
│                      │          │                              │
│  ┌────────────────┐  │          │  ┌────────────────────────┐  │
│  │  Services      │  │          │  │  Services              │  │
│  │  - API Client  │  │          │  │  - RAG Pipeline        │  │
│  │  - Axios       │  │          │  │  - Document Processing │  │
│  └────────────────┘  │          │  │  - Embedding Service   │  │
│                      │          │  │  - LLM Integration     │  │
│  ┌────────────────┐  │          │  └────────────────────────┘  │
│  │  State Mgmt    │  │          │                              │
│  │  - Pinia       │  │          │  ┌────────────────────────┐  │
│  └────────────────┘  │          │  │  Core                  │  │
│                      │          │  │  - Config              │  │
│  ┌────────────────┐  │          │  │  - Database            │  │
│  │  Router        │  │          │  │  - Settings            │  │
│  │  - Vue Router  │  │          │  └────────────────────────┘  │
│  └────────────────┘  │          │                              │
│                      │          │  ┌────────────────────────┐  │
│  Port: 3000          │          │  │  Utils                 │  │
│  Vite + Vue 3        │          │  │  - Helpers             │  │
└──────────────────────┘          │  │  - Validators          │  │
                                  │  └────────────────────────┘  │
                                  │                              │
                                  │  ┌────────────────────────┐  │
                                  │  │  Models/Schemas        │  │
                                  │  │  - Data Models         │  │
                                  │  │  - Pydantic Schemas    │  │
                                  │  └────────────────────────┘  │
                                  │                              │
                                  │  Port: 8000                  │
                                  │  Python + FastAPI            │
                                  └──────────────────────────────┘
                                            │
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
          ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
          │  Vector Database │   │   LLM Provider   │   │   File Storage   │
          │   (ChromaDB)     │   │    (OpenAI)      │   │   (Local/S3)     │
          └──────────────────┘   └──────────────────┘   └──────────────────┘
```

## 📁 Project Structure

```
rag-fortress/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── core/              # Core configuration & settings
│   │   │   ├── logging.py     # Centralized logging with colored output
│   │   │   └── exceptions.py  # Custom exceptions & handlers (26 types)
│   │   ├── config/            # Modular configuration system
│   │   │   ├── settings.py    # Main settings (composition)
│   │   │   ├── app_settings.py      # App configuration
│   │   │   ├── llm_settings.py      # LLM providers config
│   │   │   ├── embedding_settings.py # Embedding providers config
│   │   │   └── vectordb_settings.py # Vector DB config
│   │   ├── services/          # Business logic & RAG pipeline
│   │   ├── routes/            # API endpoints
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── middleware/        # Custom middleware
│   │   └── utils/             # Helper functions
│   ├── tests/                 # Backend tests (93+ test cases)
│   ├── docs/                  # Backend documentation
│   │   ├── settings-architecture.md
│   │   ├── settings-architecture-visual.md
│   │   ├── settings-migration-guide.md
│   │   └── refactoring-summary.md
│   ├── logs/                  # Application logs (rotating)
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment template
│   └── .gitignore
│
├── frontend/                  # Vue.js Frontend
│   ├── src/
│   │   ├── components/       # Reusable Vue components
│   │   ├── views/            # Page components (Home, Chat)
│   │   ├── router/           # Vue Router configuration
│   │   ├── stores/           # Pinia state management
│   │   ├── services/         # API service layer
│   │   ├── assets/           # Static assets & styles
│   │   ├── App.vue           # Root component
│   │   └── main.js           # Entry point
│   ├── public/               # Public static files
│   ├── package.json          # Node dependencies
│   ├── vite.config.js        # Vite configuration
│   ├── .env.example          # Frontend env template
│   └── .gitignore
│
├── docs/                     # Documentation
│   └── initial-backlog.md
├── LICENSE
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Node.js 18+**
- **Git**

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Run the server
uvicorn app.main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic Settings** - Modular environment-based configuration
- **ChromaDB / Qdrant** - Vector databases for embeddings (5 providers supported)
- **LangChain** - LLM orchestration framework
- **OpenAI / Google / HuggingFace** - Multiple LLM providers with fallback support
- **SQLAlchemy** - Database ORM
- **Pytest** - Testing framework (93+ test cases)

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **Vite** - Next-generation build tool
- **Vue Router** - Official routing library
- **Pinia** - State management
- **Axios** - HTTP client

## ⚙️ Configuration Architecture

RAG Fortress uses a **modular configuration system** for improved maintainability:

### Modular Settings Structure
```python
Settings (Main)
├── AppSettings         # General app config
├── LLMSettings        # LLM providers (OpenAI, Google, HuggingFace)
├── EmbeddingSettings  # Embedding providers (5 options)
└── VectorDBSettings   # Vector databases (5 options)
```

### Supported Providers

#### LLM Providers
- **OpenAI**: GPT-3.5, GPT-4 models
- **Google**: Gemini Pro models
- **HuggingFace**: Llama, Flan-T5, and more
- **Fallback**: Automatic fallback with smart defaults

#### Embedding Providers
- **HuggingFace**: Sentence Transformers (default, free)
- **OpenAI**: text-embedding models
- **Google**: Gemini embeddings
- **Cohere**: embed-english models
- **Voyage AI**: voyage-2 model

#### Vector Databases
- **Chroma**: Development only
- **Qdrant**: Recommended for production
- **Pinecone**: Fully managed
- **Weaviate**: Open-source
- **Milvus**: High-performance

### Core Features
- ✅ **Multi-Provider Support**: Switch between providers with environment variables
- ✅ **Fallback LLM**: Automatic fallback if primary LLM fails
- ✅ **Environment Validation**: Production restrictions (e.g., Chroma blocked)
- ✅ **Comprehensive Testing**: 93+ test cases covering all configurations
- ✅ **Exception Handling**: 26 custom exception types with proper handlers
- ✅ **Structured Logging**: Colored console output + rotating file logs

📚 **Documentation**: See `backend/docs/settings-architecture.md` for detailed configuration guide

## 📝 Development Workflow

1. **Backend Development**: Work in the `backend/` directory
   - Add routes in `app/routes/`
   - Implement business logic in `app/services/`
   - Define data models in `app/models/` and `app/schemas/`

2. **Frontend Development**: Work in the `frontend/` directory
   - Create components in `src/components/`
   - Add views/pages in `src/views/`
   - API calls go through `src/services/api.js`

3. **Testing**
   - Backend: `pytest` in `backend/tests/`
   - Frontend: Jest/Vitest (to be configured)

## 🔐 Environment Variables

### Backend (.env)

#### Application Settings
- `APP_NAME` - Application name (default: "RAG Fortress")
- `APP_DESCRIPTION` - Short description used in branding and emails (default: "Secure document intelligence platform")
- `ENVIRONMENT` - Environment (development/staging/production)
- `DEBUG` - Debug mode (auto-disabled in production)
- `SECRET_KEY` - JWT secret key (required)
- `DATABASE_URL` - Database connection string

#### LLM Configuration
- `LLM_PROVIDER` - Primary LLM (openai/google/huggingface/llamacpp)
- `OPENAI_API_KEY` - OpenAI API key
- `GOOGLE_API_KEY` - Google Gemini API key
- `HF_API_TOKEN` - HuggingFace API token
- `LLAMACPP_MODEL_PATH` - Local llama.cpp GGUF path (only required if not using the endpoint)
- `LLAMACPP_ENDPOINT_URL` / `LLAMACPP_ENDPOINT_API_KEY` / `LLAMACPP_ENDPOINT_MODEL` (optional) - Preferred OpenAI-compatible llama.cpp HTTP endpoint; leave `LLAMACPP_MODEL_PATH` unset when pointing at a remote model.
- `FALLBACK_LLM_PROVIDER` - Fallback LLM provider (optional)
- `INTERNAL_LLM_PROVIDER` / `INTERNAL_LLM_API_KEY` / `INTERNAL_LLM_MODEL` - Internal model overrides (used for sensitive data)
- `INTERNAL_LLAMACPP_ENDPOINT_URL` / `INTERNAL_LLAMACPP_ENDPOINT_MODEL` / `INTERNAL_LLAMACPP_ENDPOINT_API_KEY` - Internal endpoint-style llama.cpp configuration; works without a local model path.

#### Embedding Configuration
- `EMBEDDING_PROVIDER` - Embedding provider (huggingface/openai/google/cohere/voyage)
- Provider-specific API keys and models

#### Vector Database Configuration
- `VECTOR_DB_PROVIDER` - Vector DB (chroma/qdrant/pinecone/weaviate/milvus)
- Provider-specific connection settings

#### RAG Parameters
- `CHUNK_SIZE` - Document chunk size (default: 1000)
- `CHUNK_OVERLAP` - Chunk overlap (default: 200)
- `TOP_K_RESULTS` - Top-K retrieval (default: 5)
- `SIMILARITY_THRESHOLD` - Similarity threshold (default: 0.7)

📝 **See `.env.example` for complete list and documentation**

### Frontend (.env)
- `VITE_API_BASE_URL` - Backend API URL (default: http://localhost:8000)

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Submit a pull request

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🗺️ Roadmap

- [ ] Core RAG pipeline implementation
- [ ] Document upload & processing
- [ ] Vector database integration
- [ ] LLM query interface
- [ ] User authentication
- [ ] Document management UI
- [ ] Advanced search features
- [ ] Deployment configurations