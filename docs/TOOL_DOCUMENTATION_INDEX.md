# Tool 1-6 Documentation Index

Complete documentation of the 6-tool agent system for AI-driven adaptive testing and question generation.

## Quick Navigation

### For Quick Reference (5 minutes)

Start here: **[TOOL_QUICK_REFERENCE.md](TOOL_QUICK_REFERENCE.md)**

- Tool call examples with real inputs/outputs
- Input validation checklist
- Scoring rules by question type
- Error handling patterns
- Performance metrics table
- File locations and REQ mapping
- Constants and debugging checklist

### For Detailed Understanding (30 minutes)

Start here: **[TOOL_DEFINITIONS_SUMMARY.md](TOOL_DEFINITIONS_SUMMARY.md)**

- Complete signature and type information
- Comprehensive input/output documentation
- Database query details and caching strategies
- LLM prompts and validation rules
- Error handling with fallback values
- Pipeline workflows (Mode 1 & Mode 2)
- Tool integration patterns

---

## Tool Inventory

| Tool | Purpose | Mode | Status |
|------|---------|------|--------|
| **Tool 1** | Get User Profile | Generation | Implemented |
| **Tool 2** | Search Question Templates | Generation | Implemented |
| **Tool 3** | Get Difficulty Keywords | Generation | Implemented |
| **Tool 4** | Validate Question Quality | Validation | Implemented |
| **Tool 5** | Save Generated Question | Persistence | Implemented |
| **Tool 6** | Score & Explain Answer | Grading | Implemented |

---

## Implementation Files

### Tool Implementation Files

```
src/agent/tools/
├── user_profile_tool.py          # Tool 1 (REQ-A-Mode1-Tool1)
├── search_templates_tool.py       # Tool 2 (REQ-A-Mode1-Tool2)
├── difficulty_keywords_tool.py    # Tool 3 (REQ-A-Mode1-Tool3)
├── validate_question_tool.py      # Tool 4 (REQ-A-Mode1-Tool4)
├── save_question_tool.py          # Tool 5 (REQ-A-Mode1-Tool5)
├── score_and_explain_tool.py      # Tool 6 (REQ-A-Mode2-Tool6)
└── __init__.py
```

### Integration Files

```
src/agent/
├── fastmcp_server.py             # FastMCP wrappers for all 6 tools
├── llm_agent.py                  # Agent orchestration & execution
├── config.py                      # LLM & Tool configuration
├── prompts/
│   └── react_prompt.py            # ReAct prompt template
└── data_contracts.py              # Pydantic schemas
```

---

## Key Concepts

### Two-Mode Architecture

#### Mode 1: Question Generation (Tools 1-5)

```
User Profile → Template Search → Keywords → LLM Generation → Validation → Save
     [1]           [2]              [3]          LLM          [4]         [5]
```

**Use Case**: Generate adaptive test questions tailored to user profile and difficulty

#### Mode 2: Auto-Scoring (Tool 6)

```
User Answer → Question Metadata → LLM Score & Explain → Explanation + References
    [input]       [metadata]              [6]                  [output]
```

**Use Case**: Auto-grade answers with semantic understanding and learning explanations

---

## Required Knowledge

### Understanding Tool 1

- User profile schema (self_level, years_experience, job_role, interests)
- Fallback mechanism for database failures
- UUID validation for user_id parameter

### Understanding Tool 2

- Difficulty range scaling (±1.5 from input)
- Template filtering by category and interests
- Graceful empty result handling

### Understanding Tool 3

- In-memory caching with TTL (1 hour)
- Thread-safe cache access with locks
- Concept structures with acronyms and key points

### Understanding Tool 4

- 2-stage validation: LLM semantic + rule-based
- Scoring thresholds: Pass (>=0.85), Revise (0.70-0.85), Reject (<0.70)
- Batch processing support for multiple questions

### Understanding Tool 5

- Round ID parsing (format: session_id_round_number_timestamp)
- Answer schema construction for all question types
- Retry queue mechanism for failed saves

### Understanding Tool 6

- Question-type-specific scoring (MC: exact match, SA: LLM-based)
- Partial credit range (70-79 points)
- Keyword matching for short answers (case-insensitive substring)

---

## Workflows & Pipelines

### Mode 1 Workflow: Question Generation

1. **Tool 1**: Retrieve user profile (self_level, interests, previous_score)
2. **Tool 2**: Search templates for few-shot examples (optional)
3. **Tool 3**: Get difficulty-specific keywords and concepts
4. **LLM**: Generate questions using profile + keywords + templates as context
5. **Tool 4**: Validate each generated question (LLM semantic + rules)
6. **Tool 5**: Save questions with final_score >= 0.70
7. **Return**: List of validated, saved questions with metadata

**Key Files**:

- Agent: `src/agent/llm_agent.py` (method: `generate_questions()`)
- Prompt: `src/agent/prompts/react_prompt.py`
- Config: `src/agent/config.py` (AGENT_CONFIG, TOOL_CONFIG)

### Mode 2 Workflow: Auto-Scoring

1. **Input**: User answer + question metadata (question_id, question_type, etc.)
2. **Tool 6 - Scoring Logic**:
   - MC: Exact string match (case-insensitive) → 0 or 100
   - TF: Exact string match (case-insensitive) → 0 or 100
   - SA: LLM semantic evaluation (0-100) + keyword matching
3. **Tool 6 - Explanation**: Generate explanation (>= 500 chars) + 3+ references
4. **Tool 6 - Feedback**: Add partial credit feedback if applicable (70-79 points)
5. **Return**: Attempt result with is_correct, score, explanation, feedback

**Key Files**:

- Agent: `src/agent/llm_agent.py` (method: `score_and_explain()`)
- Batch: `src/agent/llm_agent.py` (method: `submit_answers()`)

---

## Error Handling Strategy

### Error Types & Responses

| Error Type | Tools | Response | Example |
|-----------|-------|----------|---------|
| Input Validation | All | Raise ValueError/TypeError | Invalid UUID, out-of-range difficulty |
| Database Unavailable | 1, 2, 3, 5 | Return fallback/empty | Tool 1: default profile; Tool 2: [] |
| LLM Timeout/Failure | 4, 6 | Return default score | Tool 4: score=0.5; Tool 6: score=50 |
| Network Error | All | Retry (if configured) | Tool 1 retries 3x |
| Partial Failure | 4, 5 | Continue with partial results | Tool 4: batch continues per item |

### Fallback Values

**Tool 1 (User Profile)**:

```python
{
    "self_level": "beginner",
    "years_experience": 0,
    "job_role": "Unknown",
    "duty": "Not specified",
    "interests": [],
    "previous_score": 0
}
```

**Tool 2 (Templates)**: Empty list `[]`

**Tool 3 (Keywords)**: Default keywords (communication, problem-solving, etc.)

**Tool 4 (Validation)**: `is_valid=False`, `recommendation="reject"`

**Tool 5 (Save)**: Queue for retry, return `success=False, queued_for_retry=True`

**Tool 6 (Score)**: `score=50, is_correct=False`

---

## Data Validation Rules

### Tool 1: get_user_profile

```
user_id: UUID string (36 chars, format: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
```

### Tool 2: search_question_templates

```
interests: list[str]
  - Length: 1-10 items
  - Each item: 1-50 characters
difficulty: int (1-10)
category: str (one of: "technical", "business", "general")
```

### Tool 3: get_difficulty_keywords

```
difficulty: int (1-10)
category: str (one of: "technical", "business", "general")
```

### Tool 4: validate_question_quality

```
stem: str (1-250 chars)
question_type: str (one of: "multiple_choice", "true_false", "short_answer")
choices: list[str] | None (required for MC, 4-5 items)
correct_answer: str | None (required for MC/TF)
batch: bool (default: False)
```

### Tool 5: save_generated_question

```
item_type: str (one of: "multiple_choice", "true_false", "short_answer")
stem: str (1-2000 chars)
choices: list[str] | None (required for MC)
correct_key: str | None (required for MC/TF, must be in choices)
correct_keywords: list[str] | None (required for short_answer)
difficulty: int (1-10, default: 5)
categories: list[str] (non-empty, default: ["general"])
round_id: str (format: "session_id_round_number_timestamp")
validation_score: float | None (0.0-1.0)
explanation: str | None
```

### Tool 6: score_and_explain

```
session_id: str (non-empty)
user_id: str (non-empty)
question_id: str (non-empty)
question_type: str (one of: "multiple_choice", "true_false", "short_answer")
user_answer: str (non-empty)
correct_answer: str | None (required for MC/TF)
correct_keywords: list[str] | None (required for short_answer)
difficulty: int | None (1-10)
category: str | None
```

---

## Performance Characteristics

### Timeouts (Configurable)

```
Tool 1: 3 seconds
Tool 2: 5 seconds
Tool 3: 2 seconds
Tool 4: 10 seconds
Tool 5: 10 seconds
Tool 6: 15 seconds
```

### Caching

- **Tool 1**: No caching (single user lookup)
- **Tool 2**: Query optimization only
- **Tool 3**: In-memory cache, 1-hour TTL
- **Tool 4**: No caching
- **Tool 5**: No caching
- **Tool 6**: No caching (real-time scoring)

### Retries

- **Tool 1**: 3 retries with exponential backoff
- **Tool 2**: 1 retry
- **Tool 3**: 1 retry
- **Tool 4**: No retries (validation is deterministic)
- **Tool 5**: Retry queue mechanism
- **Tool 6**: No retries (real-time grading)

---

## Testing & Development

### Test Locations

```
tests/
├── test_agent/
│   ├── test_tools/
│   │   ├── test_user_profile_tool.py
│   │   ├── test_search_templates_tool.py
│   │   ├── test_difficulty_keywords_tool.py
│   │   ├── test_validate_question_tool.py
│   │   ├── test_save_question_tool.py
│   │   └── test_score_and_explain_tool.py
│   └── test_llm_agent.py
```

### Unit Test Pattern

```python
def test_tool_valid_input():
    result = tool_func(valid_input)
    assert expected_structure_check(result)

def test_tool_invalid_input():
    with pytest.raises((ValueError, TypeError)):
        tool_func(invalid_input)

def test_tool_fallback():
    result = tool_func(valid_input_but_missing_dependency)
    assert fallback_value_check(result)
```

### Integration Test Pattern

```python
async def test_mode1_pipeline():
    # Tool 1 → Tool 2 → Tool 3 → LLM → Tool 4 → Tool 5
    request = GenerateQuestionsRequest(survey_id="...", round_idx=1)
    response = await agent.generate_questions(request)
    assert response.items
    assert all(item.validation_score >= 0.70 for item in response.items)
```

---

## Troubleshooting

### Common Issues

**Tool 1 Returns Default Profile**

- Check: User exists in database
- Check: Database connectivity
- Check: user_id format is valid UUID

**Tool 2 Returns Empty List**

- Check: Templates exist in database with matching interests
- Check: Difficulty range: ±1.5 from input
- Check: Category is one of {technical, business, general}

**Tool 3 Returns Fallback Keywords**

- Check: Database has DifficultyKeyword records
- Check: In-memory cache was cleared
- Check: Difficulty (1-10) and category are valid

**Tool 4 Returns is_valid=False**

- Check: Question stem > 250 chars (trim required)
- Check: MC questions have 4-5 choices
- Check: Correct answer is in choices list
- Check: No duplicate choices
- Check: LLM API key is set (GEMINI_API_KEY)

**Tool 5 Returns success=False**

- Check: Database is running
- Check: Question model is defined in SQLAlchemy
- Check: round_id format is correct
- Check: Retry queue via `get_retry_queue()`

**Tool 6 Returns score=50**

- Check: LLM API key is set (GEMINI_API_KEY)
- Check: LLM response is valid JSON
- Check: correct_keywords are provided for short answers
- Check: Question type is one of {multiple_choice, true_false, short_answer}

---

## Related Documentation

- **User Scenarios**: `docs/user_scenarios_mvp1.md`
- **Architecture**: `docs/PROJECT_SETUP_PROMPT.md`
- **Requirements**: `docs/feature_requirement_mvp1.md`
- **Progress Tracking**: `docs/DEV-PROGRESS.md`
- **API Endpoints**: `src/backend/api/` (FastAPI routes)

---

## Support & Questions

For specific tool issues, refer to:

1. Tool implementation file in `src/agent/tools/`
2. FastMCP wrapper in `src/agent/fastmcp_server.py`
3. Test file in `tests/test_agent/test_tools/`
4. This documentation (TOOL_DEFINITIONS_SUMMARY.md or TOOL_QUICK_REFERENCE.md)

For REQ-related questions, check:

- REQ ID in tool docstring (e.g., "REQ: REQ-A-Mode1-Tool1")
- Corresponding requirement in `docs/feature_requirement_mvp1.md`
