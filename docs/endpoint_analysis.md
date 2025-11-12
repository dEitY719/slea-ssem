# Endpoint Analysis: POST /questions/answer/score vs POST /questions/autosave

## Overview

Critical format differences exist between what autosave stores and what score_answer expects, causing validation failures. This document provides the complete structure expectations and validation logic.

---

## 1. ScoringRequest Model (POST /questions/answer/score)

### Location

`src/backend/api/questions.py` (lines 175-188)

### Request Schema

```python
class ScoringRequest(BaseModel):
    session_id: str = Field(..., description="TestSession ID")
    question_id: str = Field(..., description="Question ID")
```

**Key Points:**

- Only requires `session_id` and `question_id` in request
- Does NOT take `user_answer` directly in request
- **Retrieves user_answer from database** - must have been saved via autosave first

### Response Schema

```python
class ScoringResponse(BaseModel):
    scored: bool
    question_id: str
    user_answer: dict[str, Any] | str  # ⚠️ Can be dict OR string
    is_correct: bool
    score: float                         # Base score (0-100)
    feedback: str
    time_penalty_applied: bool
    final_score: float
    scored_at: str
```

---

## 2. AutosaveRequest Model (POST /questions/autosave)

### Location

`src/backend/api/questions.py` (lines 109-126)

### Request Schema

```python
class AutosaveRequest(BaseModel):
    session_id: str = Field(..., description="TestSession ID")
    question_id: str = Field(..., description="Question ID")
    user_answer: dict[str, Any] = Field(..., description="User's answer (JSON)")
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")
```

**Key Requirement:**

- `user_answer` must be a **JSON dictionary** (not string)
- No specific schema validation at API layer
- Stored as-is in database

---

## 3. ScoringService.score_answer() Implementation

### Location

`src/backend/services/scoring_service.py` (lines 41-124)

### Code Flow

```python
def score_answer(self, session_id: str, question_id: str) -> dict[str, Any]:
    # 1. Validate session exists
    test_session = self.session.query(TestSession).filter_by(id=session_id).first()
    
    # 2. Validate question exists and belongs to session
    question = self.session.query(Question).filter_by(id=question_id, session_id=session_id).first()
    
    # 3. **CRITICAL**: Fetch attempt answer from DB (from autosave)
    attempt_answer = (
        self.session.query(AttemptAnswer)
        .filter_by(session_id=session_id, question_id=question_id)
        .first()
    )
    if not attempt_answer:
        raise ValueError(f"Answer for question {question_id} not found (not yet saved)")
    
    # 4. Score based on item_type
    if question.item_type == "multiple_choice":
        is_correct, base_score = self._score_multiple_choice(
            attempt_answer.user_answer,      # ⚠️ Retrieved from DB
            question.answer_schema           # ⚠️ Retrieved from Question
        )
    elif question.item_type == "true_false":
        is_correct, base_score = self._score_true_false(...)
    elif question.item_type == "short_answer":
        is_correct, base_score = self._score_short_answer(...)
```

---

## 4. User Answer Format Expectations by Question Type

### 4.1 Multiple Choice

#### What autosave stores

```json
{
  "selected_key": "A"  or "B" or "C" or "D"
}
```

#### What _score_multiple_choice() expects

```python
def _score_multiple_choice(self, user_answer: Any, answer_schema: dict) -> tuple[bool, float]:
    # Validation: user_answer MUST be a dict
    if not isinstance(user_answer, dict):
        raise ValueError("user_answer must be a dictionary for multiple choice")
    
    # Validation: MUST have 'selected_key' field
    if "selected_key" not in user_answer:
        raise ValueError("user_answer missing 'selected_key' field")
    
    # Comparison
    selected_key = str(user_answer["selected_key"]).strip()
    correct_key = str(answer_schema.get("correct_key", "")).strip()
    is_correct = selected_key == correct_key
    score = 1.0 if is_correct else 0.0
```

#### Answer Schema Structure

```json
{
  "correct_key": "A",
  "explanation": "...",
  ...
}
```

---

### 4.2 True/False

#### What autosave stores

```json
{
  "answer": true  or "true" or "yes" or "1"
}
```

#### What _score_true_false() expects

```python
def _score_true_false(self, user_answer: Any, answer_schema: dict) -> tuple[bool, float]:
    # Validation: user_answer MUST be a dict
    if not isinstance(user_answer, dict):
        raise ValueError("user_answer must be a dictionary for true/false")
    
    # Validation: MUST have 'answer' field
    if "answer" not in user_answer:
        raise ValueError("user_answer missing 'answer' field")
    
    user_ans = user_answer["answer"]
    
    # Normalization: supports bool, string, various formats
    if isinstance(user_ans, bool):
        user_bool = user_ans
    elif isinstance(user_ans, str):
        user_lower = user_ans.lower().strip()
        if user_lower in ("true", "yes", "1"):
            user_bool = True
        elif user_lower in ("false", "no", "0"):
            user_bool = False
        else:
            raise ValueError(f"Invalid true/false answer: {user_ans}")
    else:
        raise ValueError(f"Invalid true/false answer type: {type(user_ans)}")
    
    # Get and compare correct answer
    correct_ans = answer_schema.get("correct_answer")
    # ... similar normalization ...
    is_correct = user_bool == correct_bool
    score = 1.0 if is_correct else 0.0
```

#### Answer Schema Structure

```json
{
  "correct_answer": true  or "true",
  "explanation": "...",
  ...
}
```

---

### 4.3 Short Answer

#### What autosave stores

```json
{
  "text": "The answer is..."
}
```

#### What _score_short_answer() expects

```python
def _score_short_answer(self, user_answer: Any, answer_schema: dict) -> tuple[bool, float]:
    # Flexible: accepts both dict and plain string
    if isinstance(user_answer, dict):
        answer_text = str(user_answer.get("text", "")).strip()
    else:
        answer_text = str(user_answer).strip()
    
    # Get keywords from answer_schema
    keywords = answer_schema.get("keywords", [])
    
    if not keywords:
        # If no keywords, empty answer = 0, non-empty = 100
        return len(answer_text) > 0, 100.0 if len(answer_text) > 0 else 0.0
    
    # Keyword matching (case-insensitive, substring matching)
    answer_lower = answer_text.lower()
    matched_count = 0
    for keyword in keywords:
        keyword_lower = str(keyword).lower().strip()
        if keyword_lower and keyword_lower in answer_lower:
            matched_count += 1
    
    # Partial credit calculation
    total_keywords = len(keywords)
    score = (matched_count / total_keywords * 100.0) if total_keywords > 0 else 0.0
    is_correct = matched_count == total_keywords
```

#### Answer Schema Structure

```json
{
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "explanation": "...",
  ...
}
```

---

## 5. Database Model (AttemptAnswer)

### Location

`src/backend/models/attempt_answer.py`

### Schema

```python
class AttemptAnswer(Base):
    id: Mapped[str]                           # UUID
    session_id: Mapped[str]                   # FK to test_sessions
    question_id: Mapped[str]                  # FK to questions
    user_answer: Mapped[str | dict]           # JSON field (flexible)
    is_correct: Mapped[bool]                  # Set by scoring service
    score: Mapped[float]                      # Set by scoring service (0-100)
    response_time_ms: Mapped[int]             # From autosave request
    saved_at: Mapped[datetime]                # Autosave timestamp
    created_at: Mapped[datetime]              # Record creation
```

---

## 6. AutosaveService.save_answer() Implementation

### Location

`src/backend/services/autosave_service.py` (lines 42-113)

### Code Flow

```python
def save_answer(self, session_id: str, question_id: str, user_answer: dict[str, Any], response_time_ms: int) -> AttemptAnswer:
    # 1. Validate session exists and is saveable
    test_session = self.session.query(TestSession).filter_by(id=session_id).first()
    if not test_session:
        raise ValueError(f"Test session {session_id} not found")
    
    if test_session.status == "completed":
        raise ValueError(f"Session {session_id} is already completed")
    
    # 2. Validate question exists and belongs to session
    question = self.session.query(Question).filter_by(id=question_id, session_id=session_id).first()
    if not question:
        raise ValueError(f"Question {question_id} not found in session {session_id}")
    
    # 3. Set started_at on first answer if not already set
    if not test_session.started_at:
        test_session.started_at = datetime.now(UTC)
        self.session.commit()
    
    # 4. Check if answer already exists (idempotent update)
    existing = self.session.query(AttemptAnswer).filter_by(session_id=session_id, question_id=question_id).first()
    
    if existing:
        # Update: just replace user_answer, response_time_ms, saved_at
        existing.user_answer = user_answer  # ⚠️ Stores as-is (no validation)
        existing.response_time_ms = response_time_ms
        existing.saved_at = datetime.now(UTC)
        self.session.commit()
        return existing
    
    # 5. Create new answer
    answer = AttemptAnswer(
        session_id=session_id,
        question_id=question_id,
        user_answer=user_answer,  # ⚠️ Stores as-is (no validation)
        is_correct=False,          # Set by scoring service later
        score=0.0,                 # Set by scoring service later
        response_time_ms=response_time_ms,
        saved_at=datetime.now(UTC)
    )
    self.session.add(answer)
    self.session.commit()
    return answer
```

**Key Observation:** No validation of user_answer structure in autosave - stored as-is.

---

## 7. Format Differences Summary

| Aspect | Autosave (POST /autosave) | Score Endpoint (POST /answer/score) |
|--------|---------------------------|-------------------------------------|
| **Input** | `user_answer` in request body | No input - retrieved from DB |
| **Validation** | None at API layer | Strict per item_type |
| **Storage** | Stores dict as-is | Retrieved and scored |
| **MC Format** | `{"selected_key": "A"}` | Expected: `{"selected_key": "X"}` |
| **TF Format** | `{"answer": true}` | Expected: `{"answer": true/bool/string}` |
| **SA Format** | `{"text": "answer"}` or plain string | Expected: Either format works |
| **Error Handling** | Minimal | Strict ValueError on mismatch |

---

## 8. Common Failure Scenarios

### Scenario 1: Missing "selected_key" in MC autosave

```json
// WRONG - What client might send to autosave
{
  "user_answer": {
    "choice": "A"  // Wrong field name!
  }
}

// Result: Stores as-is in DB
// When score_answer() runs:
// ❌ ValueError: "user_answer missing 'selected_key' field"
```

### Scenario 2: String instead of dict for MC

```json
// WRONG
{
  "user_answer": "A"  // String, not dict!
}

// Result: Stores string in DB
// When score_answer() runs:
// ❌ ValueError: "user_answer must be a dictionary for multiple choice"
```

### Scenario 3: Correct format

```json
// CORRECT - Autosave
{
  "user_answer": {
    "selected_key": "A"
  }
}

// Stores in DB, score_answer() retrieves and validates successfully
// ✅ Scores correctly
```

---

## 9. Validation Flow Diagram

```
Frontend Client
    |
    v
POST /questions/autosave
    |
    +-> AutosaveRequest validation (Pydantic)
    |   - session_id: required string
    |   - question_id: required string
    |   - user_answer: required dict (no internal validation)
    |   - response_time_ms: required int >= 0
    |
    v
AutosaveService.save_answer()
    |
    +-> No validation of user_answer structure
    +-> Stores dict as-is in DB
    |
    v
Database (attempt_answers table)
    |
    user_answer: JSON (flexible, accepts any structure)
    |
    v
POST /questions/answer/score
    |
    +-> ScoringRequest validation
    |   - session_id: required string
    |   - question_id: required string
    |
    v
ScoringService.score_answer()
    |
    +-> Fetch attempt_answer from DB
    +-> Fetch question from DB
    |
    v
Switch on question.item_type:
    |
    +-> "multiple_choice"
    |   |
    |   v
    |   _score_multiple_choice()
    |   |
    |   +-> Validate: isinstance(user_answer, dict) ✓
    |   +-> Validate: "selected_key" in user_answer ✓
    |   +-> Extract: selected_key = user_answer["selected_key"]
    |   +-> Compare: selected_key == answer_schema["correct_key"]
    |
    +-> "true_false"
    |   |
    |   v
    |   _score_true_false()
    |   |
    |   +-> Validate: isinstance(user_answer, dict) ✓
    |   +-> Validate: "answer" in user_answer ✓
    |   +-> Extract: answer = user_answer["answer"]
    |   +-> Normalize: bool, string formats supported
    |   +-> Compare: normalized user_answer == normalized correct_answer
    |
    +-> "short_answer"
        |
        v
        _score_short_answer()
        |
        +-> Flexible: accepts dict or string
        +-> Extract text: from dict["text"] or plain string
        +-> Get keywords: answer_schema["keywords"]
        +-> Match keywords: case-insensitive substring matching
        +-> Calculate: (matched / total) * 100
```

---

## 10. Summary: Critical Requirements

### For Autosave Request (Frontend → POST /autosave)

1. **Multiple Choice:**

   ```json
   {
     "session_id": "uuid",
     "question_id": "uuid",
     "user_answer": {
       "selected_key": "A"  // or B, C, D - required
     },
     "response_time_ms": 5000
   }
   ```

2. **True/False:**

   ```json
   {
     "session_id": "uuid",
     "question_id": "uuid",
     "user_answer": {
       "answer": true  // or false, or "true"/"false"/"yes"/"no"/"1"/"0"
     },
     "response_time_ms": 5000
   }
   ```

3. **Short Answer:**

   ```json
   {
     "session_id": "uuid",
     "question_id": "uuid",
     "user_answer": {
       "text": "The answer to the question..."
     },
     "response_time_ms": 5000
   }
   ```

### For Score Request (Frontend → POST /answer/score)

```json
{
  "session_id": "uuid",  // Must match saved answer
  "question_id": "uuid"  // Must match saved answer
  // user_answer is NOT sent here - it's retrieved from DB
}
```

### Critical Invariant

**The `user_answer` format sent to `/autosave` MUST match exactly what the scoring methods expect, because autosave does NO validation and score_answer does STRICT validation.**
