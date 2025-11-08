# REQ-A-Mode1-Tool5: Save Generated Question

**Tool 5 for Mode 1 Question Generation Pipeline**

---

## 📋 Requirements Summary

| Field | Value |
|-------|-------|
| **REQ ID** | REQ-A-Mode1-Tool5 |
| **Feature** | Save Generated Question |
| **Type** | Question Storage Tool |
| **Priority** | Must (M) |
| **MVP** | 1.0 |
| **Phase** | 4 (✅ Done) |

---

## 🎯 Purpose

Save validated questions to the question_bank with metadata (validation_score, explanation).

This tool persists questions that have passed Tool 4 validation to the PostgreSQL database,
storing all necessary information for test delivery and analytics.

---

## 📥 Input Specification

```python
save_generated_question(
    item_type: str,                          # "multiple_choice"|"true_false"|"short_answer"
    stem: str,                               # Question content (max 2000 chars)
    choices: list[str] | None,               # Answer choices (for MC/TF)
    correct_key: str | None,                 # Correct answer (for MC/TF)
    correct_keywords: list[str] | None,      # Keywords (for short_answer)
    difficulty: int,                         # 1-10 difficulty level
    categories: list[str],                   # Domain categories ["LLM", "RAG"]
    round_id: str,                           # Round ID for tracking
    validation_score: float | None = None,   # Tool 4's final_score (metadata)
    explanation: str | None = None           # Optional explanation (metadata)
) -> dict
```

**Parameters**:
- `item_type`: Question type (must match QUESTION_TYPES)
- `stem`: Question text/stem (required, non-empty)
- `choices`: Answer choices (required for MC/TF, None for short_answer)
- `correct_key`: Correct answer value (required for MC/TF)
- `correct_keywords`: Keywords for short_answer (required for short_answer type)
- `difficulty`: Difficulty 1-10 (required)
- `categories`: Domain categories (required, non-empty list)
- `round_id`: Round ID from Tool 3/4 pipeline (required)
- `validation_score`: Tool 4's final_score for traceability (optional)
- `explanation`: Question explanation for learning (optional)

---

## 📤 Output Specification

```python
{
    "question_id": "uuid",                  # Newly created question ID
    "round_id": "...",                      # Echo of input round_id
    "saved_at": "2025-11-09T10:30:00Z",    # ISO 8601 timestamp
    "success": True,                        # Save success flag
    "error": str | None,                    # Error message if failed
    "queued_for_retry": bool                # True if added to memory queue
}
```

**For successful save (success=True)**:
- `question_id`: UUID string
- `saved_at`: Timestamp
- `error`: None
- `queued_for_retry`: False

**For failed save (success=False)**:
- `question_id`: None
- `error`: Exception message
- `queued_for_retry`: True (added to SAVE_RETRY_QUEUE)

---

## 🗄️ Database Mapping

**Table**: `questions` (PostgreSQL)

| Column | Source | Type | Notes |
|--------|--------|------|-------|
| `id` | Auto-generated | UUID | Primary key |
| `session_id` | Extracted from round_id | String | For linking to test_sessions |
| `item_type` | Input parameter | Enum | Multiple_choice, true_false, short_answer |
| `stem` | Input parameter | String(2000) | Question content |
| `choices` | Input parameter | JSON array | MC/TF choices |
| `answer_schema` | Built from inputs | JSON object | Stores correct_key, correct_keywords, validation_score, explanation |
| `difficulty` | Input parameter | Integer | 1-10 |
| `category` | First item of categories | String(100) | Primary domain category |
| `round` | Extracted from round_id | Integer | Round number (1 or 2) |
| `created_at` | Auto-set | DateTime | Current timestamp |

**Answer Schema Structure**:
```python
{
    "correct_key": "...",           # For MC/TF
    "correct_keywords": [...],      # For short_answer
    "validation_score": 0.92,       # Tool 4's final_score
    "explanation": "..."            # Question explanation
}
```

---

## ✅ Validation Rules

### Input Validation
- `item_type`: Must be in {"multiple_choice", "true_false", "short_answer"}
- `stem`: Non-empty string, max 2000 chars
- `difficulty`: Integer 1-10
- `categories`: Non-empty list of strings
- `round_id`: Non-empty string
- **Type-specific**:
  - MC: correct_key must be in choices
  - TF: correct_key must be "True" or "False"
  - SA: correct_keywords must be non-empty list of strings

### Round ID Parsing
Format: `"{session_id}_{round_number}_{timestamp}"`
- Example: `"sess_abc123_1_2025-11-09T10:30:00Z"`
- Extraction:
  - `session_id`: First part (parts[0])
  - `round_number`: Second part (parts[1]) - parsed as int
  - Defaults to round 1 if parsing fails

### Category Handling
- Primary category: First item from categories list
- Additional categories can be stored in answer_schema for future use
- Defaults to "general" if not provided

---

## 📊 Error Handling & Recovery

### Success Path
1. Validate inputs
2. Build answer_schema
3. Create Question instance
4. Add to session, commit, refresh
5. Return success response with question_id

### Failure Path
1. Database error caught
2. Rollback transaction
3. Add to SAVE_RETRY_QUEUE (memory queue)
4. Return response with success=False, queued_for_retry=True
5. **Batch retry** can be executed later by processing SAVE_RETRY_QUEUE

### Memory Queue Management
- `get_retry_queue()`: Return copy of queued items
- `clear_retry_queue()`: Clear queue after successful batch save
- Max queue size: Configurable (currently unlimited)

---

## 🧪 Test Coverage

### Test Classes (15 tests total)

#### 1️⃣ TestInputValidation (5 tests)
- ✅ Empty stem validation
- ✅ Invalid item_type detection
- ✅ Invalid difficulty out of range
- ✅ Empty categories list
- ✅ Empty round_id validation

#### 2️⃣ TestAnswerSchemaValidation (2 tests)
- ✅ Answer schema for multiple_choice (correct_key)
- ✅ Answer schema for short_answer (correct_keywords)

#### 3️⃣ TestSaveQuestionHappyPath (3 tests)
- ✅ Save multiple_choice question
- ✅ Save true_false question
- ✅ Save short_answer question

#### 4️⃣ TestResponseStructure (2 tests)
- ✅ Response has all required fields (question_id, round_id, saved_at, success)
- ✅ Response round_id matches input round_id

#### 5️⃣ TestErrorHandling (1 test)
- ✅ Database error → fallback to memory queue

#### 6️⃣ TestMetadataStorage (2 tests)
- ✅ validation_score stored in answer_schema
- ✅ Explanation stored in answer_schema

### Test Results

```
======================== 15 passed in 2.04s ==============================
✅ 100% Pass Rate
```

---

## 📊 Traceability Matrix

| Acceptance Criteria | Test Coverage | Status |
|-------------------|---------------|--------|
| AC1: Save all question types | TestSaveQuestionHappyPath (3 tests) | ✅ Pass |
| AC2: Store metadata (validation_score, explanation) | TestMetadataStorage (2 tests) + TestAnswerSchemaValidation | ✅ Pass |
| AC3: Return question_id + timestamp | TestResponseStructure (2 tests) | ✅ Pass |
| AC4: Error recovery with memory queue | TestErrorHandling | ✅ Pass |
| AC5: Proper input validation | TestInputValidation (5 tests) | ✅ Pass |

---

## 🔄 Implementation Details

### File Locations
- **Implementation**: `src/agent/tools/save_question_tool.py` (416 lines)
- **Tests**: `tests/agent/tools/test_save_question_tool.py` (15 tests)

### Key Functions

| Function | Purpose |
|----------|---------|
| `save_generated_question()` | Main public tool (LangChain @tool decorator) |
| `_save_generated_question_impl()` | Core implementation (testable) |
| `_validate_save_question_inputs()` | Input parameter validation |
| `_build_answer_schema()` | Construct JSON schema from inputs |
| `_extract_category_string()` | Get primary category from list |
| `_extract_round_number()` | Parse round number from round_id |
| `_extract_session_id()` | Parse session_id from round_id |
| `get_retry_queue()` | Retrieve failed saves for batch retry |
| `clear_retry_queue()` | Clear queue after successful batch save |

### Architecture

```
save_generated_question()
  ↓
  _save_generated_question_impl()
    ├─ _validate_save_question_inputs()    [Input validation]
    ├─ _build_answer_schema()              [Metadata storage]
    ├─ _extract_category_string()          [Category mapping]
    ├─ _extract_round_number()             [Round ID parsing]
    ├─ Create Question instance
    ├─ db.add() + db.commit()              [Save to DB]
    └─ (On error) SAVE_RETRY_QUEUE.append() [Memory fallback]
```

### Design Decisions

1. **Metadata Storage**: Both validation_score and explanation stored in answer_schema JSON
2. **Graceful Degradation**: Database errors don't fail completely - items added to retry queue
3. **Round ID Parsing**: Extracts session_id and round_num for proper linking
4. **Category Selection**: Uses first category as primary, extensible for future use
5. **Type Safety**: Full type hints with strict validation

---

## 🚀 Integration Points

### Upstream (Tool 4: Validate Question Quality)
- Input: validation_score and recommendation from Tool 4
- Constraint: Only save if recommendation="pass" (score >= 0.85)

### Downstream (Mode 1 Pipeline Orchestration)
- Output: question_id used for response building
- Feedback: success flag indicates save status

### Database Schema
- Maps to `questions` table
- Links to `test_sessions` via session_id (extracted from round_id)
- answer_schema stores flexible JSON data

---

## 📝 Git Commit Information

**Commit SHA**: (to be created during Phase 4)

**Commit Message Format**:
```
feat(agent): Implement REQ-A-Mode1-Tool5 Save Generated Question tool

Complete Phase 4 implementation for REQ-A-Mode1-Tool5 (생성된 문항 저장):

**Changes**:
- Created src/agent/tools/save_question_tool.py with full implementation
- Created tests/agent/tools/test_save_question_tool.py with 15 tests
- Updated docs/progress/REQ-A-Mode1-Tool5.md with Phase 4 documentation
- Updated docs/DEV-PROGRESS.md to mark Tool5 as completed

**REQ-A-Mode1-Tool5 Status**:
- Phase: 4 (✅ Done)
- Test Coverage: 15 tests (100% pass rate)
- Implementation: Database persistence with metadata storage
- Error Recovery: Memory queue for failed saves (batch retry)
- Acceptance Criteria: All AC1-AC5 verified

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 📚 Related Documentation

- **Feature Requirements**: `docs/feature_requirement_mvp1.md` (lines 1917-1925, 2159-2210)
- **Agent REQ ID Assignment**: `docs/AGENT-REQ-ID-ASSIGNMENT.md` (lines 91-98)
- **Development Progress**: `docs/DEV-PROGRESS.md`
- **Tool 1**: `docs/progress/REQ-A-Mode1-Tool1-PHASE3.md`
- **Tool 2**: `docs/progress/REQ-A-Mode1-Tool2.md`
- **Tool 3**: `docs/progress/REQ-A-Mode1-Tool3.md`
- **Tool 4**: `docs/progress/REQ-A-Mode1-Tool4.md`

---

## 🚀 Next Steps

The Mode 1 pipeline is now 80% complete:
- ✅ Tool 1: Get User Profile
- ✅ Tool 2: Search Question Templates
- ✅ Tool 3: Get Difficulty Keywords
- ✅ Tool 4: Validate Question Quality
- ✅ Tool 5: Save Generated Question
- ⏳ Pipeline Integration: Mode1-Pipeline (orchestrator)
- ⏳ Tool 6: Score & Generate Explanation (Mode 2)

---

**Status**: ✅ Phase 4 Complete
**Date Completed**: 2025-11-09
**Developer**: Claude Code
**Review Status**: Awaiting team review
