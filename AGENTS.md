# Repository Guidelines

## Project Structure & Module Organization
- `src/` contains the Python package. Extend `src/backend` for API services (FastAPI entrypoint `src.backend.main:app`), `src/frontend` for client utilities, and keep shared contracts in `src/__init__.py`.
- `tests/` mirrors the package tree (`tests/backend/...`) so every module ships with matching pytest coverage.
- Place docs, specs, and user journeys in `docs/` (e.g., `docs/user_scenarios_mvp1.md`), and keep feature progress in `docs/progress/`.
- Automation lives in `scripts/` and `tools/`; day-to-day workflows use `tools/dev.sh`. Generated artifacts should land in `build/`.

## Build, Test, and Development Commands
- `uv sync` installs dependencies from `pyproject.toml`/`uv.lock` into the active environment.
- `./tools/dev.sh up` runs Alembic upgrades (when configured) and starts the FastAPI dev server on `http://localhost:8000`.
- `./tools/dev.sh test` executes the pytest suite (`pytest -q`); run before committing.
- `tox -e ruff|mypy|py311` performs linting, typing, and the Py3.11 test matrix; `tox -e style` applies full formatting.

## Coding Style & Naming Conventions
- Style Python with Black (120-char lines) and isort (`profile=black`); rely on Ruff for lint fixes.
- Maintain strict typing, avoid unchecked `Any`, and use snake_case for functions/modules, CapWords for classes.
- Shell helpers must pass `shellcheck` and `shfmt -i 4`.

## Testing Guidelines
- Write pytest functions named for behaviors (`test_handles_invalid_payload`).
- Share fixtures in `tests/conftest.py` and mirror new modules with matching tests.
- Acceptance flows should reflect scenarios in `docs/`; run `./tools/dev.sh test` locally followed by `tox -e py311` before PRs.

## Commit & Pull Request Guidelines
- Follow `type: summary` commit subjects (e.g., `docs: update workflow`), stay under ~72 chars, and bundle related schema/scripts.
- PRs must explain rationale, reference docs/spec sections, list validation evidence (pytest output, screenshots), and note config/security impacts.
- Tag AI-generated work per agent (e.g., 🤖 markers) when applicable, and request reviews from owners of touched areas.
