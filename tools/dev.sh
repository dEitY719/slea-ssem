#!/usr/bin/env bash
set -euo pipefail

# slea-ssem development tool
# Auto-filled by generator (editable)

# Prefer uv if available; fallback to python
if command -v uv >/dev/null 2>&1; then
  PY_RUN="uv run"
  PY_TEST="uv run pytest -q"
else
  PY_RUN="python"
  PY_TEST="python -m pytest -q"
fi
UVICORN_ENTRY="src.backend.main:app"
USE_ALEMBIC=false
IS_DJANGO=false
MANAGE_PY="manage.py"
DEFAULT_DATASET="./data"
DEFAULT_PORT=8000
DEFAULT_LOG_LEVEL=${LOG_LEVEL:-INFO}
DEFAULT_LOG_FILE=${LOG_FILE:-false}
PORT=${PORT:-$DEFAULT_PORT}

cmd="${1:-help}"

case "$cmd" in
  up)
    target="${2:-b}" # Default to backend
    # Parse optional KEY=VALUE overrides (e.g., LOG_LEVEL=DEBUG LOG_FILE=true)
    if [ "$#" -ge 3 ]; then
      shift 2
      for kv in "$@"; do
        if [[ "$kv" == *=* ]]; then
          export "${kv?}"
        fi
      done
    fi
    LOG_LEVEL=${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}
    LOG_FILE=${LOG_FILE:-$DEFAULT_LOG_FILE}

    case "$target" in
      b|backend)
        echo "🔧 Starting backend dev server on port $PORT..."
        echo "   LOG_LEVEL=${LOG_LEVEL}"
        echo "   LOG_FILE=${LOG_FILE}"

        # Optional file logging (Phase1 debug)
        LOG_DIR="logs/phase1_debug"
        PHASE1_LOG_PATH=""
        if [ "${LOG_FILE,,}" = "true" ]; then
          mkdir -p "$LOG_DIR"
          TS=$(date +%Y%m%d_%H%M%S)
          MODEL_SAFE=$(echo "${LITELLM_MODEL:-backend}" | tr '/-' '__')
          PHASE1_LOG_PATH="${LOG_DIR}/${MODEL_SAFE}_${TS}.log"
          echo "   Writing logs to ${PHASE1_LOG_PATH}"
          # Clear file to start fresh
          > "$PHASE1_LOG_PATH"
        fi

        if $IS_DJANGO; then
          export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-"config.settings.dev"}
          $PY_RUN python "$MANAGE_PY" migrate
          $PY_RUN python "$MANAGE_PY" runserver 0.0.0.0:$PORT
        else
          if $USE_ALEMBIC; then
            $PY_RUN alembic upgrade head
          fi
          if [ -n "$UVICORN_ENTRY" ]; then
            APP_ENV=${APP_ENV:-dev} DATASET=${DATASET:-"$DEFAULT_DATASET"}

            # Get absolute path to logging config
            SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
            LOG_CONFIG="${SCRIPT_DIR}/logging_config.yaml"

            # Build Uvicorn command with logging config for clean output
            UVICORN_CMD=(
              $PY_RUN uvicorn
              "$UVICORN_ENTRY"
              --reload
              --host 127.0.0.1
              --port "$PORT"
              --log-level "${LOG_LEVEL,,}"
              --log-config "$LOG_CONFIG"
            )

            if [ "${LOG_FILE,,}" = "true" ]; then
              # Export log path for app to use (Phase-1-Debug logging)
              export PHASE1_LOG_PATH
              # Capture clean logs (color codes removed by logging config)
              # shellcheck disable=SC2068
              "${UVICORN_CMD[@]}" 2>&1 | tee "$PHASE1_LOG_PATH"
            else
              # shellcheck disable=SC2068
              "${UVICORN_CMD[@]}"
            fi
          else
            echo "❌ No dev server configured. Edit tools/dev.sh to add your start command."
            exit 1
          fi
        fi
        ;;
      f|frontend)
        echo "🎨 Starting frontend dev server..."
        if [ -d "src/frontend" ]; then
            (cd src/frontend && npm run dev)
        else
            echo "❌ src/frontend directory not found."
            exit 1
        fi
        ;;
      *)
        echo "❌ Invalid target for 'up': '$target'. Use 'b' (backend) or 'f' (frontend)."
        exit 1
        ;;
    esac
    ;;

  test)
    echo "🧪 Running tests..."
    $PY_TEST
    ;;

  fmt|format)
    echo "🖤 Format + lint (tox -e ruff)..."
    if command -v tox >/dev/null 2>&1; then
      tox -e ruff
    else
      echo "❌ tox not found. Install: uv pip install tox"
      exit 1
    fi
    ;;

  shell)
    echo "🐚 Entering project shell..."
    if command -v uv >/dev/null 2>&1; then
      exec uv run bash
    else
      echo "❌ uv not found. Activate virtualenv manually."
      exit 1
    fi
    ;;

  cli)
    echo "🖥️  Starting interactive CLI..."
    $PY_RUN python run.py
    ;;

  down)
    echo "🛑 Stopping dev server on port $PORT..."
    # Find and kill processes using specified port
    if command -v lsof >/dev/null 2>&1; then
      PIDS=$(lsof -ti :$PORT 2>/dev/null || true)
      if [ -n "$PIDS" ]; then
        echo "$PIDS" | xargs kill -9 2>/dev/null || true
        sleep 1
        echo "✅ Dev server stopped (port $PORT freed)"
      else
        echo "ℹ️  No process running on port $PORT"
      fi
    else
      # Fallback: kill uvicorn processes
      echo "⚠️  lsof not available. Killing all uvicorn processes..."
      pkill -9 uvicorn 2>/dev/null || echo "ℹ️  No uvicorn process found"
    fi
    ;;

  clean)
    echo "🧹 Cleaning Python cache..."
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    find . -type f -name "*.pyd" -delete 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    echo "✅ Python cache cleaned"
    ;;

  *)
    cat <<'HELP'
Usage: ./tools/dev.sh <command> [target]

Commands:
  up [b|f]     Start dev server (b: backend (default), f: frontend)
  down         Stop dev server (free port)
  test         Run test suite (pytest)
  format       Format + lint code (tox -e ruff)
  clean        Clean Python cache (__pycache__, *.pyc, etc)
  shell        Enter project shell
  cli          Start interactive CLI

Environment Variables:
  PORT         Server port (default: 8000)
               Example: PORT=8100 ./tools/dev.sh up
  DATASET      Dataset location (default: ./data)
               Example: DATASET=/path ./tools/dev.sh up
  APP_ENV      Environment (default: dev)
               Options: dev|staging|prod
  LOG_LEVEL    Uvicorn log level (default: INFO)
               Example: LOG_LEVEL=DEBUG ./tools/dev.sh up b
  LOG_FILE     true|false (default: false). When true, backend log is written to logs/phase1_debug/<model>_<timestamp>.log

Examples:
  ./tools/dev.sh up                 # Start backend on http://localhost:8000
  ./tools/dev.sh up b               # Explicitly start backend
  ./tools/dev.sh up f               # Start frontend dev server
  PORT=8100 ./tools/dev.sh up       # Start backend on http://localhost:8100
  PORT=8100 ./tools/dev.sh down     # Stop port 8100
  ./tools/dev.sh cli                # Start CLI
  ./tools/dev.sh clean              # Clean Python cache (before restarting CLI)

See CLAUDE.md for more.
HELP
    ;;
esac
