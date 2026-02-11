# syntax=docker/dockerfile:1.4

# ==============================================================================
# Stage 1: Build stage with UV
# ==============================================================================
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /build

# Install build dependencies for compiling Python packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Set environment variables to force CPU-only packages
ENV CUDA_VISIBLE_DEVICES="" \
    TORCH_CUDA_ARCH_LIST="" \
    FORCE_CUDA="0" \
    PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu" \
    CMAKE_ARGS="-DLLAMA_CUBLAS=OFF -DLLAMA_METAL=OFF"

# Install dependencies from pyproject.toml with CPU-only packages
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache \
    --index-url https://pypi.org/simple \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    . && \
    uv pip install --system --no-cache --force-reinstall --no-deps \
    --index-url https://download.pytorch.org/whl/cpu \
    torch torchvision torchaudio 2>/dev/null || true
# ==============================================================================
# Stage 2: Runtime stage
# ==============================================================================
FROM python:3.13-slim-bookworm AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder (installed to system python)
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser migrations/ ./migrations/

# Copy setup scripts
COPY --chown=appuser:appuser migrate.py startup.py setup.py ./

# Copy data directory structure (will be overridden by volumes)
COPY --chown=appuser:appuser data/ ./data/

# Create logs directory
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/data /app/logs

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
