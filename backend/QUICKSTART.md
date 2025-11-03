# Quick Start Guide

## Running the Application

### Development Mode (with auto-reload)

```bash
cd backend
python run.py
```

### Production Mode (multiple workers)

```bash
cd backend
python run_production.py
```

### Using Uvicorn Directly

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

## Verify Application is Running

```bash
# Health check
curl http://localhost:8000/health

# Expected response
{"status": "healthy", "version": "1.0.0"}
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Available Endpoints

### Health Check
```
GET /health
```

### Background Ingestion
```
POST /api/v1/ingestion/start
GET  /api/v1/ingestion/status/{task_id}
GET  /api/v1/ingestion/tasks
```

## Startup Features

✅ **Automatic Initialization**
- Embedding provider initialized on startup
- Test requests verify services are working
- Fast startup time

✅ **Graceful Shutdown**
- Resources cleaned up properly
- No hanging connections

✅ **Health Monitoring**
- `/health` endpoint shows readiness status
- Logs show initialization progress

## Environment Variables

Key settings (from `.env` file):

```env
# Server
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["http://localhost:5173"]

# Data directories
PENDING_DIR=./data/knowledge_base/pending
PROCESSED_DIR=./data/knowledge_base/processed
```

## Common Issues

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Embeddings not loading
- Check your `.env` file has correct embedding settings
- Verify model files exist
- Check logs in `logs/rag_fortress.log`

## Next Steps

1. Place documents in `data/knowledge_base/pending/`
2. Start background ingestion: `POST /api/v1/ingestion/start`
3. Monitor progress: `GET /api/v1/ingestion/status/{task_id}`

See full documentation in `docs/` folder.
