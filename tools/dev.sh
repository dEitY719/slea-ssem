#!/usr/bin/env bash
set -euo pipefail

# slea-ssem development tool
# Auto-filled by generator (editable)
PY_RUN="uv run"
PY_TEST="uv run pytest -q"
UVICORN_ENTRY="src.backend.main:app"
USE_ALEMBIC=false
IS_DJANGO=false
MANAGE_PY="manage.py"
DEFAULT_DATASET="./data"
DEFAULT_PORT=8000
PORT=${PORT:-$DEFAULT_PORT}

cmd="${1:-help}"

case "$cmd" in
  up)
    echo "🔧 Starting dev server on port $PORT..."
    if $IS_DJANGO; then
      export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-"config.settings.dev"}
      $PY_RUN python "$MANAGE_PY" migrate
      $PY_RUN python "$MANAGE_PY" runserver 0.0.0.0:$PORT
    else
      if $USE_ALEMBIC; then
        $PY_RUN alembic upgrade head
      fi
      if [ -n "$UVICORN_ENTRY" ]; then
        APP_ENV=${APP_ENV:-dev} DATASET=${DATASET:-"$DEFAULT_DATASET"} \
        $PY_RUN uvicorn "$UVICORN_ENTRY" --reload --host 0.0.0.0 --port $PORT
      else
        echo "❌ No dev server configured. Edit tools/dev.sh to add your start command."
        exit 1
      fi
    fi
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

  *)
    cat <<'HELP'
Usage: ./tools/dev.sh <command>

Commands:
  up           Start dev server (uvicorn + DB init)
  down         Stop dev server (free port)
  test         Run test suite (pytest)
  format       Format + lint code (tox -e ruff)
  shell        Enter project shell
  cli          Start interactive CLI

Environment Variables:
  PORT         Server port (default: 8000)
               Example: PORT=8100 ./tools/dev.sh up
  DATASET      Dataset location (default: ./data)
               Example: DATASET=/path ./tools/dev.sh up
  APP_ENV      Environment (default: dev)
               Options: dev|staging|prod

Examples:
  ./tools/dev.sh up                 # Start on port 8000
  PORT=8100 ./tools/dev.sh up       # Start on port 8100
  PORT=8100 ./tools/dev.sh down     # Stop port 8100
  ./tools/dev.sh cli                # Start CLI

See CLAUDE.md for more.
HELP
    ;;
esac
