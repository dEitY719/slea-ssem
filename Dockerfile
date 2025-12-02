# ==================== STAGE 1: Frontend Build ====================
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

WORKDIR /app

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

# Copy frontend source
COPY src/frontend/package*.json ./src/frontend/
RUN if [ "$BUILD_FRONTEND" = "true" ] && [ -f src/frontend/package.json ]; then \
        cd src/frontend && npm ci; \
    fi

COPY src/frontend/ ./src/frontend/

# Build frontend (output to /app/dist via vite.config.ts ../../dist)
RUN if [ "$BUILD_FRONTEND" = "true" ] && [ -f src/frontend/package.json ]; then \
        cd src/frontend && npm run build:prod; \
    else \
        mkdir -p src/frontend/dist; \
    fi

# ==================== STAGE 2: Backend Builder ====================
# Base Image: Python 3.13 (pyproject.toml requires-python: >=3.13)
FROM python:3.13-slim AS backend-builder

# ==================== BUILD-TIME ARGS ====================
# 빌드 시점 전용 설정 (이미지에 고정되지 않음)
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=pypi.org pypi.python.org files.pythonhosted.org
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

# ==================== BUILD ENVIRONMENT SETUP ====================
# 프록시 설정 (소문자 env: apt-get, pip가 인식)
ENV http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY} \
    DEBIAN_FRONTEND=noninteractive

# apt proxy 설정 (사내 환경에서 필요)
RUN if [ -n "${HTTP_PROXY}" ]; then \
        echo "Acquire::http::Proxy \"${HTTP_PROXY}\";" > /etc/apt/apt.conf.d/proxy.conf && \
        echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" >> /etc/apt/apt.conf.d/proxy.conf; \
    fi

# 작업 디렉토리
WORKDIR /app

# Certificate handling (먼저 복사)
COPY docker/certs/ /tmp/certs/
RUN if [ -d /tmp/certs/internal ] && [ "$(ls -A /tmp/certs/internal/*.crt 2>/dev/null)" ]; then \
        mkdir -p /usr/local/share/ca-certificates/ && \
        cp /tmp/certs/internal/*.crt /usr/local/share/ca-certificates/ && \
        update-ca-certificates; \
    fi

# 시스템 의존성 설치 (인증서 설치 후)
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

# ==================== DEPENDENCIES INSTALLATION ====================
# 패키지 메타 및 소스 코드 복사 (순서: 빌드 캐시 최적화)
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Pip 최신화 및 패키지 설치
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir .

# ==================== SOURCE CODE ====================
# 나머지 파일 복사 (설정, 문서, CI 등)
# .dockerignore에서 .env 제외 (Docker 환경에서는 docker-compose.yml 환경변수 사용)
COPY . .

# (디버그용) 파일 확인
RUN ls -la /app/src/ && \
    python -c "import sys; print(f'Python {sys.version}')"

# ==================== RUNTIME IMAGE ====================
# 최종 이미지 (builder 결과물 최소 복사)
FROM python:3.13-slim

ARG APP_VERSION="0.1.0"
ARG HTTP_PROXY
ARG HTTPS_PROXY

# ==================== RUNTIME ENVIRONMENT ====================
# 런타임 기본 환경변수 (실제 값은 .env/docker-compose/docker run에서 오버라이드)
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
RUN if [ -n "${HTTP_PROXY}" ]; then \
        echo "Acquire::http::Proxy \"${HTTP_PROXY}\";" > /etc/apt/apt.conf.d/proxy.conf && \
        echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" >> /etc/apt/apt.conf.d/proxy.conf; \
    fi

# ==================== RUNTIME DEPENDENCIES ====================
# 런타임 필수 패키지만 설치
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
# Note: vite.config.ts에서 ../../dist로 설정되어 /app/dist에 생성됨
RUN mkdir -p ./src/backend/static
COPY --from=frontend-builder /app/dist ./src/backend/static/

# ==================== SECURITY: NON-ROOT USER ====================
# 비루트 사용자 생성 (호스트 UID 1000과 동일하게 설정해서 volume mount 접근 가능하게 함)
RUN useradd -u 1000 -m -s /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app && \
    chmod -R u+rwX,g+rX,o-rwx /app

USER appuser

# ==================== HEALTH CHECK ====================
# 헬스체크: 포트 연결 확인
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# ==================== PORT EXPOSURE ====================
# 포트 노출 (기본값)
EXPOSE ${PORT}

# ==================== OCI LABELS ====================
LABEL org.opencontainers.image.title="slea-ssem-backend" \
    org.opencontainers.image.description="AI-driven learning platform for employees" \
    org.opencontainers.image.source="https://github.com/dEitY719/slea-ssem" \
    org.opencontainers.image.version="${APP_VERSION}" \
    org.opencontainers.image.created="2025-11-25"

# ==================== ENTRYPOINT & CMD ====================
# tini: PID 1 시그널 처리 (좀비 프로세스 방지)
ENTRYPOINT ["/usr/bin/tini", "--"]

# 기본 명령: FastAPI uvicorn 서버
# Shell form으로 환경변수 확장 가능하게 함 (exec form은 ${HOST} 리터럴로 전달됨)
CMD ["sh", "-c", "python -m uvicorn src.backend.main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8000}"]
