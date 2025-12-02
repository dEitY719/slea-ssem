# ==============================================================================
# SLEA-SSEM Unified Dockerfile
# Supports External (Public) and Internal (Corporate) Environments
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Frontend Builder
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

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

# 인증서가 있으면 먼저 복사 (apk 실행 전)
RUN if [ -d /tmp/certs/internal ] && [ "$(ls -A /tmp/certs/internal/*.crt 2>/dev/null)" ]; then \
        mkdir -p /usr/local/share/ca-certificates/ && \
        cp /tmp/certs/internal/*.crt /usr/local/share/ca-certificates/; \
    fi

# HTTPS → HTTP로 변경 (사내 환경에서 인증서 검증 우회)
RUN if [ -n "${HTTP_PROXY}" ]; then \
        sed -i 's/https/http/g' /etc/apk/repositories; \
    fi

# npm configuration (인증서 설치 전에 먼저 설정)
RUN npm config set registry ${NPM_REGISTRY} && \
    npm config set strict-ssl ${NPM_STRICT_SSL}

# npm proxy 설정
RUN if [ -n "${http_proxy}" ]; then \
        npm config set proxy ${http_proxy} && \
        npm config set https-proxy ${https_proxy}; \
    fi

# ca-certificates 설치 (이제 HTTP로 접근)
RUN if [ -d /tmp/certs/internal ] && [ "$(ls -A /tmp/certs/internal/*.crt 2>/dev/null)" ]; then \
        apk add --no-cache ca-certificates && \
        update-ca-certificates; \
    fi

ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates

# Frontend build (conditional)
COPY src/frontend/ ./src/frontend/
RUN if [ "$BUILD_FRONTEND" = "true" ] && [ -f src/frontend/package.json ]; then \
        cd src/frontend && npm ci; \
    fi

RUN if [ "$BUILD_FRONTEND" = "true" ] && [ -f src/frontend/package.json ]; then \
        cd src/frontend && npm run build:prod; \
    else \
        mkdir -p src/frontend/dist; \
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

# apt proxy 설정 (사내 환경에서 필요)
RUN if [ -n "${HTTP_PROXY}" ]; then \
        echo "Acquire::http::Proxy \"${HTTP_PROXY}\";" > /etc/apt/apt.conf.d/proxy.conf && \
        echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" >> /etc/apt/apt.conf.d/proxy.conf; \
    fi

# Certificate handling (먼저 복사)
COPY docker/certs/ /tmp/certs/
RUN if [ -d /tmp/certs/internal ] && [ "$(ls -A /tmp/certs/internal/*.crt 2>/dev/null)" ]; then \
        mkdir -p /usr/local/share/ca-certificates/ && \
        cp /tmp/certs/internal/*.crt /usr/local/share/ca-certificates/ && \
        update-ca-certificates; \
    fi

# System dependencies (인증서 설치 후)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    tini \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

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

# apt proxy 설정 (사내 환경, build args는 여기서 사용 불가하므로 ENV 사용)
# Note: Runtime stage에서는 build args를 다시 선언해야 함
ARG HTTP_PROXY
ARG HTTPS_PROXY

RUN if [ -n "${HTTP_PROXY}" ]; then \
        echo "Acquire::http::Proxy \"${HTTP_PROXY}\";" > /etc/apt/apt.conf.d/proxy.conf && \
        echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" >> /etc/apt/apt.conf.d/proxy.conf; \
    fi

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
# Note: vite.config.ts에서 outDir: ../../dist로 설정되어 /fe/dist에 생성됨
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
