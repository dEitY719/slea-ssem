# REQ-Based Development Workflow

Universal template for implementing requirement-driven features using TDD.

---

## Overview

A 4-phase workflow for implementing requirements (REQ-X-Y format):

**Specification → Tests → Code → Documentation**

### Key Principle

Never code before tests are approved. Never commit without documentation.

---

## Phase 1: Specification

### Goal

Extract and present requirement specification for approval before proceeding.

### Process

1. Locate REQ in feature specification file (e.g., `docs/feature_requirements.md`)
2. Extract complete requirement block
3. Analyze components, intent, acceptance criteria
4. Design solution: module location, function signature, logic outline
5. Present specification summary and ask for approval

### Example Output

```markdown
## REQ-B-B3-Score: Answer Scoring

**Components**:
- REQ-B-B3-Score-1: Score within 1 second
- REQ-B-B3-Score-2: Implement scoring logic
- REQ-B-B3-Score-3: Apply time penalty

**Implementation Approach**:
- Create ScoringService.score_answer()
- Route to type-specific scorer
- Apply time penalty if session exceeded limit
- Update AttemptAnswer with results
```

### Deliverable

Create progress file: `docs/progress/REQ-X-Y.md`

### Checkpoint

⛔ **STOP**: Ask approval: "Specification approved? Proceed to Phase 2?"

---

## Phase 2: Test Design

### Goal

Design comprehensive test cases before writing implementation code.

### Process

1. Create test file: `tests/<domain>/test_<feature_name>.py`
2. Design 4-5 test classes with 20-40 tests total
3. Cover: happy path, input validation, edge cases, acceptance criteria
4. Include REQ ID in docstrings: `# REQ: REQ-X-Y`
5. Use reusable fixtures for database setup

### Test Class Example

```python
class TestScoringMultipleChoice:
    """REQ-B-B3-Score-2: Score multiple choice questions."""

    def test_correct_answer_scores_one_point(self):
        """Correct answer scores 1.0."""

    def test_incorrect_answer_scores_zero(self):
        """Incorrect answer scores 0.0."""

    def test_missing_selected_key_raises_error(self):
        """Missing 'selected_key' raises ValueError."""
```

### Deliverable

Test file with all tests failing (red tests).

### Checkpoint

⛔ **STOP**: Ask approval: "Tests approved? Proceed to Phase 3?"

---

## Phase 3: Implementation

### Goal

Write minimal code to satisfy specification and pass all tests.

### Process

1. Implement core logic in identified module
2. Add type hints on all functions
3. Add docstrings on all public methods
4. Run tests iteratively: `pytest tests/<domain>/test_<feature>.py -v`
5. Run quality checks: linting, type checking, formatting
6. Fix failing tests one at a time

### Example Service Method

```python
def score_answer(
    self,
    session_id: str,
    question_id: str,
) -> dict[str, Any]:
    """
    Score a submitted answer with time penalty.

    REQ: REQ-B-B3-Score-1, 2, 3

    Args:
        session_id: TestSession ID
        question_id: Question ID

    Returns:
        Dict with: scored, question_id, user_answer, is_correct, score, ...

    Raises:
        ValueError: If session, question, or answer not found
    """
    # Implementation here
```

### Quality Checklist

- All tests passing (100%)
- Type hints on all functions
- Docstrings on all public functions
- Code quality checks passed
- Line length ≤ 120 characters

### Validation Checkpoint

⛾ **STOP if tests fail**: Fix before proceeding to Phase 4.

---

## Phase 4: Documentation & Commit

### Goal

Document progress and create a detailed commit.

### Process

1. Update progress file: `docs/progress/REQ-X-Y.md`
2. Update main progress tracking: `docs/DEV-PROGRESS.md`
3. Create detailed commit with REQ breakdown
4. Verify clean working tree

### Progress File Template

```markdown
# REQ-X-Y: [Feature Name]

**Developer**: [Name]
**Status**: Phase 4 (Done)
**Completion Date**: YYYY-MM-DD

## Requirement Summary

[1-2 sentences from spec]

## Implementation Approach

- Core design decisions
- Service/API structure
- Example: [Brief description]

## Files Created/Modified

| File | Changes | Lines |
|------|---------|-------|
| src/backend/services/... | New methods | +150 |
| tests/backend/test_... | Test suite | +500 |

## Test Coverage

- Happy path: [# tests]
- Validation: [# tests]
- Edge cases: [# tests]
- **Total**: [#] tests, 100% pass rate

## Acceptance Criteria Met

| Criteria | Status |
|----------|--------|
| [From spec] | ✅ |
| [From spec] | ✅ |

## Code Quality

- Ruff linting: ✅
- Type hints: ✅
- Docstrings: ✅
- Line length: ✅ (≤120 chars)

## Next Steps

1. [Follow-up REQ if applicable]
```

### Commit Message Template

```
feat: Implement REQ-X-Y [feature name]

Implement [feature] system for REQ-X-Y:

**REQ-X-Y-1**: [Component 1 description]
- [Key detail]

**REQ-X-Y-2**: [Component 2 description]
- [Key detail]

**Test Coverage**: [#] tests across [#] classes
- All passing (100% success rate)

**Files Changed**: [#] files (+[#] lines)
- [file]: [description]

**Code Quality**: Ruff ✅ | Types ✅ | Docs ✅
```

### Deliverable

- Progress documentation: `docs/progress/REQ-X-Y.md`
- Updated main progress: `docs/DEV-PROGRESS.md`
- Clean git commit with detailed message
- All tests passing

---

## Timeline

| Phase | Duration | Key Action | Gate |
|-------|----------|-----------|------|
| 1 | 15-30 min | Parse spec | Approval |
| 2 | 30-60 min | Write tests | Approval |
| 3 | 1-3 hours | Implement code | Tests pass |
| 4 | 30 min | Document + commit | Clean tree |

**Total: 2.5-5 hours per REQ**

---

## Key Principles

### Specification First

Skip Phase 1 and you'll rework later.

### Tests Before Code

Phase 2 tests validate spec, not implementation.

### Traceability

Every test and commit references the REQ ID.

### Documentation-as-Artifact

Progress file proves what was built, why, and how well.

---

## Version History

- **v1.0** (2025-11-07): Initial workflow documentation
