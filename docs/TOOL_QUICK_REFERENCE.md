# Tool 1-6 Quick Reference Card

## Tool Call Patterns

### Tool 1: Get User Profile
```python
profile = get_user_profile(user_id="550e8400-e29b-41d4-a716-446655440000")

# Returns:
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "self_level": "intermediate",
    "years_experience": 5,
    "job_role": "Software Engineer",
    "duty": "Backend Development",
    "interests": ["AI", "Cloud Computing"],
    "previous_score": 85
}
```

### Tool 2: Search Question Templates
```python
templates = search_question_templates(
    interests=["LLM", "RAG", "Agent Architecture"],
    difficulty=7,
    category="technical"
)

# Returns: List of up to 10 templates with stem, type, correct_answer, etc.
```

### Tool 3: Get Difficulty Keywords
```python
keywords = get_difficulty_keywords(difficulty=7, category="technical")

# Returns:
{
    "difficulty": 7,
    "category": "technical",
    "keywords": ["LLM", "Transformer", "Attention", ...],
    "concepts": [{"name": "...", "acronym": "...", "definition": "...", "key_points": [...]}, ...],
    "example_questions": [{"stem": "...", "type": "...", "difficulty_score": 7.0, ...}, ...]
}
```

### Tool 4: Validate Question Quality
```python
# Single validation
result = validate_question_quality(
    stem="What is RAG?",
    question_type="multiple_choice",
    choices=["A) Retrieval", "B) Generation", "C) Both", "D) Neither"],
    correct_answer="C"
)

# Batch validation
results = validate_question_quality(
    stem=["Question 1", "Question 2"],
    question_type=["short_answer", "true_false"],
    choices=[None, ["True", "False"]],
    correct_answer=["Answer 1", "True"],
    batch=True
)

# Returns: dict or list[dict] with is_valid, score, rule_score, final_score, feedback, issues, recommendation
```

### Tool 5: Save Generated Question
```python
result = save_generated_question(
    item_type="multiple_choice",
    stem="What is RAG?",
    choices=["A) Retrieval", "B) Generation", "C) Both", "D) Neither"],
    correct_key="C",
    difficulty=7,
    categories=["LLM", "RAG"],
    round_id="sess_123_1_2025-11-09T10:30:00Z",
    validation_score=0.92,
    explanation="RAG combines retrieval with generation..."
)

# Returns on success:
{
    "question_id": "550e8400-e29b-41d4-a716-446655440001",
    "round_id": "sess_123_1_2025-11-09T10:30:00Z",
    "saved_at": "2025-11-09T10:35:00Z",
    "success": True
}
```

### Tool 6: Score & Explain Answer
```python
# Multiple Choice
result = score_and_explain(
    session_id="sess_001",
    user_id="user_001",
    question_id="q_001",
    question_type="multiple_choice",
    user_answer="B",
    correct_answer="B"
)

# Short Answer
result = score_and_explain(
    session_id="sess_001",
    user_id="user_001",
    question_id="q_003",
    question_type="short_answer",
    user_answer="RAG combines retrieval and generation",
    correct_keywords=["RAG", "retrieval", "generation"],
    difficulty=7
)

# Returns:
{
    "attempt_id": "att_550e8400-e29b-41d4-a716-446655440002",
    "session_id": "sess_001",
    "question_id": "q_001",
    "user_id": "user_001",
    "is_correct": True,
    "score": 100,
    "explanation": "Your answer demonstrates solid understanding of RAG principles...",
    "keyword_matches": ["RAG", "retrieval", "generation"],
    "feedback": None,
    "graded_at": "2025-11-09T10:40:00Z"
}
```

---

## Input Validation Summary

### Tool 1
- `user_id`: str, non-empty, valid UUID format ✓

### Tool 2
- `interests`: list[str], 1-10 items, each 1-50 chars ✓
- `difficulty`: int, 1-10 ✓
- `category`: str, one of {technical, business, general} ✓

### Tool 3
- `difficulty`: int, 1-10 ✓
- `category`: str, one of {technical, business, general} ✓

### Tool 4
- `stem`: str, max 250 chars, non-empty ✓
- `question_type`: str, one of {multiple_choice, true_false, short_answer} ✓
- `choices`: list[str], required for MC (4-5 items) ✓
- `correct_answer`: str, required for MC/TF ✓

### Tool 5
- `item_type`: str, one of {multiple_choice, true_false, short_answer} ✓
- `stem`: str, max 2000 chars, non-empty ✓
- `choices`: list[str], required for MC ✓
- `correct_key`: str, required for MC/TF, must be in choices ✓
- `correct_keywords`: list[str], required for short_answer ✓
- `difficulty`: int, 1-10 ✓
- `categories`: list[str], non-empty ✓
- `round_id`: str, format: "session_id_round_number_timestamp" ✓

### Tool 6
- `session_id`: str, non-empty ✓
- `user_id`: str, non-empty ✓
- `question_id`: str, non-empty ✓
- `question_type`: str, one of {multiple_choice, true_false, short_answer} ✓
- `user_answer`: str, non-empty ✓
- `correct_answer`: str, required for MC/TF ✓
- `correct_keywords`: list[str], required for short_answer ✓

---

## Scoring Rules (Tool 6)

### Multiple Choice
```
is_correct = (user_answer.upper() == correct_answer.upper())
score = 100 if is_correct else 0
```

### True/False
```
is_correct = (user_answer.lower() == correct_answer.lower())
score = 100 if is_correct else 0
```

### Short Answer
```
is_correct = (llm_score >= 80)
score = llm_score (0-100 from LLM)

Criteria:
- 40 pts: Key keywords/concepts
- 40 pts: Semantic correctness
- 20 pts: Clarity/completeness

Partial Credit: 70-79 → is_correct=False but score > 0
```

---

## Error Responses

### When Tool Call Fails
All tools follow error handling patterns:

1. **Input Validation Error**: Raise `ValueError` or `TypeError` immediately
2. **Database Error**: Use fallback/graceful degradation
3. **LLM Error**: Return default score or empty results
4. **Timeout**: Return cached or fallback value

### Common Fallbacks
- **Tool 1**: Return default profile with "beginner" level
- **Tool 2**: Return empty list `[]`
- **Tool 3**: Return default keywords (communication, teamwork, etc.)
- **Tool 4**: Return `is_valid=False` with feedback
- **Tool 5**: Queue for retry, return `success=False`
- **Tool 6**: Return `score=50`, `is_correct=False`

---

## Performance Metrics

| Tool | Timeout | Retries | Caching | Parallel |
|------|---------|---------|---------|----------|
| Tool 1 | 3s | 3x | No | N/A |
| Tool 2 | 5s | 1x | DB only | N/A |
| Tool 3 | 2s | 1x | 1hr TTL | N/A |
| Tool 4 | 10s | 0 | No | Maybe (future) |
| Tool 5 | 10s | Retry queue | No | Maybe (future) |
| Tool 6 | 15s | 0 | No | Yes (batch) |

---

## Integration Points

### Mode 1 Pipeline (Question Generation)
```
User Request
    ↓
Tool 1: Get Profile
    ↓
Tool 2: Search Templates (optional)
    ↓
Tool 3: Get Keywords
    ↓
LLM: Generate Questions
    ↓
Tool 4: Validate (per question)
    ↓
Tool 5: Save (if valid)
    ↓
Response: Generated Questions
```

### Mode 2 Pipeline (Auto-Scoring)
```
User Answer Submission
    ↓
Tool 6: Score & Explain
    ├─ MC/TF: Exact match (0 or 100)
    ├─ SA: LLM score (0-100) + keywords
    └─ Generate explanation + references
    ↓
Response: Score, Explanation, Feedback
```

---

## File Locations

| Component | File |
|-----------|------|
| Tool 1 | `/src/agent/tools/user_profile_tool.py` |
| Tool 2 | `/src/agent/tools/search_templates_tool.py` |
| Tool 3 | `/src/agent/tools/difficulty_keywords_tool.py` |
| Tool 4 | `/src/agent/tools/validate_question_tool.py` |
| Tool 5 | `/src/agent/tools/save_question_tool.py` |
| Tool 6 | `/src/agent/tools/score_and_explain_tool.py` |
| FastMCP Wrappers | `/src/agent/fastmcp_server.py` |
| Agent | `/src/agent/llm_agent.py` |
| Config | `/src/agent/config.py` |

---

## REQ Mapping

| Tool | REQ ID | Phase |
|------|--------|-------|
| Tool 1 | REQ-A-Mode1-Tool1 | Mode 1 (Generate) |
| Tool 2 | REQ-A-Mode1-Tool2 | Mode 1 (Generate) |
| Tool 3 | REQ-A-Mode1-Tool3 | Mode 1 (Generate) |
| Tool 4 | REQ-A-Mode1-Tool4 | Mode 1 (Validate) |
| Tool 5 | REQ-A-Mode1-Tool5 | Mode 1 (Save) |
| Tool 6 | REQ-A-Mode2-Tool6 | Mode 2 (Score) |

---

## Constants & Ranges

```python
# Question Types
QUESTION_TYPES = {"multiple_choice", "true_false", "short_answer"}

# Categories
SUPPORTED_CATEGORIES = {"technical", "business", "general"}

# Difficulty Scale
DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 10
# 1-3: Beginner, 4-6: Intermediate, 7-9: Advanced, 10: Expert

# Scoring Thresholds
PASS_THRESHOLD = 0.85          # Tool 4
REVISE_THRESHOLD = (0.70, 0.85)  # Tool 4
REJECT_THRESHOLD = 0.70        # Tool 4

# Short Answer Scoring
HIGH_SCORE_THRESHOLD = 80      # Tool 6 (is_correct)
PARTIAL_CREDIT_RANGE = (70, 79)  # Tool 6 (partial credit)

# Text Limits
STEM_MAX_LENGTH = 250          # Tool 4
QUESTION_STEM_MAX = 2000       # Tool 5
EXPLANATION_MIN_LENGTH = 500   # Tool 6

# Counts
MIN_CHOICES = 4
MAX_CHOICES = 5
MIN_REFERENCE_LINKS = 3
```

---

## LLM Configuration

```python
Model: Google Gemini 2.0 Flash
Temperature: 0.7
Max Tokens: 1024
Top P: 0.95
Timeout: 30 seconds
```

---

## Testing Patterns

### Unit Test Template (Tool 1)
```python
def test_get_user_profile_valid():
    result = get_user_profile(user_id="550e8400-e29b-41d4-a716-446655440000")
    assert "user_id" in result
    assert result["self_level"] in {"beginner", "intermediate", "advanced"}
    assert 0 <= result["years_experience"] <= 60
    assert 0 <= result["previous_score"] <= 100

def test_get_user_profile_invalid():
    with pytest.raises(ValueError):
        get_user_profile(user_id="invalid-uuid")
```

### Integration Test Template (Tool 4 → Tool 5)
```python
def test_validate_then_save():
    # Tool 4: Validate
    validation = validate_question_quality(
        stem="Question", question_type="short_answer", correct_answer="ans"
    )
    assert validation["final_score"] >= 0.70
    
    # Tool 5: Save if valid
    if validation["is_valid"]:
        save_result = save_generated_question(
            item_type="short_answer",
            stem="Question",
            correct_keywords=["keyword"],
            validation_score=validation["final_score"]
        )
        assert save_result["success"] is True
```

---

## Debugging Checklist

- [ ] Check input types match signature
- [ ] Validate input values in allowed ranges
- [ ] Enable verbose logging: `AGENT_CONFIG["verbose"] = True`
- [ ] Check database connectivity for Tools 1, 2, 3, 5
- [ ] Check GEMINI_API_KEY environment variable for Tools 4, 6
- [ ] Review fallback values on Tool failures
- [ ] Check retry queue for Tool 5 failures (`get_retry_queue()`)
- [ ] Verify round_id format: "session_id_round_number_timestamp"

