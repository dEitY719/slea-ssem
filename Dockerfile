# SLEA-SSEM Backend Docker Image
# Production-ready Dockerfile with multi-environment support
# 사외(공개) + 사내(폐쇄) 환경 모두 지원

# Base Image: Python 3.13 (pyproject.toml requires-python: >=3.13)
FROM python:3.13-slim AS builder

# ==================== BUILD-TIME ARGS ====================
# 빌드 시점 전용 설정 (이미지에 고정되지 않음)
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

# ==================== BUILD ENVIRONMENT SETUP ====================
# 프록시 설정 (소문자 env: apt-get, pip가 인식)
ENV http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    no_proxy=${NO_PROXY}

ENV DEBIAN_FRONTEND=noninteractive

# 시스템 의존성 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata \
    ca-certificates \
    curl \
    tini \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Pip 최신화
RUN python -m pip install --upgrade pip

# 작업 디렉토리
WORKDIR /app

# ==================== DEPENDENCIES INSTALLATION ====================
# 패키지 메타 및 소스 코드 복사 (순서: 빌드 캐시 최적화)
COPY pyproject.toml README.md ./
COPY src/ ./src/

# (선택) 사내 pip.conf 사용 시
# COPY ./pip.conf /etc/pip.conf

# 패키지 설치
RUN pip install --no-cache-dir .

# ==================== SOURCE CODE ====================
# 나머지 파일 복사 (설정, 문서, CI 등)
COPY . .

# (디버그용) 파일 확인
RUN ls -la /app/src/ && \
    python -c "import sys; print(f'Python {sys.version}')"

# ==================== RUNTIME IMAGE ====================
# 최종 이미지 (builder 결과물 최소 복사)
FROM python:3.13-slim

ARG APP_VERSION="0.1.0"

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

# Builder에서 설치된 Python 패키지 복사
# (또는 requirements.txt/uv.lock 있으면 재설치)
COPY --from=builder /app .
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# ==================== SECURITY: NON-ROOT USER ====================
# 비루트 사용자 생성 (호스트 UID 1000과 동일하게 설정해서 volume mount 접근 가능하게 함)
RUN useradd -u 1000 -m -s /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app && \
    chmod -R u+rwX,g+rX,o-rwx /app

USER appuser

# ==================== HEALTH CHECK ====================
# 헬스체크: 포트 연결 확인
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# ==================== PORT EXPOSURE ====================
# 포트 노출 (기본값)
EXPOSE ${PORT}

# ==================== OCI LABELS ====================
LABEL org.opencontainers.image.title="slea-ssem-backend" \
    org.opencontainers.image.description="AI-driven learning platform for S.LSI employees" \
    org.opencontainers.image.source="https://github.com/dEitY719/slea-ssem" \
    org.opencontainers.image.version="${APP_VERSION}" \
    org.opencontainers.image.created="2025-11-25"

# ==================== ENTRYPOINT & CMD ====================
# tini: PID 1 시그널 처리 (좀비 프로세스 방지)
ENTRYPOINT ["/usr/bin/tini", "--"]

# 기본 명령: FastAPI uvicorn 서버
# Shell form으로 환경변수 확장 가능하게 함 (exec form은 ${HOST} 리터럴로 전달됨)
CMD ["sh", "-c", "python -m uvicorn src.backend.main:app --host ${HOST:-127.0.0.1} --port ${PORT:-8000}"]
