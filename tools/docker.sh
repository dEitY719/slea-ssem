#!/usr/bin/env bash
# ==============================================================================
# SLEA-SSEM Docker 관리 스크립트
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

usage() {
    cat <<EOF
Usage: $0 <command> [environment]

Commands:
    up          Start services
    down        Stop services
    restart     Restart services
    logs        Show logs
    ps          Show running containers
    clean       Remove all containers, volumes, images

Environment:
    external    외부 환경 (집/공개망) - 기본값
    internal    사내 환경 (회사/폐쇄망)

Examples:
    $0 up                # 외부 환경으로 시작
    $0 up internal       # 사내 환경으로 시작
    $0 down              # 중단
    $0 logs              # 로그 확인

EOF
    exit 1
}

# Parse arguments
COMMAND=${1:-}
ENV=${2:-external}

# Validate command
[[ -z "$COMMAND" ]] && usage

# Validate environment
if [[ "$ENV" != "external" && "$ENV" != "internal" ]]; then
    error "Invalid environment: $ENV (use 'external' or 'internal')"
fi

# Compose files
COMPOSE_BASE="-f docker-compose.yml"
COMPOSE_FILES="$COMPOSE_BASE"

if [[ "$ENV" == "internal" ]]; then
    COMPOSE_FILES="$COMPOSE_BASE -f docker-compose.internal.yml"
fi

# Change to docker directory
cd "$DOCKER_DIR"

# Check .env file
if [[ ! -f .env ]]; then
    warn ".env file not found. Creating from example..."
    if [[ "$ENV" == "internal" ]]; then
        cp .env.internal.example .env
        info "Created .env from .env.internal.example"
    else
        cp .env.example .env
        info "Created .env from .env.example"
    fi
fi

# Execute command
case "$COMMAND" in
    up)
        info "Starting services ($ENV environment)..."
        docker-compose $COMPOSE_FILES up --build -d
        info "Services started. Check: http://localhost:8000/health"
        ;;
    down)
        info "Stopping services..."
        docker-compose $COMPOSE_FILES down
        ;;
    restart)
        info "Restarting services ($ENV environment)..."
        docker-compose $COMPOSE_FILES restart
        ;;
    logs)
        info "Showing logs (Ctrl+C to exit)..."
        docker-compose $COMPOSE_FILES logs -f
        ;;
    ps)
        docker-compose $COMPOSE_FILES ps
        ;;
    clean)
        warn "This will remove all containers, volumes, and images. Continue? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            docker-compose $COMPOSE_FILES down -v --rmi all
            info "Cleaned up successfully"
        else
            info "Cancelled"
        fi
        ;;
    *)
        error "Unknown command: $COMMAND"
        usage
        ;;
esac
