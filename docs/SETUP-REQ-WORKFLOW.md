# Setup REQ-Based Workflow

Setup guide for implementing requirement-driven development in any project.

---

## Quick Start

### Step 1: Copy Workflow Documentation

```bash
cp docs/REQ-WORKFLOW.md <your-project>/docs/REQ-WORKFLOW.md
```

### Step 2: Create Feature Requirements File

Create your project's specification file:

```bash
touch docs/feature_requirements.md
```

Minimum structure:

```markdown
# Feature Requirements

## REQ-X-Y: [Feature Name]

**Components**:
- REQ-X-Y-1: [Description]
- REQ-X-Y-2: [Description]

**Acceptance Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]

---

## REQ-X-Z: [Another Feature]

[Continue format above...]
```

### Step 3: Add to CLAUDE.md

Add this section to your project's `CLAUDE.md`:

```markdown
## REQ-Based Development Workflow

**When to use**: Request format: `"REQ-X-Y 기능 구현해"`

### Phase 1: SPECIFICATION

- Extract REQ from docs/feature_requirements.md
- Summarize: intent, constraints, performance goals
- Design: location, signature, behavior, dependencies
- ⛔ PAUSE: "Specification approved? Continue to Phase 2?"

### Phase 2: TEST DESIGN

- Create: tests/<domain>/test_<feature>.py
- Design: 4-5 test classes, 20-40 tests
- Include: REQ ID in docstrings
- ⛔ PAUSE: "Tests approved? Continue to Phase 3?"

### Phase 3: IMPLEMENTATION

- Write minimal code to pass tests
- Type hints on all functions
- Docstrings on all public methods
- Run: <quality-check> && pytest tests/<domain>/test_<feature>.py
- ⛾ STOP if tests fail

### Phase 4: DOCUMENTATION & COMMIT

- Create: docs/progress/REQ-X-Y.md
- Update: docs/DEV-PROGRESS.md
- Commit: git commit -m "feat: Implement REQ-X-Y..."
- Result: Clean working tree + detailed commit message

For detailed guidance, see `docs/REQ-WORKFLOW.md`
```

---

## Project File Structure

Ensure this minimum structure:

```
<project>/
├── CLAUDE.md
├── docs/
│   ├── REQ-WORKFLOW.md
│   ├── feature_requirements.md
│   ├── DEV-PROGRESS.md
│   └── progress/
│       └── REQ-X-Y.md (created during Phase 4)
├── src/
│   ├── services/
│   ├── api/
│   └── models/
├── tests/
│   └── backend/
│       └── test_feature.py (created during Phase 2)
└── pyproject.toml
```

---

## Progress Tracking Template

Create `docs/DEV-PROGRESS.md`:

```markdown
# Development Progress

Overall progress tracking for [Project Name] [Version].

---

## Development Status

### Backend

| REQ ID | Feature | Phase | Status | Notes |
|--------|---------|-------|--------|-------|
| REQ-B-A1 | [Name] | 0 | ⏳ Backlog | [Details] |
| REQ-B-A2 | [Name] | 0 | ⏳ Backlog | [Details] |

### Frontend

| REQ ID | Feature | Phase | Status | Notes |
|--------|---------|-------|--------|-------|
| REQ-F-A1 | [Name] | 0 | ⏳ Backlog | [Details] |

---

## Phase Legend

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | ⏳ Backlog | Not started |
| 1 | 📝 Spec | Awaiting review |
| 2 | 🧪 Test | Awaiting review |
| 3 | 💻 Impl | In progress |
| 4 | ✅ Done | Merged to main |

---

## Individual Progress Files

See `docs/progress/REQ-X-Y.md` for detailed progress on each REQ.

---

## How to Update Progress

After Phase 4:
- Update main progress table
- Change Phase to 4
- Change Status to ✅ Done
- Add commit SHA
```

---

## Language-Specific Customization

### Python (pytest, ruff, mypy)

Quality check command:

```bash
ruff check src/
mypy src/ --strict
black src/ --check
pytest tests/ -v
```

### Node.js (Jest, ESLint)

Quality check command:

```bash
npm run lint
npm run typecheck
npm run format:check
npm test
```

### Go (standard testing)

Quality check command:

```bash
go fmt ./...
go vet ./...
golangci-lint run
go test -v ./...
```

---

## Team Communication Template

Share this with your team:

```
📢 Starting REQ-Based Development Workflow

We're now using a structured 4-phase requirement workflow:

**How to use**:
1. User requests: "REQ-X-Y 기능 구현해"
2. AI Assistant automatically follows 4 phases:
   - Phase 1: Present specification (pause for review)
   - Phase 2: Design tests (pause for review)
   - Phase 3: Implement code (auto quality checks)
   - Phase 4: Document + commit (auto)

**Benefits**:
- ✅ Prevents rework (spec approved before coding)
- ✅ 100% test coverage (TDD)
- ✅ Clear commit history (one REQ = one commit)
- ✅ Traceable progress (REQ → Tests → Code)

**Reference**: See docs/REQ-WORKFLOW.md

Let's use this for all feature development!
```

---

## Verification Checklist

Before starting Phase 1:

- [ ] `docs/feature_requirements.md` created with REQ specs
- [ ] `CLAUDE.md` updated with REQ workflow section
- [ ] `docs/REQ-WORKFLOW.md` copied
- [ ] `docs/DEV-PROGRESS.md` created with progress table
- [ ] Team informed about workflow
- [ ] Quality check tools configured
- [ ] Git setup complete

---

## Customization Checklist

After setup, customize:

- [ ] REQ ID format (if different from REQ-X-Y)
- [ ] Quality check tools and commands
- [ ] Test framework and naming conventions
- [ ] Commit message template
- [ ] Directory structure
- [ ] Docstring/type hint conventions
- [ ] Performance SLAs

---

## Version History

- **v1.0** (2025-11-07): Initial setup guide
