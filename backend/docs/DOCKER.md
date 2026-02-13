# Docker Installation Guide

Complete guide to running RAG Fortress with Docker.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- Git (for cloning the repository)

Verify installation:
```bash
docker --version
docker compose version
```

## Quick Start

RAG Fortress has a three-level Docker setup:
- **Root** (`/docker-compose.yml`) - Runs both frontend and backend
- **Backend** (`/backend/docker-compose.yml`) - Backend services only
- **Frontend** (`/frontend/docker-compose.yml`) - Frontend only

### Option A: Full Stack (Frontend + Backend)

**1. Clone and navigate to project root:**
```bash
git clone <repository-url>
cd rag-fortress
```

**2. Build all images:**
```bash
docker compose build
```
*Note: First build takes 5-10+ minutes depending on your network as Docker downloads base images (Python, Node, PostgreSQL, Redis, etc.)*

**3. Generate encryption keys:**
```bash
cd backend
docker compose --profile keygen run --rm keygen
```

Copy the three output keys and add them to `backend/.env.docker`:
- `SECRET_KEY`
- `MASTER_ENCRYPTION_KEY`
- `SETTINGS_ENCRYPTION_KEY`

**4. Configure environment:**

Edit `backend/.env.docker` with your settings:
- Database credentials (or use defaults)
- API keys (OpenAI, Google, etc.)
- LLM configurations
- Email settings (uses Mailpit by default)

**5. Initialize database:**

Run migrations and seeders (recommended for first-time setup):
```bash
docker compose --profile setupdb run --rm db-setup
```

Or use specific options:
```bash
# Migrations only
docker compose --profile setupdb run --rm db-setup python migrate.py

# All seeders (default option)
docker compose --profile setupdb run --rm db-setup python setup.py --all

# Specific seeders only (comma-separated)
docker compose --profile setupdb run --rm db-setup python setup.py --only-seeder admin,roles_permissions

# Skip specific seeders
docker compose --profile setupdb run --rm db-setup python setup.py --skip-seeder knowledge_base

# Verify setup
docker compose --profile setupdb run --rm db-setup python setup.py --verify
```

**6. Initialize vector store:**
```bash
docker compose --profile qdrant-setup run --rm qdrant-setup
```

**7. Start all services:**
```bash
cd ..  # Back to project root
docker compose up -d
```

**8. Verify services:**
```bash
docker compose ps
docker compose logs backend
docker compose logs frontend
```

Access points:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Mailpit UI**: http://localhost:8025

### Option B: Backend Only

If you only need the backend (API development, testing):

**1. Navigate to backend:**
```bash
cd rag-fortress/backend
```

**2. Build backend images:**
```bash
docker compose build
```
*Note: First build takes 3-10 minutes*

**3-7. Follow steps 3-7 from Option A** (all commands run from `backend/` directory)

Access points:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Mailpit UI: http://localhost:8025
- Health check: http://localhost:8000/health

### Option C: Frontend Only

If backend is already running elsewhere:

**1. Navigate to frontend:**
```bash
cd rag-fortress/frontend
```

**2. Build frontend image:**
```bash
docker compose build
```
*Note: First build takes 2-3 minutes*

**3. Configure API endpoint:**

Edit `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

**4. Start frontend:**
```bash
docker compose up -d
```

Access: http://localhost:3000

## Architecture

### Compose Structure

RAG Fortress uses a three-level Docker Compose setup:

| Level | Path | Purpose |
|-------|------|---------|
| **Root** | `/docker-compose.yml` | Full stack (backend + frontend) |
| **Backend** | `/backend/docker-compose.yml` | Backend services only |
| **Frontend** | `/frontend/docker-compose.yml` | Frontend only |

The root compose includes both backend and frontend using the `include` directive, allowing you to run:
- Full stack from `/`
- Backend independently from `/backend`
- Frontend independently from `/frontend`

### Services

| Service | Purpose | Port(s) |
|---------|---------|---------|
| **backend** | FastAPI application | 8000 |
| **frontend** | Vue.js + Nginx SPA | 3000 |
| **postgres** | PostgreSQL 18 database | 5432 (internal) |
| **redis** | Redis Stack for caching | 6379 (internal) |
| **qdrant** | Vector database | 6333, 6334 (internal) |
| **mailpit** | Email testing (SMTP + UI) | 1025, 8025 |

### Profiles

Utility services that run once then exit:

| Profile | Command | Purpose |
|---------|---------|---------|
| **keygen** | `--profile keygen run --rm keygen` | Generate Fernet encryption keys |
| **setupdb** | `--profile setupdb run --rm db-setup` | Run migrations + seeders |
| **qdrant-setup** | `--profile qdrant-setup run --rm qdrant-setup` | Initialize Qdrant collection |

### Volumes

Persistent data storage:

```
backend_data          # Uploaded files, vector store data
backend_logs          # Application logs
huggingface_cache     # Downloaded model weights
postgres_data         # Database files
redis_data            # Cache persistence
qdrant_data           # Vector database storage
```

## Configuration

### Environment Variables

Main configuration file: `backend/.env.docker`

**Required:**
```env
SECRET_KEY=<from keygen>
MASTER_ENCRYPTION_KEY=<from keygen>
SETTINGS_ENCRYPTION_KEY=<from keygen>
DB_PASSWORD=<your_password>
LLM_API_KEY=<your_api_key>
```

**Optional but recommended:**
```env
FALLBACK_LLM_API_KEY=<your_api_key>
CLASSIFIER_LLM_API_KEY=<your_api_key>
EMBEDDING_API_KEY=<if using external embeddings>
```

**Database (defaults provided):**
```env
DB_HOST=postgres
DB_PORT=5432
DB_NAME=rag_fortress
DB_USER=rag_fortress
```

**Email (uses Mailpit by default):**
```env
SMTP_HOST=mailpit
SMTP_PORT=1025
```

### Resource Limits

Default resource allocation:

| Service | Memory Limit | CPU Limit |
|---------|--------------|-----------|
| backend | 2GB | 2 cores |
| postgres | 1GB | 1 core |
| redis | 768MB | 0.5 cores |
| qdrant | 1.5GB | 1 core |
| mailpit | 256MB | 0.25 cores |

Adjust in `docker-compose.yml` under `deploy.resources` sections as needed.

## Docker Secrets (Production)

For production deployments, use Docker secrets instead of `.env.docker` for sensitive data.

### Setup

**1. Create secret files manually:**

Create a `secrets/` directory and add individual files (one secret per file, no newlines):

```powershell
# Windows PowerShell
cd backend
mkdir secrets
"your_secret_key_value" | Out-File -NoNewline -FilePath secrets/secret_key.txt
"your_master_encryption_key" | Out-File -NoNewline -FilePath secrets/master_encryption_key.txt
"your_settings_encryption_key" | Out-File -NoNewline -FilePath secrets/settings_encryption_key.txt
"your_db_password" | Out-File -NoNewline -FilePath secrets/db_password.txt
"your_llm_api_key" | Out-File -NoNewline -FilePath secrets/llm_api_key.txt
# Add other secrets as needed
```

```bash
# Linux/Mac
cd backend
mkdir -p secrets
echo -n 'your_secret_key_value' > secrets/secret_key.txt
echo -n 'your_master_encryption_key' > secrets/master_encryption_key.txt
echo -n 'your_settings_encryption_key' > secrets/settings_encryption_key.txt
echo -n 'your_db_password' > secrets/db_password.txt
echo -n 'your_llm_api_key' > secrets/llm_api_key.txt
# Add other secrets as needed

# Set permissions
chmod 600 secrets/*.txt
```

**2. Uncomment secrets in docker-compose.yml:**

Find and uncomment the `secrets:` sections in:
- `backend` service (lines ~133-145)
- `db-setup` service (lines ~74-76)
- `qdrant-setup` service (lines ~108-109)

**3. Remove sensitive values from .env.docker:**

Comment out or remove:
```env
# SECRET_KEY=...
# MASTER_ENCRYPTION_KEY=...
# SETTINGS_ENCRYPTION_KEY=...
# DB_PASSWORD=...
# LLM_API_KEY=...
```

**4. Restart services:**
```bash
docker compose up -d --force-recreate
```

### Available Secrets

All secrets are mounted at `/run/secrets/<name>` inside containers:

**Core:**
- `secret_key` (SECRET_KEY)
- `master_encryption_key` (MASTER_ENCRYPTION_KEY)
- `settings_encryption_key` (SETTINGS_ENCRYPTION_KEY)
- `db_password` (DB_PASSWORD)

**APIs:**
- `llm_api_key` (LLM_API_KEY)
- `fallback_llm_api_key` (FALLBACK_LLM_API_KEY)
- `classifier_llm_api_key` (CLASSIFIER_LLM_API_KEY)
- `internal_llm_api_key` (INTERNAL_LLM_API_KEY)
- `embedding_api_key` (EMBEDDING_API_KEY)
- `reranker_api_key` (RERANKER_API_KEY)
- `vector_db_api_key` (VECTOR_DB_API_KEY)

**Other:**
- `smtp_password` (SMTP_PASSWORD)
- `admin_password` (ADMIN_PASSWORD)

### Secret Files Security

```bash
# Verify permissions (Linux/Mac)
ls -la secrets/
# Should show: -rw------- (600)

# Set correct permissions if needed
chmod 600 secrets/*.txt
```

**Important:** Never commit secret files to version control. The `secrets/` directory is gitignored except for `.gitkeep`.

## Common Operations

**Note:** Commands below work from any directory with a `docker-compose.yml`:
- Root (`/`) - affects all services (backend + frontend)
- Backend (`/backend`) - affects backend services only
- Frontend (`/frontend`) - affects frontend only

### View logs
```bash
# All services (in current compose context)
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f frontend

# Last 100 lines
docker compose logs --tail=100 backend
```

### Restart services
```bash
# All services
docker compose restart

# Specific service
docker compose restart backend

# Force recreate (e.g., after config changes)
docker compose up -d --force-recreate backend
```

### Stop services
```bash
# Stop without removing
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove volumes (WARNING: deletes all data)
docker compose down -v
```

### Shell access
```bash
# Backend container
docker compose exec backend bash

# Postgres
docker compose exec postgres psql -U rag_fortress -d rag_fortress

# Redis
docker compose exec redis redis-cli
```

### Database operations
```bash
# Run migrations + all seeders (default)
docker compose --profile setupdb run --rm db-setup

# Migrations only
docker compose --profile setupdb run --rm db-setup python migrate.py

# All seeders
docker compose --profile setupdb run --rm db-setup python setup.py --all

# Specific seeders only (comma-separated)
docker compose --profile setupdb run --rm db-setup python setup.py --only-seeder admin,roles_permissions,settings

# Skip specific seeders
docker compose --profile setupdb run --rm db-setup python setup.py --skip-seeder demo_data,sample_documents

# Verify database setup
docker compose --profile setupdb run --rm db-setup python setup.py --verify

# List available seeders
docker compose --profile setupdb run --rm db-setup python setup.py --help

# Database shell
docker compose exec postgres psql -U rag_fortress -d rag_fortress

# Database backup
docker compose exec postgres pg_dump -U rag_fortress rag_fortress > backup.sql

# Database restore
cat backup.sql | docker compose exec -T postgres psql -U rag_fortress -d rag_fortress
```

### Rebuild after code changes
```bash
# Rebuild and restart
docker compose up -d --build

# Rebuild specific service
docker compose build backend
docker compose up -d backend
```

### Scale services (if needed)
```bash
# Not typically needed for RAG Fortress, but available:
docker compose up -d --scale backend=2
```