# syntax=docker/dockerfile:1.4

# ==============================================================================
# Stage 1: Builder - Install dependencies
# ==============================================================================
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Build argument for optional extras (cpu, gpu, llamacpp)
# Default: cpu (HuggingFace embeddings)
# Override: docker build --build-arg UV_EXTRAS="cpu llamacpp" .
ARG UV_EXTRAS="cpu"

ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /build

# Install build dependencies needed for compiling packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev

# Copy dependency files (--link for better caching)
COPY --link pyproject.toml uv.lock ./

# Install dependencies to /opt/venv (configured via UV_PROJECT_ENVIRONMENT)
# Use UV_EXTRAS build arg to control optional dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -n "$UV_EXTRAS" ]; then \
        for extra in $UV_EXTRAS; do \
            EXTRA_FLAGS="$EXTRA_FLAGS --extra $extra"; \
        done; \
        uv sync --frozen --no-install-project --no-dev $EXTRA_FLAGS; \
    else \
        uv sync --frozen --no-install-project --no-dev; \
    fi

# Verify uvicorn was installed
RUN test -f /opt/venv/bin/uvicorn || (echo "ERROR: uvicorn not installed" && exit 1)

# ==============================================================================
# Stage 2: Runtime - Minimal production image
# ==============================================================================
FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV=/opt/venv \
    HF_HOME=/app/.cache/huggingface

# Install runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl

# Create non-root user with home directory
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 -m -d /home/appuser appuser

WORKDIR /app

# Copy virtual environment from builder (same path to preserve shebangs)
COPY --from=builder --link /opt/venv /opt/venv

# Copy application code (files that need chown cannot use --link)
COPY --from=builder --chown=appuser:appuser /build/pyproject.toml /build/uv.lock ./
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser migrations/ ./migrations/
COPY --chown=appuser:appuser generate_fernet_key.py migrate.py startup.py setup.py init_qdrant.py ./
COPY --chown=appuser:appuser data/ ./data/
COPY --chown=appuser:appuser app/ ./app/

# Create logs and cache directories
RUN mkdir -p /app/logs /app/.cache/huggingface && \
    chown -R appuser:appuser /app/data /app/logs /app/.cache

# Switch to non-root user
USER appuser

EXPOSE 8000

# Run the application (migrations happen in startup lifespan)
CMD ["/opt/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
