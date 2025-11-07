# Repository Guidelines

## Project Structure & Module Organization

- `src/` holds the Python package scaffolding; extend `backend` for API services and `frontend` for client utilities, and keep shared interfaces in `src/__init__.py`.
- `tests/` mirrors the package layout (e.g., `tests/backend/test_example.py`) so new modules ship with matching pytest coverage.
- `docs/` captures specs and scenarios such as `docs/user_scenarios_mvp1.md`; sync code with the documented flows when requirements shift.
- `scripts/` and `tools/` provide automation; use `tools/dev.sh` for day-to-day tasks and keep generated artifacts in `build/`.

## Build, Test, and Development Commands

- `uv sync` installs dependencies declared in `pyproject.toml`/`uv.lock` into the active environment.
- `./tools/dev.sh up` launches the FastAPI dev server (`src.backend.main:app`) on `http://localhost:8000`, running Alembic upgrades when configured.
- `./tools/dev.sh test` runs the pytest suite (`pytest -q`); call this before committing.
- `tox -e ruff|mypy|py311` executes linting, type checks, and the Python 3.11 test matrix; `tox -e style` applies the full formatter stack.

## Coding Style & Naming Conventions

- Format Python with Black (120-char lines) and isort (`profile=black`); rely on `ruff` for lint + quick fixes.
- Keep strict typing intact: add type hints for public APIs and avoid unchecked `Any` usages.
- Use snake_case for modules and functions, CapWords for classes, and prefix tests with `test_`.
- Shell helpers must satisfy `shellcheck` and `shfmt -i 4` to stay CI-compliant.

## Testing Guidelines

- Write pytest functions named for behavior (`test_handles_invalid_payload`) and share fixtures via `tests/conftest.py`.
- Pair every feature or regression fix with tests that reflect the user journeys documented in `docs/`.
- Run `./tools/dev.sh test` locally and `tox -e py311` before opening a PR to match CI expectations.

## Commit & Pull Request Guidelines

- Follow the `type: summary` convention seen in history (`docs: ...`, `refactor: ...`), keeping subjects under ~72 characters.
- Bundle related changes together, including schema migrations or scripts they require.
- PRs should explain rationale, list validation evidence (pytest output, screenshots), and link issues or spec sections.
- Call out configuration or security impacts explicitly and request reviews from owners of the touched areas.

## Documentation & Knowledge Sharing

- Update `docs/` alongside code so onboarding references stay current; cite the exact file/section in PR discussions.
- Capture repeatable CLI workflows or troubleshooting steps in `README.md`/`README.en.md` to support new contributors.
