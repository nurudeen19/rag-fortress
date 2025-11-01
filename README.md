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
│   │   ├── services/          # Business logic & RAG pipeline
│   │   ├── routes/            # API endpoints
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── middleware/        # Custom middleware
│   │   └── utils/             # Helper functions
│   ├── tests/                 # Backend tests
│   ├── logs/                  # Application logs
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
- **ChromaDB** - Vector database for embeddings
- **LangChain** - LLM orchestration framework
- **OpenAI API** - Language model integration
- **SQLAlchemy** - Database ORM
- **Pydantic** - Data validation

### Frontend
- **Vue 3** - Progressive JavaScript framework
- **Vite** - Next-generation build tool
- **Vue Router** - Official routing library
- **Pinia** - State management
- **Axios** - HTTP client

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
- `OPENAI_API_KEY` - OpenAI API key for LLM
- `DATABASE_URL` - Database connection string
- `CHROMA_PERSIST_DIRECTORY` - Vector DB storage path
- `SECRET_KEY` - JWT secret key
- See `.env.example` for full list

### Frontend (.env)
- `VITE_API_BASE_URL` - Backend API URL

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