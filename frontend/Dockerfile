# syntax=docker/dockerfile:1.4

# ==============================================================================
# Stage 1: Build stage
# ==============================================================================
FROM node:24-alpine AS builder

WORKDIR /build

ARG VITE_API_BASE_URL=http://localhost:8000/api

# Copy package files (--link for better caching)
COPY --link package.json package-lock.json* ./

# Verify package-lock.json exists (frozen lockfile sanity check)
RUN test -f package-lock.json || (echo "ERROR: package-lock.json not found" && exit 1)

# Install all dependencies (including dev) needed for build
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy configuration files (--link for parallel copying)
COPY --link vite.config.js tailwind.config.js postcss.config.js index.html ./

# Copy source and public directories
COPY --link src ./src
COPY --link public ./public

# Build the application with environment variables (no .env copy needed - use ARG)
RUN VITE_API_BASE_URL=$VITE_API_BASE_URL npm run build

# ==============================================================================
# Stage 2: Production stage with Nginx
# ==============================================================================
FROM nginx:1.28-alpine AS production

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx configuration from source
COPY --link nginx.conf /etc/nginx/nginx.conf

# Copy built application from builder (--link for faster copy)
COPY --from=builder --link /build/dist /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3000

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
