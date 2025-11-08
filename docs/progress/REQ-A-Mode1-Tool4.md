# REQ-A-Mode1-Tool4: Validate Question Quality

**Tool 4 for Mode 1 Question Generation Pipeline**

---

## 📋 Requirements Summary

| Field | Value |
|-------|-------|
| **REQ ID** | REQ-A-Mode1-Tool4 |
| **Feature** | Validate Question Quality |
| **Type** | Question Validation Tool |
| **Priority** | Must (M) |
| **MVP** | 1.0 |
| **Phase** | 4 (✅ Done) |

---

## 🎯 Purpose

Validate the quality of AI-generated questions using a 2-stage validation approach:
1. **LLM-based semantic validation** - Evaluates clarity, appropriateness, correctness, and bias
2. **Rule-based quality validation** - Checks format, length, choices count, and structure

**Final Score**: `min(LLM_score, rule_score)` (ensures both stages pass)

---

## 📥 Input Specification

```python
validate_question_quality(
    stem: str | list[str],              # Question text (max 250 chars)
    question_type: str | list[str],     # "multiple_choice"|"true_false"|"short_answer"
    choices: list[str] | list[list[str]] | None,  # Answer choices (4-5 for MC)
    correct_answer: str | list[str],    # Correct answer
    batch: bool = False                 # Enable batch processing
) -> dict | list[dict]
```

**Parameters**:
- `stem`: Question stem text or list of stems (for batch)
- `question_type`: Type of question or list of types
- `choices`: Answer choices list or None (for short answer/true-false)
- `correct_answer`: Correct answer or list of answers
- `batch`: Set True to validate multiple questions at once

---

## 📤 Output Specification

```python
{
    "is_valid": bool,           # True if final_score >= 0.70
    "score": float,             # LLM semantic score (0.0-1.0)
    "rule_score": float,        # Rule-based score (0.0-1.0)
    "final_score": float,       # min(score, rule_score)
    "feedback": str,            # Human-readable feedback (Korean)
    "issues": list[str],        # List of detected issues
    "recommendation": str       # "pass" | "revise" | "reject"
}
```

**For batch mode**: Returns `list[dict]` with result for each question.

---

## ✅ Validation Rules

### 🤖 LLM Semantic Validation (0.0-1.0)

Uses Google Gemini LLM to evaluate:
- **Clarity**: Is the question clear and unambiguous?
- **Appropriateness**: Is the difficulty level suitable?
- **Correctness**: Is the correct answer objective and verifiable?
- **Bias**: Are there biases or inappropriate language?
- **Format**: Is the structure valid and proper?

**Fallback**: If LLM call fails → returns 0.5 (default score)

### 📏 Rule-Based Validation (0.0-1.0)

| Rule | Constraint | Penalty |
|------|-----------|---------|
| Stem Length | ≤ 250 chars | -0.2 |
| Choices Count (MC only) | 4-5 items | -0.2 |
| Answer in Choices | Correct answer must be in choices | -0.3 |
| No Duplicate Choices | All choices must be unique | -0.15 |

**Scoring**: Starts at 1.0, deductions applied for violations

### 🎯 Recommendation Logic

| Final Score | Recommendation | Action |
|-------------|----------------|--------|
| ≥ 0.85 | **pass** | Save immediately |
| 0.70 - 0.84 | **revise** | Can regenerate with feedback |
| < 0.70 | **reject** | Discard, generate new |

**is_valid**: `True` if final_score >= 0.70, `False` otherwise

---

## 🗂️ Implementation Details

### File Location
- **Implementation**: `src/agent/tools/validate_question_tool.py`
- **Tests**: `tests/agent/tools/test_validate_question_tool.py`

### Key Functions

| Function | Purpose |
|----------|---------|
| `validate_question_quality()` | Main public tool (LangChain @tool decorator) |
| `_validate_question_quality_impl()` | Core implementation (testable) |
| `_validate_question_inputs()` | Input parameter validation |
| `_check_rule_based_quality()` | Rule-based validation logic |
| `_call_llm_validation()` | LLM semantic evaluation |
| `_get_recommendation()` | Determine pass/revise/reject |
| `_build_feedback()` | Generate human-readable feedback |

### Error Handling

- **Invalid inputs**: Raises `ValueError` or `TypeError`
- **LLM failures**: Falls back to default score (0.5)
- **Missing fields**: Validates completeness before processing
- **Special characters**: Handles unicode and special characters properly

---

## 🧪 Test Coverage

### Test Classes (23 tests total)

#### 1️⃣ TestInputValidation (4 tests)
- ✅ Empty stem validation
- ✅ Invalid question type detection
- ✅ Missing choices for multiple_choice
- ✅ Missing correct_answer detection

#### 2️⃣ TestRuleBasedValidation (6 tests)
- ✅ Valid stem length (≤ 250 chars)
- ✅ Invalid long stem (> 250 chars)
- ✅ Valid choice count (4-5 items)
- ✅ Too few choices (< 4)
- ✅ Too many choices (> 5)
- ✅ Answer not in choices

#### 3️⃣ TestSingleValidationHappyPath (3 tests)
- ✅ High-quality multiple choice question
- ✅ High-quality true/false question
- ✅ High-quality short answer question

#### 4️⃣ TestRecommendationLogic (3 tests)
- ✅ Recommendation "pass" (score ≥ 0.85)
- ✅ Recommendation "revise" (0.70 ≤ score < 0.85)
- ✅ Recommendation "reject" (score < 0.70)

#### 5️⃣ TestBatchValidation (2 tests)
- ✅ Batch returns list of results
- ✅ Each batch result has required fields

#### 6️⃣ TestEdgeCasesAndErrorHandling (2 tests)
- ✅ Special characters in question
- ✅ LLM service failure handling

#### 7️⃣ TestResponseStructure (3 tests)
- ✅ Single result has all required fields
- ✅ Score values in valid range [0.0, 1.0]
- ✅ final_score = min(LLM_score, rule_score)

### Test Results

```
======================== 23 passed, 1 warning in 2.11s =========================
```

**Pass Rate**: 100% ✅

---

## 📊 Traceability Matrix

| Acceptance Criteria | Test Coverage | Status |
|-------------------|---------------|--------|
| AC1: Single & batch validation | `TestSingleValidationHappyPath` + `TestBatchValidation` | ✅ Pass |
| AC2: LLM + rule-based scoring | `TestRuleBasedValidation` + `TestResponseStructure` | ✅ Pass |
| AC3: Correct recommendations | `TestRecommendationLogic` | ✅ Pass |
| AC4: Error handling | `TestEdgeCasesAndErrorHandling` | ✅ Pass |
| AC5: Proper logging | Integrated in implementation | ✅ Done |

---

## 🔄 Implementation Notes

### Architecture

```
validate_question_quality()
  ↓
  _validate_question_quality_impl()
    ├─ _validate_question_inputs()         [Validate inputs]
    ├─ (if batch) Process multiple questions in loop
    │   └─ _validate_single_question()
    │       ├─ _check_rule_based_quality() [Rule scoring]
    │       └─ _call_llm_validation()      [LLM scoring]
    └─ _get_recommendation() + _build_feedback()
```

### Key Design Decisions

1. **Final Score = min(LLM, Rule)**: Ensures both validation stages pass
2. **Graceful Degradation**: LLM failures don't block validation
3. **Batch Support**: Can validate multiple questions efficiently
4. **Comprehensive Feedback**: Korean feedback messages for users
5. **Type Safety**: Full type hints with mypy strict mode

### Performance Considerations

- **LLM Call Timeout**: 15 seconds (configured in agent/config.py)
- **Batch Processing**: Multiple questions processed in single loop
- **Error Recovery**: Fallback to default score on LLM failure

---

## 📝 Git Commit Information

**Commit SHA**: (to be created during Phase 4)

**Commit Message Format**:
```
chore: Update progress tracking for REQ-A-Mode1-Tool4 completion

Document Phase 4 completion for REQ-A-Mode1-Tool4 (문항 품질 검증):

**Changes**:
- Created src/agent/tools/validate_question_tool.py with full implementation
- Created tests/agent/tools/test_validate_question_tool.py with 23 tests
- Updated docs/progress/REQ-A-Mode1-Tool4.md with Phase 4 documentation
- Updated docs/DEV-PROGRESS.md to mark Tool4 as completed

**REQ-A-Mode1-Tool4 Status**:
- Phase: 4 (✅ Done)
- Test Coverage: 23 tests (100% pass rate)
- Implementation: LLM + rule-based validation
- Acceptance Criteria: All AC1-AC5 verified

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 📚 Related Documentation

- **Feature Requirements**: `docs/feature_requirement_mvp1.md` (lines 1841-1903)
- **Agent REQ ID Assignment**: `docs/AGENT-REQ-ID-ASSIGNMENT.md` (lines 78-89)
- **Development Progress**: `docs/DEV-PROGRESS.md`
- **Tool 1**: `docs/progress/REQ-A-Mode1-Tool1-PHASE3.md`
- **Tool 2**: `docs/progress/REQ-A-Mode1-Tool2.md`
- **Tool 3**: `docs/progress/REQ-A-Mode1-Tool3.md`

---

## 🚀 Next Steps (REQ-A-Mode1-Tool5)

The next tool in the pipeline is **REQ-A-Mode1-Tool5: Save Generated Question**, which will:
- Save validated questions to the question_bank
- Store validation scores as metadata
- Handle batch saving with error recovery

---

**Status**: ✅ Phase 4 Complete
**Date Completed**: 2025-11-09
**Developer**: Claude Code
**Review Status**: Awaiting team review
