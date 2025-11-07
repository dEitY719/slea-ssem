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

## REQ-Based Development Workflow (for MVP 1.0)

**When to use**: Each user request follows format: `"REQ-X-Y 기능 구현해"` (implement REQ X-Y)

### Command Format

```
User: "REQ-B-A2-Edit-1 기능 구현해"
Assistant: (Automatically follows 4-phase workflow below)
```

### Phase 1️⃣: SPECIFICATION (Parse & Pause for Review)

```
- Extract REQ ID, 요구사항, 우선순위, Acceptance Criteria from feature_requirement_mvp1.md
- Summarize: intent, constraints, performance goals
- Define: Location (module path), Signature (types, I/O, side effects),
  Behavior (logic, validation), Dependencies, Non-functional (perf/security)
- 🛑 PAUSE: Present spec, ask "Approved? Continue to Phase 2?"
```

### Phase 2️⃣: TEST DESIGN (TDD Before Code)

```
- Create: tests/<domain>/test_<feature>.py
- Design 4-5 test cases:
  ✓ Happy path (valid inputs)
  ✓ Input validation errors
  ✓ Edge cases (DB, timeout, concurrency)
  ✓ Acceptance criteria verification
- Include REQ ID in docstrings: # REQ: REQ-X-Y-Edit-1
- 🛑 PAUSE: Present test list, ask "Tests approved? Continue to Phase 3?"
```

### Phase 3️⃣: IMPLEMENTATION (Code to Spec)

```
- Write minimal code satisfying spec + tests
- Follow SOLID + conventions from above
- Run: tox -e style && pytest tests/<domain>/test_<feature>.py
- 🛑 STOP if validation fails; report errors
```

### Phase 4️⃣: SUMMARY (Report & Commit)

```
- Modified files + rationale
- Test results (all pass)
- Traceability: REQ → Spec → Tests → Code
- **Create progress file**: docs/progress/REQ-X-Y.md with full Phase 1-4 documentation
  * Include: Requirements, Implementation locations, Test results, Git commit
  * Add REQ traceability table (implementation ↔ test coverage)
- **Update progress tracking**: docs/DEV-PROGRESS.md
  * Find REQ row in developer section
  * Change Phase: 0 → 4
  * Change Status: ⏳ Backlog → ✅ Done
  * Update Notes: Add commit SHA (e.g., "Commit: f5412e9")
- Create git commit:
  * Format: "chore: Update progress tracking for REQ-X-Y completion"
  * Include: progress file creation + DEV-PROGRESS.md update
  * Tag with 🤖 Claude Code marker
```

**Key Principle**: Phase 1-2 pause for review = prevent rework. Spec must be approved before coding.
**Progress Tracking**: Always complete Phase 4 progress files to maintain audit trail & team visibility.

---

**Forcing Function Principle**: 3-4 intuitive commands (dev.sh, commit.sh, tox) reduce learning curve & execution variance. See `docs/PROJECT_SETUP_PROMPT.md` for details.
