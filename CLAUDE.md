# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**slea-ssem**: AI-driven learning platform for S.LSI employees. Two-round adaptive testing with RAG-based dynamic question generation, LLM auto-scoring, and ranking system.

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Alembic (migrations)
- **Package Manager**: uv
- **Testing**: pytest
- **Code Quality**: ruff, black, mypy (strict), pylint

## Development

### Quick Start (3 Commands)

```bash
./tools/dev.sh up              # Start dev server (localhost:8000)
./tools/dev.sh test            # Run tests
./tools/dev.sh format          # Format + lint code
```

### Common Commands

```bash
./tools/dev.sh shell           # Enter project shell
./tools/dev.sh help            # Show all commands

tox -e py311                   # Test on Python 3.11
tox -e style                   # Full format/lint pipeline
```

## Testing

```bash
pytest                         # Run all tests
pytest -k <name>              # Run specific test
pytest -v                      # Verbose output
tox -e py310 py311 py312      # Test multiple versions
```

## Code Quality (Before Commit)

- [ ] `./tools/dev.sh format` passes (ruff, black, mypy, pylint)
- [ ] `./tools/dev.sh test` passes
- [ ] Type hints on all functions (mypy strict mode)
- [ ] Docstrings on public functions
- [ ] Line length ≤ 120 chars

## Git Workflow

```bash
./tools/commit.sh              # Interactive commit (Conventional Commits)
./tools/release.sh patch|minor|major  # Release & tag
```

**Commit types**: feat, fix, chore, refactor, test, docs
**Branch format**: `feature/name`, `fix/name`, `hotfix/name`

## Architecture

```text
Frontend ↔ Backend (FastAPI) ↔ PostgreSQL + LLM/RAG

Key Components:
- User Auth: Azure AD → Session management
- Tests: 2-round adaptive (difficulty adjusts based on score)
- Scoring: MC (exact match) + Short answer (LLM-based)
- Ranking: Global ranking + percentile + category breakdown
```

### Key Files

| Path | Purpose |
|------|---------|
| `src/backend/main.py` | FastAPI app entry (TBD) |
| `src/backend/api/` | Route handlers (TBD) |
| `src/backend/models/` | SQLAlchemy models (TBD) |
| `tests/` | pytest test suite |
| `docs/` | User scenarios, setup guides |
| `alembic/` | Database migrations |

## Data Schema (MVP 1.0)

**Key Entities**:

- `users`: id, ad_id (email), nickname (UNIQUE)
- `users_profile`: user_id (FK), level, career, interests
- `test_sessions`: user_id, round (1-2), status
- `test_questions`: session_id (FK), content, difficulty_level, category
- `test_responses`: session_id, question_id, user_answer, is_correct, score
- `test_results`: user_id, grade, total_score, rank, category_breakdown

## Conventions

**Variable Naming**: snake_case (Python)
**Constants**: UPPER_SNAKE_CASE
**Functions**: verb_noun (e.g., `get_user`, `create_session`)
**Classes**: PascalCase
**Async**: Prefix with `a_` if async function

## Troubleshooting

**Type errors?** Run `tox -e mypy` (strict mode enforced)
**Import errors?** Run `tox -e ruff` then `./tools/dev.sh format`
**DB issues?** Check `alembic/versions/` for migrations, then `./tools/dev.sh up`

## Further Reading

- **User Scenarios**: `docs/user_scenarios_mvp1.md`
- **Setup Template**: `docs/PROJECT_SETUP_PROMPT.md`
- **Contributing**: See git flow above + code quality rules

---

**Forcing Function Principle**: 3-4 intuitive commands (dev.sh, commit.sh, tox) reduce learning curve & execution variance. See `docs/PROJECT_SETUP_PROMPT.md` for details.
