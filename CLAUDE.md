# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**slea-ssem**: AI-driven learning platform for employees. Two-round adaptive testing with RAG-based dynamic question generation, LLM auto-scoring, and ranking system.

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Alembic (migrations)
- **Package Manager**: uv
- **Testing**: pytest
- **Code Quality**: ruff, black, mypy (strict), pylint

## Development

### Quick Start (4 Commands)

```bash
./tools/dev.sh up              # Start dev server (localhost:8000)
./tools/dev.sh down            # Stop dev server (free port)
./tools/dev.sh test            # Run tests
./tools/dev.sh format          # Format + lint code
```

### Common Commands

```bash
./tools/dev.sh cli             # Start interactive CLI
./tools/dev.sh shell           # Enter project shell
./tools/dev.sh help            # Show all commands

tox -e py311                   # Test on Python 3.11
tox -e style                   # Full format/lint pipeline
```

### Server Management with Custom Port

```bash
PORT=8100 ./tools/dev.sh up    # Start on port 8100
PORT=8100 ./tools/dev.sh down  # Stop port 8100 server
```

**Notes**:

- Default port: 8000 (can override with `PORT` env var)
- `down` automatically finds and kills the server on specified port
- `down` works with or without `lsof` command available

### Package Management

**When installing new packages during development**:

```bash
uv add <package-name>          # Add to [project] dependencies
uv add --dev <package-name>    # Add to dev dependencies
```

This automatically updates `pyproject.toml` and `uv.lock`. **Do NOT manually edit pyproject.toml for dependencies** — always use `uv add`.

## Testing

### Test Suite Structure

```
tests/
├── backend/          # Backend service & API tests (RECOMMENDED ✅)
├── agent/            # AI Agent integration tests (optional)
└── cli/              # CLI command tests (optional)
```

**Total tests**: ~775 tests (backend: ~300, agent: ~200, cli: ~275)

### Quick Test Guide

```bash
# ✅ RECOMMENDED: Run backend tests only (fast, covers most cases)
pytest tests/backend/ -v

# ✅ Run specific backend test file
pytest tests/backend/test_question_gen_service_retake.py -v

# ✅ Run specific test by name
pytest tests/backend/ -k test_retake -v

# ⏭️ OPTIONAL: Run agent integration tests (slower)
pytest tests/agent/ -v

# ⏭️ OPTIONAL: Run CLI tests (slower)
pytest tests/cli/ -v

# ❌ AVOID: Full test suite (775 tests, very slow ~10+ mins)
pytest                         # Don't use - too many tests
pytest -k <name>              # Run specific test
pytest -v                      # Verbose output
tox -e py310 py311 py312      # Test multiple versions (developer only)
```

### When to Run Which Tests

| Scenario | Command | Duration |
|----------|---------|----------|
| **After code changes** | `pytest tests/backend/ -v` | ~2-3 min |
| **Before commit** | `pytest tests/backend/ -v` | ~2-3 min |
| **Specific feature testing** | `pytest tests/backend/ -k feature_name` | ~30 sec |
| **Agent integration debugging** | `pytest tests/agent/ -v` | ~3-5 min |
| **CLI command testing** | `pytest tests/cli/ -v` | ~3-5 min |
| **Full validation** (developer only) | `tox -e py311` | ~15+ min |

### Best Practices

- ✅ Always run `pytest tests/backend/ -v` before committing
- ✅ Use `-k` flag to run specific tests: `pytest tests/backend/ -k retake`
- ✅ Use `--tb=short` for cleaner error output: `pytest tests/backend/ -v --tb=short`
- ❌ Don't run full `pytest` without arguments (775 tests = very slow)
- ❌ Don't run agent/cli tests unless debugging those specific features

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

### Rich Console Markup Issues

**Problem**: When printing usage strings with square brackets like `[level]`, `[years]`, Rich Console interprets them as markup tags and removes them.

```python
# ❌ Wrong: Will output "Usage: cmd [--option]" (brackets removed)
console.print("Usage: cmd [level] [years] [--option VALUE]")

# ✅ Correct: Use markup=False parameter
console.print("Usage: cmd [level] [years] [--option VALUE]", markup=False)

# ✅ Also correct: Escape with double brackets
console.print("Usage: cmd [[level]] [[years]] [--option VALUE]")
```

**When to use**:

- Use `markup=False` when printing usage/help text with square brackets (cleaner)
- Use `[[...]]` when you need markup enabled elsewhere but want literal brackets

**Cache after changes**: Run `./tools/dev.sh clean` before testing CLI changes, as Python caches compiled modules.

---

## LLM-Based Development Guidelines

### Quick Summary

When working with LLM prompts and LangChain, **always separate content from template logic**. Mixing them causes escaping nightmares when you add JSON examples to prompts.

**Key Pattern**:

```python
# ✅ CORRECT: Use SystemMessage, not from_template()
system_message = SystemMessage(content=prompt_text)  # {} stays as plain text
return ChatPromptTemplate.from_messages([system_message, ...])

# ❌ WRONG: from_template() interprets {} as variables
ChatPromptTemplate.from_template(prompt_text)  # JSON needs escaping!
```

### Two Critical Issues Learned the Hard Way

#### 1. ReAct Format Completeness (LiteLLM Issue)

- **Problem**: LLM sometimes skips Action Input or Observation fields
- **Root Cause**: High temperature (0.7) + vague prompt instructions
- **Solution**: Use temperature 0.3 + explicit format requirements
- **Reference**: `docs/postmortem-litellm-no-tool-results.md`

#### 2. JSON Escaping in Prompts (Template Logic Issue)

- **Problem**: `{"user_id": "..."}` in prompt → interpreted as template variable
- **Root Cause**: Mixing content and logic; using `from_template()`
- **Solution**: SOLID-based refactoring (Builder + Factory patterns)
- **Reference**: `docs/postmortem-prompt-escaping-solid-refactoring.md`

### SOLID-Based Solution (Condensed)

**File Structure**:

```
src/agent/prompts/
├── prompt_content.py  (pure text, no escaping!)
├── prompt_builder.py  (Builder + Factory patterns)
└── react_prompt.py    (simple API via factory delegation)
```

**Key Code Pattern**:

```python
# Content: Just plain text, no escaping needed
def get_system_prompt() -> str:
    parts = [
        "Your role...",
        REACT_FORMAT_RULES,
        "Action Input: {\"user_id\": \"...\"}",  # ✅ Natural JSON!
        "Instructions...",
    ]
    return "\n".join(parts)

# Template: Uses SystemMessage, not from_template()
class ReactPromptBuilder(PromptBuilder):
    def build(self) -> ChatPromptTemplate:
        system_prompt = get_system_prompt()  # Pure text
        system_message = SystemMessage(content=system_prompt)  # No {} interpretation!
        return ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="messages"),
        ])
```

### Checklist for Future LLM Projects

When adding LLM prompts to ANY project:

- [ ] **Separate content and logic**: Different files, never mix
- [ ] **Use SystemMessage**: `SystemMessage(content=...)` NOT `from_template()`
- [ ] **No escaping needed**: If you're using `{{`, you're doing it wrong
- [ ] **Apply Builder + Factory**: For flexibility and testability
- [ ] **Document the architecture**: Reference PROMPT_SOLID_REFACTORING.md

### Complete Documentation & Analysis

For full details with implementation examples and analysis, read these postmortem documents:

1. **`docs/postmortem-litellm-no-tool-results.md`** (25 min read)
   - "No tool results extracted!" error deep analysis
   - Temperature impact on consistency with data
   - Phase 1-4 improvement roadmap
   - Why LiteLLM differs from native Gemini API
   - Key insights for future projects

2. **`docs/postmortem-prompt-escaping-solid-refactoring.md`** (30 min read)
   - JSON escaping problem explanation with real examples
   - Complete SOLID-based solution
   - Builder + Factory pattern implementation
   - Future extension examples (conditional content, custom builders)
   - Prevention checklist

3. **`docs/PROMPT_SOLID_REFACTORING.md`** (Complete Implementation Reference)
   - Before/after architecture comparison
   - Full file structure with complete code
   - Testing results and verification
   - SOLID principles breakdown with code examples
   - Future improvements roadmap

---

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

## CLI Feature Requirement Workflow

**When to use**: CLI 기능 추가/개선할 때, 모든 feature는 requirement 먼저 정의

### Step 1: Requirement 작성

**파일**: `docs/CLI-FEATURE-REQUIREMENTS.md`에 다음 포맷으로 추가

**포맷**: `REQ-CLI-[DOMAIN]-[NUMBER]`

- Domain: auth, survey, profile, questions, session, export, ...
- Number: 도메인 내 순번 (1, 2, 3, ...)

**템플릿**:

```markdown
### REQ-CLI-[DOMAIN]-[NUMBER]: [기능명]

**Description**:
한 문장 요약

상세 설명 (2-3줄)

**사용 예**:
```bash
> command [args]
✓ success output
```

**기대 출력**:

- 성공: 메시지 + 데이터
- 실패: 에러 메시지

**에러 케이스**:

- Not authenticated → "Please login first"
- API error → 상세 에러 메시지
- Invalid input → Usage 가이드

**Acceptance Criteria**:

- [ ] 명령어 정확 작동
- [ ] 에러 처리 완벽
- [ ] 도움말 명확

**Priority**: M/H/L
**Dependencies**: [API / Module]
**Status**: ⏳ Backlog

```

### Step 2-5: REQ-Based Workflow 적용

**Phase 1-4는 기존 CLAUDE.md의 REQ-Based Development Workflow과 동일**

```

REQ-CLI-AUTH-1 기능 구현해
↓
Phase 1: 요구사항 검토 → Approve?
Phase 2: 테스트 설계 → Approve?
Phase 3: 구현 + 검증
Phase 4: Commit + Progress tracking

```

### CLI Feature 발견 및 추가 방법

**방법: 즉시 추가 (권장)**

```

사용자: "CLI에 세션 저장 기능이 필요해"
↓

1. docs/CLI-FEATURE-REQUIREMENTS.md에 REQ-CLI-SESSION-1 추가
2. Requirement 정의 (5분)
3. "REQ-CLI-SESSION-1 기능 구현해" 요청
4. Claude가 4단계 Workflow 적용

```

### CLI Requirement 관리

**조직**:
- `docs/CLI-FEATURE-REQUIREMENTS.md`: 모든 CLI 요구사항 통합 관리
- `docs/DEV-PROGRESS.md`: CLI 섹션에 진행 상황 추적
- `docs/progress/REQ-CLI-*.md`: 각 기능별 Phase 4 documentation

**진행 추적**:
- Phase 4 완료 시:
  1. `docs/CLI-FEATURE-REQUIREMENTS.md`에서 Status: ✅ Done 변경
  2. `docs/DEV-PROGRESS.md`의 CLI 섹션에서 Phase 4로 변경
  3. Commit SHA 기록

---

**Forcing Function Principle**: 3-4 intuitive commands (dev.sh, commit.sh, tox) reduce learning curve & execution variance. See `docs/PROJECT_SETUP_PROMPT.md` for details.

---

## 🎯 CURRENT STATUS & NEXT TASKS

### 🔍 [2025-11-25] CLI Architecture Refactoring Discovery

**문제 발견**:
- CLI와 Docker Backend가 **서로 다른 PostgreSQL DB**에 접근
  - CLI: `localhost:5432/sleassem_dev` (로컬 WSL)
  - Backend: Docker 내부 `slea-db:5432` (포트 5433으로 노출)
- `profile update_survey` 성공 (Docker API → Docker DB)
- `questions generate` 실패 (CLI가 로컬 DB 확인 → 데이터 없음)

**근본 원인**: `src/cli/actions/questions.py`의 8개 함수가 `SessionLocal()`로 직접 DB 접근
```python
# ❌ 문제 있는 코드들:
_get_latest_survey()          # line 29
_get_latest_session()         # line 55
_get_latest_question()        # line 76
_get_all_questions_in_session()  # line 127
_get_unscored_answers()       # line 159
_get_question_type()          # line 195
_get_answer_info()            # line 250
show_session_questions()      # line 706
```

**해결책**: CLI가 REST API만 호출하도록 리팩토링 (2-phase 작업)

---

### 📋 REQ-CLI-QUESTIONS-1: CLI DB 직접 접근 제거 및 REST API 마이그레이션

**Phase 0: 선행 작업 (내일)**

**1단계: Backend API 엔드포인트 추가 (~1시간)**

필요한 새로운 API (5개):
- `GET /profile/survey` ✅ 이미 있음 (profile.py)
- `GET /questions/session/latest` ❌ 없음
- `GET /questions/{question_id}` ❌ 없음
- `GET /questions/session/{session_id}/questions` ❌ 없음
- `GET /questions/session/{session_id}/unscored` ❌ 없음

위치: `src/backend/api/questions.py`

**2단계: CLI 리팩토링 (~1시간)**

제거할 함수들:
```python
# 각 함수를 client.make_request() 호출로 변경
_get_latest_survey()       → GET /profile/survey
_get_latest_session()      → GET /questions/session/latest
_get_latest_question()     → GET /questions/{question_id}
_get_all_questions_in_session() → GET /questions/session/{session_id}/questions
_get_unscored_answers()    → GET /questions/session/{session_id}/unscored
_get_question_type()       → GET /questions/{question_id}
_get_answer_info()         → GET /questions/{question_id}/answer
show_session_questions()   → GET /questions/session/{session_id}/questions
```

제거: `from src.backend.database import SessionLocal` import

---

### ✅ 기존 High-Priority Tasks (미연기)

### Task 1: REQ-A-Agent-Backend-1 (Mock → Real Agent 통합) ⭐
- **File**: `src/backend/services/question_gen_service.py` (수정)
- **Status**: ⏳ Not started
- **Duration**: ~1.5시간
- **Spec Location**: `docs/AGENT-TEST-SCENARIO.md` lines 471-555

### Task 2 (Optional): REQ-A-Agent-Backend-2 (ScoringService 통합)
- **File**: `src/backend/services/scoring_service.py`
- **Status**: ⏳ Not started
- **Duration**: ~1시간
- **Spec Location**: `docs/AGENT-TEST-SCENARIO.md` lines 517-555

---

## 📚 Documentation References (Already Exist)
**Do NOT regenerate these** - they are already complete:
- `docs/TOOL_DEFINITIONS_SUMMARY.md` - Complete tool signatures & details
- `docs/TOOL_QUICK_REFERENCE.md` - Quick examples & validation rules
- `docs/TOOL_DOCUMENTATION_INDEX.md` - Navigation & troubleshooting
- `docs/AGENT-TEST-SCENARIO.md` - Full phase planning (REQ-A-Agent-*)

**Just reference them when implementing!**

---

## 🚀 Quick Start After Context Gap

1. Read this section first (2 min)
2. Run: `git log --oneline -10` to see recent commits
3. Start with Task 1 (REQ-A-Agent-Backend-1) in `docs/AGENT-TEST-SCENARIO.md` lines 471-555
4. Use TOOL documentation (don't regenerate - it already exists)
5. Create progress file in `docs/progress/REQ-A-Agent-Backend-1.md` after Phase 4
