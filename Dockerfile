# ==================== STAGE 1: Frontend Build ====================
FROM node:20-alpine AS frontend-builder

ARG BUILD_FRONTEND=true
ARG NPM_REGISTRY=https://registry.npmjs.org/
ARG NPM_STRICT_SSL=true
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

ENV http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY}

WORKDIR /app

COPY docker/certs/ /tmp/certs/

RUN if [ -d /tmp/certs/internal ] && [ "$(ls -A /tmp/certs/internal/*.crt 2>/dev/null)" ]; then \
        mkdir -p /usr/local/share/ca-certificates/ && \
        cp /tmp/certs/internal/*.crt /usr/local/share/ca-certificates/; \
    fi

RUN if [ -n "${HTTP_PROXY}" ]; then \
        sed -i 's/https/http/g' /etc/apk/repositories; \
    fi

RUN npm config set registry ${NPM_REGISTRY} && \
    npm config set strict-ssl ${NPM_STRICT_SSL}

RUN if [ -n "${http_proxy}" ]; then \
        npm config set proxy ${http_proxy} && \
        npm config set https-proxy ${https_proxy}; \
    fi

RUN if [ -d /tmp/certs/internal ] && [ "$(ls -A /tmp/certs/internal/*.crt 2>/dev/null)" ]; then \
        apk add --no-cache ca-certificates && \
        update-ca-certificates; \
    fi

ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates

COPY src/frontend/package*.json ./src/frontend/
RUN if [ "$BUILD_FRONTEND" = "true" ] && [ -f src/frontend/package.json ]; then \
        cd src/frontend && npm ci; \
    fi

COPY src/frontend/ ./src/frontend/

RUN if [ "$BUILD_FRONTEND" = "true" ] && [ -f src/frontend/package.json ]; then \
        cd src/frontend && npm run build:prod; \
    else \
        mkdir -p src/frontend/dist; \
    fi

# ==================== STAGE 2: Backend Builder ====================
FROM python:3.13-slim AS backend-builder

# ==================== BUILD-TIME ARGS ====================
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=pypi.org pypi.python.org files.pythonhosted.org
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

# ==================== BUILD ENVIRONMENT SETUP ====================
ENV http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY} \
    DEBIAN_FRONTEND=noninteractive

RUN if [ -n "${HTTP_PROXY}" ]; then \
        echo "Acquire::http::Proxy \"${HTTP_PROXY}\";" > /etc/apt/apt.conf.d/proxy.conf && \
        echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" >> /etc/apt/apt.conf.d/proxy.conf; \
    fi

WORKDIR /app

COPY docker/certs/ /tmp/certs/
RUN if [ -d /tmp/certs/internal ] && [ "$(ls -A /tmp/certs/internal/*.crt 2>/dev/null)" ]; then \
        mkdir -p /usr/local/share/ca-certificates/ && \
        cp /tmp/certs/internal/*.crt /usr/local/share/ca-certificates/ && \
        update-ca-certificates; \
    fi

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    tini \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc && \
    echo "[global]" > /etc/pip.conf && \
    echo "index-url = ${PIP_INDEX_URL}" >> /etc/pip.conf && \
    echo "trusted-host = ${PIP_TRUSTED_HOST}" >> /etc/pip.conf

# ==================== DEPENDENCIES INSTALLATION ====================
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir .

# ==================== SOURCE CODE ====================
COPY . .

RUN ls -la /app/src/ && \
    python -c "import sys; print(f'Python {sys.version}')"

# ==================== RUNTIME IMAGE ====================
FROM python:3.13-slim

ARG APP_VERSION="0.1.0"
ARG HTTP_PROXY
ARG HTTPS_PROXY

# ==================== RUNTIME ENVIRONMENT ====================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    TZ=Asia/Seoul \
    PORT=8000 \
    HOST=0.0.0.0 \
    LOG_LEVEL=INFO \
    ENVIRONMENT=development

RUN if [ -n "${HTTP_PROXY}" ]; then \
        echo "Acquire::http::Proxy \"${HTTP_PROXY}\";" > /etc/apt/apt.conf.d/proxy.conf && \
        echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" >> /etc/apt/apt.conf.d/proxy.conf; \
    fi

# ==================== RUNTIME DEPENDENCIES ====================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata \
    ca-certificates \
    curl \
    tini \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend builder에서 설치된 Python 패키지 복사
COPY --from=backend-builder /app .
COPY --from=backend-builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Frontend builder에서 빌드된 정적 파일 복사
RUN mkdir -p ./src/backend/static
COPY --from=frontend-builder /app/dist ./src/backend/static/

# ==================== SECURITY: NON-ROOT USER ====================
RUN useradd -u 1000 -m -s /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app && \
    chmod -R u+rwX,g+rX,o-rwx /app

USER appuser

# ==================== HEALTH CHECK ====================
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# ==================== PORT EXPOSURE ====================
EXPOSE ${PORT}

# ==================== OCI LABELS ====================
LABEL org.opencontainers.image.title="slea-ssem-backend" \
    org.opencontainers.image.description="AI-driven learning platform for employees" \
    org.opencontainers.image.source="https://github.com/dEitY719/slea-ssem" \
    org.opencontainers.image.version="${APP_VERSION}" \
    org.opencontainers.image.created="2025-11-25"

# ==================== ENTRYPOINT & CMD ====================
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "python -m uvicorn src.backend.main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8000}"]
