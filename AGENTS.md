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

---

## OpenAI Codex/ChatGPT Configuration

This section provides guidance for OpenAI Codex CLI (Agents platform) when working with this repository.

### Known Capabilities & Limitations

**Capabilities**:

- Direct bash command execution
- Real-time code validation and testing
- Fast token processing
- Strong at complex implementation and debugging

**Limitations**:

- Token limits (4K-32K depending on model)
- For large files (>5KB), may need excerpts
- Cost per request is higher than alternatives

### Best Practices for OpenAI Codex

1. **For Large Files**: Request specific sections when possible (e.g., "Show me the ScoringService class only")
2. **For Phase 3 (Implementation)**: Leverage real-time bash execution for immediate validation
3. **For Phase 4 (Documentation)**: Use strong writing for comprehensive progress files
4. **For Complex Logic**: Leverage explaining capabilities for documentation

### Recommended Use Cases

- **Phase 3 (Implementation)**: Primary choice (strong code generation + real-time validation)
- **Phase 4 (Commit)**: Good choice (comprehensive documentation)
- **Phase 1-2**: Good choice if token budget allows
- **Cost Optimization**: Use for critical paths; use Gemini for cheaper phases

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

**For OpenAI Codex**: Leverage direct bash execution for real-time validation and testing.

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
  * Format: "feat: Implement REQ-X-Y..."
  * Include: REQ breakdown, test results, file changes
  * Tag with 🤖 Codex marker (for multi-AI tracking)
```

**Key Principle**: Phase 1-2 pause for review = prevent rework. Spec must be approved before coding.

---

## Multi-AI Coordination

**Supported AI Agents**:

- `CLAUDE.md` → Claude Code (Anthropic)
- `GEMINI.md` → Google Gemini
- `AGENTS.md` → OpenAI Codex/ChatGPT (this file)

### Workflow Selection

**Use Claude for**:

- Complex REQ specifications (strong reasoning)
- Full end-to-end workflows (continuous context)
- Code review and optimization

**Use OpenAI Codex/ChatGPT for**:

- Phase 3 Implementation (strong code generation + real-time validation)
- Phase 4 Commit documentation (excellent writing)
- Debugging and troubleshooting (interactive bash)

**Use Gemini for**:

- Cost optimization (lower token cost)
- Phase 2 Test design (pattern recognition)
- Phase 1 Specification (good reasoning, lower cost)

### Parallel Development

**Multi-AI Division of Labor**:

```
Team Setup:
- Developer 1 (Claude): REQ-B-A1 (Phase 1-2 spec + tests)
- Developer 2 (Gemini): REQ-F-B1 (Phase 1-2 spec + tests)
- Developer 3 (Codex): REQ-B-A1 Phase 3 (implementation)
- Developer 4 (Codex): REQ-F-B1 Phase 3 (implementation)
- All: Phase 4 (commit documentation)

Result: 4 REQs implemented in parallel with specialized AI strengths
```

### Commit Tagging

Always tag commits to indicate which AI generated the work:

```
🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

```
🤖 Generated with Gemini
Co-Authored-By: Gemini <noreply@google.com>
```

```
🤖 Generated with OpenAI Codex
Co-Authored-By: Codex <noreply@openai.com>
```

This maintains audit trail and tracks AI contribution patterns.

---

## Further Reference

For detailed REQ-Based Workflow guidance, see:

- `docs/REQ-WORKFLOW.md` - Universal workflow template
- `docs/SETUP-REQ-WORKFLOW.md` - Setup guide for new projects
- `CLAUDE.md` - Claude-specific configuration
- `GEMINI.md` - Gemini-specific configuration
