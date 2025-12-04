# ============================================================
# SLEA-SSEM Makefile
# Docker 표준 템플릿 기반 개발 환경 관리
# 외부(집/공개망) + 사내(회사/폐쇄망) 환경 지원
# ============================================================

SHELL := /bin/bash
.ONESHELL:
.PHONY: help init init-internal build build-internal up up-internal down restart logs ps shell shell-db test lint type-check quality clean rebuild validate
.SILENT:

# ============================================================
# Configuration
# ============================================================

PROJECT_NAME := slea-ssem
DOCKER_DIR := docker

# Use 'docker compose' (v2) by default, fallback to 'docker-compose' (v1)
DC := $(shell command -v docker-compose >/dev/null 2>&1 && echo docker-compose || echo "docker compose")

# Environment (external or internal)
ENV ?= external

# Compose files (상대 경로 - docker/ 디렉토리 기준)
COMPOSE_BASE := -f docker-compose.yml
ifeq ($(ENV),internal)
	COMPOSE_FILES := $(COMPOSE_BASE) -f docker-compose.internal.yml
	ENV_FILE := .env.internal
	ENV_NAME := 사내 (폐쇄망)
else
	COMPOSE_FILES := $(COMPOSE_BASE)
	ENV_FILE := .env.example
	ENV_NAME := 외부 (공개망)
endif

# Service names (from docker-compose.yml)
BACKEND := slea-backend
DB := slea-db

# 색상
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m

# ============================================================
# Help (Default Target)
# ============================================================

help:
	@echo -e "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo -e "$(BLUE)$(PROJECT_NAME) - Docker 표준 템플릿$(NC)"
	@echo -e "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo -e "$(YELLOW)현재 환경: $(ENV_NAME)$(NC)"
	@echo ""
	@echo -e "$(GREEN)초기 설정:$(NC)"
	@echo "  make init              🔧 .env 파일 초기화 (외부)"
	@echo "  make init-internal     🔧 .env 파일 초기화 (사내)"
	@echo ""
	@echo -e "$(GREEN)Docker 관리:$(NC)"
	@echo "  make build             🔨 이미지 빌드 (외부/공개망)"
	@echo "  make build-internal    🔨 이미지 빌드 (사내/폐쇄망)"
	@echo "  make up                🚀 서비스 시작 (외부)"
	@echo "  make up-internal       🚀 서비스 시작 (사내)"
	@echo "  make down              🛑 서비스 정지"
	@echo "  make restart           🔄 재시작"
	@echo "  make rebuild           🆕 clean + build + up"
	@echo ""
	@echo -e "$(GREEN)로깅 & 모니터링:$(NC)"
	@echo "  make logs              📊 Backend 로그"
	@echo "  make ps                📋 서비스 목록"
	@echo "  make shell             💻 Backend 셸"
	@echo "  make shell-db          💻 Database 셸"
	@echo ""
	@echo -e "$(GREEN)개발 (TDD):$(NC)"
	@echo "  make test              🧪 테스트 (pytest)"
	@echo "  make lint              🔎 코드 검사 (ruff)"
	@echo "  make type-check        ✅ 타입 검사 (mypy)"
	@echo "  make quality           📈 전체 검사 (lint + type-check + test)"
	@echo ""
	@echo -e "$(GREEN)정리:$(NC)"
	@echo "  make clean             🧹 전체 캐시 삭제 (Python + Docker)"
	@echo ""
	@echo -e "$(GREEN)사용 예시 (외부 PC):$(NC)"
	@echo "  make init              # 1. 초기화"
	@echo "  make build             # 2. 빌드"
	@echo "  make up                # 3. 시작"
	@echo ""
	@echo -e "$(GREEN)사용 예시 (사내 PC):$(NC)"
	@echo "  make init-internal     # 1. 초기화"
	@echo "  make build-internal    # 2. 빌드 (프록시 자동 적용)"
	@echo "  make up-internal       # 3. 시작"
	@echo ""
	@echo -e "$(GREEN)고급 사용:$(NC)"
	@echo "  ENV=internal HTTP_PROXY= make build  # 사내 빌드 프록시 비우기"
	@echo "  ENV=external make up                 # 환경명 명시"
	@echo ""
	@echo -e "$(YELLOW)⚠️ 주의:$(NC)"
	@echo "  • 외부 PC: make build-internal 사용 금지 (프록시 연결 불가)"
	@echo "  • 사내 PC: GEMINI_API_KEY 경고는 정상 (빈값이 기본)"
	@echo "  • 자세한 정보: README.md 참조"
	@echo ""

# ============================================================
# 1. 초기 설정
# ============================================================

init:
	@echo -e "$(YELLOW)🔧 외부 환경 .env 파일 생성 중...$(NC)"
	@if [ ! -f $(DOCKER_DIR)/.env ]; then \
		cp $(DOCKER_DIR)/.env.example $(DOCKER_DIR)/.env; \
		echo -e "$(GREEN)✅ $(DOCKER_DIR)/.env 생성 완료 ($(DOCKER_DIR)/.env.example에서)$(NC)"; \
	else \
		echo -e "$(BLUE)ℹ️  $(DOCKER_DIR)/.env 파일이 이미 있습니다 (환경 변경 시: rm $(DOCKER_DIR)/.env && make init)$(NC)"; \
	fi

init-internal:
	@echo -e "$(YELLOW)🔧 사내 환경 .env 파일 생성 중...$(NC)"
	@if [ ! -f $(DOCKER_DIR)/.env.internal ]; then \
		cp $(DOCKER_DIR)/.env.internal.example $(DOCKER_DIR)/.env.internal; \
		echo -e "$(GREEN)✅ $(DOCKER_DIR)/.env.internal 생성 완료 ($(DOCKER_DIR)/.env.internal.example에서)$(NC)"; \
		echo -e "$(YELLOW)⚠️  인증서 복사 필요: cp assets/*.crt $(DOCKER_DIR)/certs/internal/$(NC)"; \
	else \
		echo -e "$(BLUE)ℹ️  $(DOCKER_DIR)/.env.internal 파일이 이미 있습니다 (환경 변경 시: rm $(DOCKER_DIR)/.env.internal && make init-internal)$(NC)"; \
	fi

# ============================================================
# 2. 빌드 (Proxy 자동 주입)
# ============================================================

# Pre-build validation (check required files exist)
validate:
	@echo -e "$(BLUE)✓ 빌드 전제조건 검사 중 ($(ENV_NAME))...$(NC)"
	@if [ ! -f pyproject.toml ]; then \
		echo -e "$(RED)❌ 오류: pyproject.toml 파일이 없습니다$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f README.md ]; then \
		echo -e "$(RED)❌ 오류: README.md 파일이 없습니다$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f Dockerfile ]; then \
		echo -e "$(RED)❌ 오류: Dockerfile이 없습니다$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f $(DOCKER_DIR)/docker-compose.yml ]; then \
		echo -e "$(RED)❌ 오류: $(DOCKER_DIR)/docker-compose.yml이 없습니다$(NC)"; \
		exit 1; \
	fi
	@if [ "$(ENV)" = "internal" ] && [ ! -f $(DOCKER_DIR)/docker-compose.internal.yml ]; then \
		echo -e "$(RED)❌ 오류: $(DOCKER_DIR)/docker-compose.internal.yml이 없습니다$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(GREEN)✅ 모든 파일 검증 완료$(NC)"

build: validate
	@echo -e "$(YELLOW)🔨 이미지 빌드 중 ($(ENV_NAME))...$(NC)"
	@if [ -f $(DOCKER_DIR)/$(ENV_FILE) ]; then \
		echo -e "$(BLUE)   - HTTP_PROXY: $$(grep -h '^HTTP_PROXY=' $(DOCKER_DIR)/$(ENV_FILE) | cut -d= -f2 || echo [미설정])$(NC)"; \
		echo -e "$(BLUE)   - PIP_INDEX_URL: $$(grep -h '^PIP_INDEX_URL=' $(DOCKER_DIR)/$(ENV_FILE) | cut -d= -f2 || echo [기본])$(NC)"; \
	fi
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) build; \
	else \
		$(DC) $(COMPOSE_FILES) build; \
	fi
	@echo -e "$(GREEN)✅ 빌드 완료$(NC)"

build-internal:
	@$(MAKE) build ENV=internal

# ============================================================
# 3. 실행 및 관리
# ============================================================

up:
	@echo -e "$(YELLOW)🚀 서비스 시작 중 ($(ENV_NAME))...$(NC)"
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) up -d; \
	else \
		$(DC) $(COMPOSE_FILES) up -d; \
	fi
	@sleep 2
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) ps; \
	else \
		$(DC) $(COMPOSE_FILES) ps; \
	fi
	@echo ""
	@echo -e "$(GREEN)✅ 시작 완료!$(NC)"
	@echo -e "$(BLUE)포트:$(NC)"
	@echo "  - Backend: http://localhost:8000"
	@echo "  - Database: localhost:5433"

up-internal:
	@$(MAKE) up ENV=internal

down:
	@echo -e "$(YELLOW)🛑 서비스 정지 중...$(NC)"
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) down; \
	else \
		$(DC) $(COMPOSE_FILES) down; \
	fi
	@echo -e "$(GREEN)✅ 정지 완료$(NC)"

restart:
	@echo -e "$(YELLOW)🔄 서비스 재시작 중 ($(ENV_NAME))...$(NC)"
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) restart; \
	else \
		$(DC) $(COMPOSE_FILES) restart; \
	fi
	@echo -e "$(GREEN)✅ 재시작 완료$(NC)"

rebuild: down build up
	@echo -e "$(GREEN)✅ 재구축 완료$(NC)"

# ============================================================
# 4. 로깅 & 모니터링
# ============================================================

logs:
	@echo -e "$(YELLOW)📊 Backend 로그 (실시간)$(NC)"
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) logs -f $(BACKEND); \
	else \
		$(DC) $(COMPOSE_FILES) logs -f $(BACKEND); \
	fi

ps:
	@echo -e "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo -e "$(BLUE)실행 중인 서비스 ($(ENV_NAME))$(NC)"
	@echo -e "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) ps; \
	else \
		$(DC) $(COMPOSE_FILES) ps; \
	fi

# ============================================================
# 5. 컨테이너 접속
# ============================================================

shell:
	@echo -e "$(YELLOW)💻 Backend 셸 접속$(NC)"
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) exec $(BACKEND) sh; \
	else \
		$(DC) $(COMPOSE_FILES) exec $(BACKEND) sh; \
	fi

shell-db:
	@echo -e "$(YELLOW)💻 Database 접속$(NC)"
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) exec $(DB) psql -U slea_user -d sleassem_dev; \
	else \
		$(DC) $(COMPOSE_FILES) exec $(DB) psql -U slea_user -d sleassem_dev; \
	fi

# ============================================================
# 6. 개발 (TDD)
# ============================================================

test:
	@echo -e "$(YELLOW)🧪 테스트 실행 중...$(NC)"
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) exec $(BACKEND) pytest tests/backend/ -v --tb=short; \
	else \
		$(DC) $(COMPOSE_FILES) exec $(BACKEND) pytest tests/backend/ -v --tb=short; \
	fi

lint:
	@echo -e "$(YELLOW)🔎 코드 검사 중 (Ruff)...$(NC)"
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) exec $(BACKEND) ruff check src tests; \
	else \
		$(DC) $(COMPOSE_FILES) exec $(BACKEND) ruff check src tests; \
	fi

type-check:
	@echo -e "$(YELLOW)✅ 타입 검사 중 (mypy strict)...$(NC)"
	cd $(DOCKER_DIR)
	@if [ "$(ENV)" = "internal" ]; then \
		$(DC) --env-file $(ENV_FILE) $(COMPOSE_FILES) exec $(BACKEND) mypy src --strict; \
	else \
		$(DC) $(COMPOSE_FILES) exec $(BACKEND) mypy src --strict; \
	fi

quality: lint type-check test
	@echo -e "$(GREEN)✅ 품질 검사 완료$(NC)"

# ============================================================
# 7. 정리
# ============================================================

clean:
	@echo -e "$(YELLOW)🧹 전체 캐시 정리 중 (Python + Docker)...$(NC)"
	@echo -e "$(BLUE)   • Python 캐시...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo -e "$(BLUE)   • Docker BuildKit 캐시...$(NC)"
	docker builder prune -af
	@echo -e "$(GREEN)✅ 전체 캐시 정리 완료$(NC)"

# ============================================================
# Default target
# ============================================================

.DEFAULT_GOAL := help
