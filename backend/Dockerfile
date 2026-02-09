# syntax=docker/dockerfile:1.4

# ==============================================================================
# Stage 1: Build stage with UV
# ==============================================================================
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /build

# Copy dependency files first for better caching
COPY pyproject.toml ./
COPY requirements.txt ./

# Install dependencies using UV (much faster than pip)
# --no-cache to keep the image small
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -r requirements.txt

# ==============================================================================
# Stage 2: Runtime stage
# ==============================================================================
FROM python:3.13-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Disable pip version check
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # UV cache
    UV_CACHE_DIR=/tmp/uv-cache

# Install runtime dependencies only (security updates and essential tools)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    # For PostgreSQL
    libpq5 \
    # For health checks
    curl \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser migrations/ ./migrations/

# Create necessary directories with proper permissions
RUN mkdir -p /app/data/files/knowledge_base \
    /app/data/vector_store \
    /app/data/error_reports \
    /app/logs \
    && chown -R appuser:appuser /app/data /app/logs

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
