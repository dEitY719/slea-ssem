# ==============================================================================
# SLEA-SSEM Unified Dockerfile
# Supports External (Public) and Internal (Corporate) Environments
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Frontend Builder
# ------------------------------------------------------------------------------
FROM node:18-alpine AS frontend-builder

ARG BUILD_FRONTEND=true
ARG NPM_REGISTRY=https://registry.npmjs.org/
ARG NPM_STRICT_SSL=true
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

# Proxy environment
ENV http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY}

WORKDIR /fe

# Certificate handling (certs/ 폴더 전체 복사 - 빈 폴더라도 OK)
COPY docker/certs/ /tmp/certs/
RUN if [ -d /tmp/certs/internal ] && [ "$(ls -A /tmp/certs/internal/*.crt 2>/dev/null)" ]; then \
        apk add --no-cache ca-certificates && \
        cp /tmp/certs/internal/*.crt /usr/local/share/ca-certificates/ && \
        update-ca-certificates; \
    fi
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates

# npm configuration
RUN npm config set registry ${NPM_REGISTRY} && \
    npm config set strict-ssl ${NPM_STRICT_SSL} && \
    if [ -n "${http_proxy}" ]; then \
        npm config set proxy ${http_proxy} && \
        npm config set https-proxy ${https_proxy}; \
    fi

# Frontend build (conditional)
COPY src/frontend/package*.json ./
RUN if [ "$BUILD_FRONTEND" = "true" ] && [ -f package.json ]; then \
        npm ci; \
    fi

COPY src/frontend/ ./
RUN if [ "$BUILD_FRONTEND" = "true" ] && [ -f package.json ]; then \
        npm run build; \
    else \
        mkdir -p dist; \
    fi


# ------------------------------------------------------------------------------
# Stage 2: Python Builder
# ------------------------------------------------------------------------------
FROM python:3.13-slim AS python-builder

ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=pypi.org pypi.python.org files.pythonhosted.org
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

# Proxy environment
ENV http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY} \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    tini \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Certificate handling
COPY docker/certs/ /tmp/certs/
RUN if [ -d /tmp/certs/internal ] && [ "$(ls -A /tmp/certs/internal/*.crt 2>/dev/null)" ]; then \
        mkdir -p /usr/local/share/ca-certificates/ && \
        cp /tmp/certs/internal/*.crt /usr/local/share/ca-certificates/ && \
        update-ca-certificates; \
    fi

# pip configuration
RUN mkdir -p /etc && \
    echo "[global]" > /etc/pip.conf && \
    echo "index-url = ${PIP_INDEX_URL}" >> /etc/pip.conf && \
    echo "trusted-host = ${PIP_TRUSTED_HOST}" >> /etc/pip.conf

# Python dependencies
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir .


# ------------------------------------------------------------------------------
# Stage 3: Runtime
# ------------------------------------------------------------------------------
FROM python:3.13-slim

ARG APP_VERSION="0.1.0"
ARG BUILD_FRONTEND=true

# Runtime environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    TZ=Asia/Seoul \
    PORT=8000 \
    HOST=0.0.0.0 \
    LOG_LEVEL=INFO \
    ENVIRONMENT=development

# Runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata \
    ca-certificates \
    curl \
    tini \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages and source
COPY --from=python-builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=python-builder /app ./

# Copy Frontend build (dist 폴더는 항상 존재 - 빌드 결과 또는 빈 폴더)
RUN mkdir -p ./src/backend/static
COPY --from=frontend-builder /fe/dist ./src/backend/static/

# Security: Non-root user
RUN useradd -u 1000 -m -s /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app && \
    chmod -R u+rwX,g+rX,o-rwx /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

# OCI Labels
LABEL org.opencontainers.image.title="slea-ssem-backend" \
      org.opencontainers.image.description="AI-driven learning platform (External + Internal)" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.created="2025-12-01"

# Entrypoint
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "python -m uvicorn src.backend.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}"]
