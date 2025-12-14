# Background Setup on Startup

## Overview

This feature allows the RAG Fortress server to start immediately in production environments (like PaaS platforms) without blocking on database setup. The server becomes operational right away and runs migrations/seeders in the background.

## How It Works

### Normal Startup (Default)
```bash
# ALLOW_SETUP_ON_START is false (default)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

1. Server attempts to initialize all services
2. If database is not ready, startup fails
3. Server does not start until everything is ready

### Background Setup Mode (Recommended for PaaS)
```bash
# Set environment variable
export ALLOW_SETUP_ON_START=true
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

1. Server starts **immediately**
2. Readiness state is set to `false`
3. Setup runs in background:
   - Database migrations
   - Essential seeders (admin, departments)
4. After setup completes, services are initialized
5. Readiness state is set to `true`
6. Server is now ready to handle traffic

### Skip Setup Mode
```bash
# When database is already set up
export SKIP_AUTO_SETUP=true
python run_production.py
```

1. Server starts normally
2. Skips migrations and seeders entirely
3. Initializes services immediately
4. Use when database is already configured

## Health Check Endpoints

### Liveness Probe: `/health`
- Returns `{"status": "ok"}` if server is running
- Use for container/process health checks
- Always returns 200 OK once server starts

### Readiness Probe: `/health/ready`
- Shows if application can handle traffic
- Use for load balancer readiness checks

**Responses:**

```json
// Ready to receive traffic
{
  "status": "ready",
  "message": "Application is ready to receive traffic",
  "version": "1.0.0"
}

// Setup running in background
{
  "status": "not_ready",
  "message": "Setup is running in background, please try again later",
  "version": "1.0.0"
}

// Setup failed
{
  "status": "error",
  "message": "Setup failed: Database migrations failed",
  "version": "1.0.0"
}

// Initial startup
{
  "status": "not_ready",
  "message": "Application is starting, please try again later",
  "version": "1.0.0"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOW_SETUP_ON_START` | `false` | Enable background setup mode |
| `SKIP_AUTO_SETUP` | `false` | Skip migrations/seeders entirely |
| `UVICORN_WORKERS` | `1` | Number of worker processes |
| `PORT` | `8000` | Server port |
| `HOST` | `0.0.0.0` | Server host |


## Benefits

✅ **Fast Startup** - Server responds to health checks immediately  
✅ **Zero Downtime** - New instances become ready gradually  
✅ **Better Resilience** - Temporary DB issues don't prevent startup  
✅ **PaaS Friendly** - Works with strict startup timeout platforms  
✅ **Production Ready** - Proper separation of liveness vs readiness
