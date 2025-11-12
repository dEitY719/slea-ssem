# Tool 1-6 Definitions & Interfaces - Complete Reference

## Overview

The slea-ssem agent system provides 6 specialized tools for AI-driven adaptive testing and question generation. These tools are organized into two pipelines:

- **Mode 1 Pipeline (Tools 1-5)**: Question generation with LLM + validation
- **Mode 2 Pipeline (Tool 6)**: Auto-scoring and explanation generation

All tools use LangChain's `@tool` decorator and are registered in the FastMCP server.

---

## Tool 1: Get User Profile (REQ-A-Mode1-Tool1)

**Purpose**: Retrieve user's self-assessment profile for context-aware question generation.

### Location

- Implementation: `/home/bwyoon/para/project/slea-ssem/src/agent/tools/user_profile_tool.py`
- FastMCP wrapper: `/home/bwyoon/para/project/slea-ssem/src/agent/fastmcp_server.py` (lines 29-77)

### Signature

```python
def get_user_profile(user_id: str) -> dict[str, Any]
```

### Input Parameters

| Parameter | Type | Required | Description | Validation |
|-----------|------|----------|-------------|-----------|
| `user_id` | str | Yes | User ID (UUID format) | Must be non-empty UUID string |

### Output Format

```python
{
    "user_id": str,                    # Echo of input user_id
    "self_level": str,                 # "beginner" | "intermediate" | "advanced"
    "years_experience": int,           # 0-60 years
    "job_role": str,                   # Job title/role
    "duty": str,                       # Main responsibilities
    "interests": list[str],            # List of interest categories (e.g., ["LLM", "RAG"])
    "previous_score": int              # Previous test score (0-100)
}
```

### Error Handling

- **Invalid user_id**: Raises `ValueError` if not valid UUID format
- **Database error**: Returns default profile with fallback values
- **Type error**: Raises `TypeError` if user_id is not string

### Fallback Profile (on error)

```python
{
    "user_id": <input>,
    "self_level": "beginner",
    "years_experience": 0,
    "job_role": "Unknown",
    "duty": "Not specified",
    "interests": [],
    "previous_score": 0
}
```

### Database Query

- Table: `UserProfileSurvey`
- Filter: `user_id` matching (handles both int and UUID)
- Sort: By `submitted_at` descending (latest first)

### Notes

- Includes retry logic (up to 3 attempts)
- Timeout: 3 seconds (configurable via TOOL_CONFIG)
- No parallel calls necessary (single lookup)

---

## Tool 2: Search Question Templates (REQ-A-Mode1-Tool2)

**Purpose**: Search existing question templates for few-shot examples to improve LLM-generated question quality.

### Location

- Implementation: `/home/bwyoon/para/project/slea-ssem/src/agent/tools/search_templates_tool.py`
- FastMCP wrapper: `/home/bwyoon/para/project/slea-ssem/src/agent/fastmcp_server.py` (lines 80-122)

### Signature

```python
def search_question_templates(
    interests: list[str],
    difficulty: int,
    category: str
) -> list[dict[str, Any]]
```

### Input Parameters

| Parameter | Type | Required | Constraints | Example |
|-----------|------|----------|------------|---------|
| `interests` | list[str] | Yes | 1-10 items, each 1-50 chars | ["LLM", "RAG", "Agent Architecture"] |
| `difficulty` | int | Yes | 1-10 range | 7 (for advanced) |
| `category` | str | Yes | One of: "technical", "business", "general" | "technical" |

### Difficulty Scale

- **1-3**: Beginner
- **4-6**: Intermediate
- **7-9**: Advanced
- **10**: Expert

### Output Format

```python
[
    {
        "id": str,                          # Template UUID
        "stem": str,                        # Question text
        "type": str,                        # "multiple_choice" | "true_false" | "short_answer"
        "choices": list[str],               # Answer choices (empty for short_answer/true_false)
        "correct_answer": str,              # Correct answer key or text
        "correct_rate": float,              # 0.0-1.0 success rate
        "usage_count": int,                 # Usage frequency
        "avg_difficulty_score": float       # 1.0-10.0 average difficulty
    },
    # ... up to 10 results, sorted by correct_rate descending, then usage_count
]
```

### Database Query

- Table: `QuestionTemplate`
- Filters:
  - `category` = input category
  - `domain` IN input interests (list filtering)
  - `avg_difficulty_score` BETWEEN [difficulty - 1.5, difficulty + 1.5]
  - `usage_count > 0` (only validated templates)
  - `is_active = True`
- Sort: By `correct_rate` descending, then `usage_count` descending
- Limit: 10 results

### Error Handling

- **Invalid inputs**: Raises `ValueError` or `TypeError` with descriptive message
- **No results found**: Returns empty list `[]` (graceful degradation)
- **Database error**: Returns `[]` with warning log
- **Invalid interest items**: Raises `ValueError` if any interest exceeds 50 chars

### Notes

- Difficulty range: ±1.5 from input (e.g., difficulty=7 searches 5.5-8.5)
- Results prioritize high success rate for quality examples
- Timeout: 5 seconds (configurable via TOOL_CONFIG)
- No caching at tool level (handled by query optimization)

---

## Tool 3: Get Difficulty Keywords (REQ-A-Mode1-Tool3)

**Purpose**: Retrieve difficulty-specific keywords and concepts to guide LLM question generation.

### Location

- Implementation: `/home/bwyoon/para/project/slea-ssem/src/agent/tools/difficulty_keywords_tool.py`
- FastMCP wrapper: `/home/bwyoon/para/project/slea-ssem/src/agent/fastmcp_server.py` (lines 125-161)

### Signature

```python
def get_difficulty_keywords(difficulty: int, category: str) -> dict[str, Any]
```

### Input Parameters

| Parameter | Type | Required | Constraints | Example |
|-----------|------|----------|------------|---------|
| `difficulty` | int | Yes | 1-10 range | 7 |
| `category` | str | Yes | "technical", "business", or "general" | "technical" |

### Output Format

```python
{
    "difficulty": int,                  # Echo of input
    "category": str,                    # Echo of input
    "keywords": list[str],              # 5-20 keywords for difficulty/category
    "concepts": list[dict],             # Up to 10 concept definitions
    "example_questions": list[dict]     # Up to 5 example questions
}
```

### Concepts Structure

```python
{
    "name": str,                        # Concept name (e.g., "Effective Communication")
    "acronym": str,                     # Short acronym (e.g., "EC")
    "definition": str,                  # Concept definition
    "key_points": list[str]             # 3-5 key points/tips
}
```

### Example Questions Structure

```python
{
    "stem": str,                        # Question text
    "type": str,                        # "short_answer" | "multiple_choice" | "true_false"
    "difficulty_score": float,          # 1.0-10.0 actual difficulty
    "answer_summary": str               # Brief expected answer
}
```

### Database Query

- Table: `DifficultyKeyword`
- Filters:
  - `difficulty` = input difficulty
  - `category` = input category
- Returns: Single record (difficulty+category is unique key)

### Caching Strategy

- **In-memory cache** with 1-hour TTL
- Cache key format: `"{difficulty}_{category}"`
- Thread-safe locking for cache access
- Cache hit → return immediately
- Cache miss → query DB and populate cache

### Fallback Keywords (on error or missing DB record)

```python
{
    "difficulty": 5,
    "category": "general",
    "keywords": [
        "Communication", "Problem Solving", "Teamwork",
        "Critical Thinking", "Adaptability"
    ],
    "concepts": [
        {
            "name": "Effective Communication",
            "acronym": "EC",
            "definition": "Clear and efficient exchange of information",
            "key_points": ["Clear message formulation", "Active listening", "Feedback exchange"]
        },
        {
            "name": "Problem-Solving Approach",
            "acronym": "PSA",
            "definition": "Systematic method for addressing challenges",
            "key_points": ["Define the problem", "Generate solutions", "Evaluate and implement"]
        }
    ],
    "example_questions": [
        {
            "stem": "What is effective communication in a team?",
            "type": "short_answer",
            "difficulty_score": 5.0,
            "answer_summary": "Clear exchange of information with active listening"
        }
    ]
}
```

### Error Handling

- **Invalid inputs**: Raises `ValueError` or `TypeError`
- **Cache miss + DB miss**: Returns default keywords
- **Database error**: Returns cached value or default
- Graceful degradation ensures LLM always has keyword guidance

### Notes

- Timeout: 2 seconds (configurable via TOOL_CONFIG)
- Cache expires after 1 hour (in production, use expiration mechanism)
- Used during LLM prompt engineering for question generation

---

## Tool 4: Validate Question Quality (REQ-A-Mode1-Tool4)

**Purpose**: Validate AI-generated questions using 2-stage validation (LLM semantic + rule-based).

### Location

- Implementation: `/home/bwyoon/para/project/slea-ssem/src/agent/tools/validate_question_tool.py`
- FastMCP wrapper: `/home/bwyoon/para/project/slea-ssem/src/agent/fastmcp_server.py` (lines 164-209)

### Signature

```python
def validate_question_quality(
    stem: str | list[str],
    question_type: str | list[str],
    choices: list[str] | list[list[str]] | None = None,
    correct_answer: str | list[str] = None,
    batch: bool = False
) -> dict[str, Any] | list[dict[str, Any]]
```

### Input Parameters (Single)

| Parameter | Type | Required | Constraints | Example |
|-----------|------|----------|------------|---------|
| `stem` | str | Yes | Max 250 chars | "What is RAG?" |
| `question_type` | str | Yes | "multiple_choice", "true_false", "short_answer" | "multiple_choice" |
| `choices` | list[str] | Conditional | Required for MC (4-5 items) | ["A", "B", "C", "D"] |
| `correct_answer` | str | Conditional | Required for MC/TF | "B" |
| `batch` | bool | No | If True, inputs treated as lists | False |

### Input Parameters (Batch)

When `batch=True`, parameters become lists:

```python
stem: list[str]
question_type: list[str]
choices: list[list[str]] | None
correct_answer: list[str]
```

### Output Format (Single)

```python
{
    "is_valid": bool,                   # True if final_score >= 0.70
    "score": float,                     # LLM semantic score (0.0-1.0)
    "rule_score": float,                # Rule-based score (0.0-1.0)
    "final_score": float,               # min(score, rule_score)
    "feedback": str,                    # Human-readable feedback (Korean)
    "issues": list[str],                # List of detected problems
    "recommendation": str               # "pass" (>=0.85) | "revise" (0.70-0.85) | "reject" (<0.70)
}
```

### Output Format (Batch)

Returns `list[dict]` with same structure as above for each question.

### Validation Rules (Rule-Based)

| Rule | Condition | Score Impact | Issue Message |
|------|-----------|--------------|---------------|
| Stem length | > 250 chars | -0.2 | "Stem length exceeds maximum" |
| MC choices count | Not 4-5 items | -0.2 | "Invalid number of choices" |
| Answer in choices | answer ∉ choices | -0.3 | "Correct answer not found in choices" |
| Duplicate choices | len(choices) ≠ len(set(choices)) | -0.15 | "Duplicate choices detected" |

### LLM Validation (Semantic)

LLM evaluates on scale 0.0-1.0 considering:

1. **Clarity**: Is the question clear and unambiguous?
2. **Appropriateness**: Is difficulty level appropriate?
3. **Correctness**: Is correct answer objective and verifiable?
4. **Bias**: Any biases or inappropriate language?
5. **Format**: Is format valid and properly structured?

LLM returns score only (no explanation).

### Score Thresholds

- **Pass**: >= 0.85 (ready to save immediately)
- **Revise**: 0.70-0.85 (needs improvement before saving)
- **Reject**: < 0.70 (should be regenerated)

### Final Score Calculation

```
final_score = min(llm_score, rule_score)
is_valid = final_score >= 0.70
```

### Feedback Examples (Korean)

- **Pass**: "질문이 우수한 품질입니다. 즉시 저장할 수 있습니다."
- **Revise**: "질문이 기본 기준을 충족하지만 개선이 가능합니다. 피드백을 바탕으로 재생성을 권장합니다."
- **Reject**: "질문이 기준을 충족하지 않습니다. 새로운 질문 생성을 권장합니다."

### Error Handling

- **Invalid inputs**: Raises `ValueError` or `TypeError` with detailed message
- **LLM failure**: Returns `DEFAULT_LLM_SCORE = 0.5`
- **Batch processing**: Continues on individual errors, returns partial results

### Notes

- Supports both single and batch validation
- LLM response expected: float between 0.0 and 1.0 only (no explanation)
- Feedback and issues are combined for actionable output

---

## Tool 5: Save Generated Question (REQ-A-Mode1-Tool5)

**Purpose**: Save validated questions to database with metadata traceability.

### Location

- Implementation: `/home/bwyoon/para/project/slea-ssem/src/agent/tools/save_question_tool.py`
- FastMCP wrapper: `/home/bwyoon/para/project/slea-ssem/src/agent/fastmcp_server.py` (lines 212-270)

### Signature

```python
def save_generated_question(
    item_type: str,
    stem: str,
    choices: list[str] | None = None,
    correct_key: str | None = None,
    correct_keywords: list[str] | None = None,
    difficulty: int = 5,
    categories: list[str] | None = None,
    round_id: str = "",
    validation_score: float | None = None,
    explanation: str | None = None
) -> dict[str, Any]
```

### Input Parameters

| Parameter | Type | Required | Constraints | Example |
|-----------|------|----------|------------|---------|
| `item_type` | str | Yes | "multiple_choice", "true_false", "short_answer" | "multiple_choice" |
| `stem` | str | Yes | Max 2000 chars, non-empty | "What is RAG?" |
| `choices` | list[str] | Conditional | Required for MC (4-5 items) | ["A", "B", "C", "D"] |
| `correct_key` | str | Conditional | Required for MC/TF, must be in choices | "B" |
| `correct_keywords` | list[str] | Conditional | Required for short_answer | ["RAG", "retrieval", "generation"] |
| `difficulty` | int | No | 1-10 range | 7 |
| `categories` | list[str] | No | Domain categories, default ["general"] | ["LLM", "RAG"] |
| `round_id` | str | No | Format: "session_id_round_timestamp" | "sess_123_1_2025-11-09T10:30:00Z" |
| `validation_score` | float | No | Tool 4's final_score (metadata) | 0.92 |
| `explanation` | str | No | Optional explanation text | "RAG combines retrieval with generation..." |

### Round ID Format

```
Format: {session_id}_{round_number}_{timestamp}
Example: sess_abc123_1_2025-11-06T10:30:00Z
- session_id: Extracted for DB linking
- round_number: 1 or 2 (defaults to 1 if invalid)
- timestamp: ISO 8601 format
```

### Output Format (Success)

```python
{
    "question_id": str,                 # UUID of saved question
    "round_id": str,                    # Echo of input round_id
    "saved_at": str,                    # ISO 8601 timestamp
    "success": True
}
```

### Output Format (Failure - Queued for Retry)

```python
{
    "question_id": None,
    "round_id": str,                    # Echo of input round_id
    "saved_at": str,                    # Timestamp when queued
    "success": False,
    "error": str,                       # Error description
    "queued_for_retry": True            # Indicates queued status
}
```

### Database Persistence

**Table**: `Question`

**Fields Saved**:

```python
{
    "session_id": "unknown",            # Placeholder (filled by orchestration)
    "item_type": str,                   # Input item_type
    "stem": str,                        # Input stem
    "choices": list[str] | None,        # Input choices
    "answer_schema": dict,              # Constructed below
    "difficulty": int,                  # Input difficulty
    "category": str,                    # First category from categories list
    "round": int,                       # Extracted from round_id
    "created_at": datetime              # Automatic timestamp
}
```

### Answer Schema Structure

```python
{
    # Conditional: Type-specific answer data
    "correct_key": str,                 # For MC/TF
    "correct_keywords": list[str],      # For short_answer
    
    # Metadata: Traceability
    "validation_score": float,          # Tool 4 final_score
    "explanation": str                  # Optional explanation
}
```

### Retry Queue

On database failure:

1. Question added to `SAVE_RETRY_QUEUE` (in-memory list)
2. Returns response with `"queued_for_retry": True`
3. Can be retrieved via `get_retry_queue()` and reprocessed via `clear_retry_queue()`

### Error Handling

- **Invalid inputs**: Raises `ValueError` or `TypeError` with validation message
- **Database error**: Rolls back transaction and queues for retry
- **Missing parameters**: Uses defaults or raises error for conditionally required fields

### Helper Functions

```python
# Get queued items for batch retry
def get_retry_queue() -> list[dict[str, Any]]

# Clear queue after successful batch retry
def clear_retry_queue() -> int  # Returns count cleared
```

### Validation Rules

| Condition | Type | Error |
|-----------|------|-------|
| item_type not in allowed | MC/TF/SA | ValueError |
| stem empty or > 2000 | MC/TF/SA | ValueError |
| choices not in MC | MC | ValueError |
| correct_key not in choices | MC | ValueError |
| correct_key not T/F | TF | ValueError |
| correct_keywords empty | SA | ValueError |
| categories empty | All | ValueError |
| difficulty not 1-10 | All | ValueError |
| round_id empty | All | ValueError |

### Notes

- Timeout: 10 seconds (configurable via TOOL_CONFIG)
- Supports batch retry mechanism for resilience
- Metadata stored in answer_schema for audit trail
- Session ID resolved during agent orchestration phase

---

## Tool 6: Score & Explain Answer (REQ-A-Mode2-Tool6)

**Purpose**: Auto-grade user answers with LLM-based scoring and generate educational explanations.

### Location

- Implementation: `/home/bwyoon/para/project/slea-ssem/src/agent/tools/score_and_explain_tool.py`
- FastMCP wrapper: `/home/bwyoon/para/project/slea-ssem/src/agent/fastmcp_server.py` (lines 278-352)

### Signature

```python
def score_and_explain(
    session_id: str,
    user_id: str,
    question_id: str,
    question_type: str,
    user_answer: str,
    correct_answer: str | None = None,
    correct_keywords: list[str] | None = None,
    difficulty: int | None = None,
    category: str | None = None
) -> dict[str, Any]
```

### Input Parameters

| Parameter | Type | Required | Constraints | Example |
|-----------|------|----------|------------|---------|
| `session_id` | str | Yes | Test session ID | "sess_001" |
| `user_id` | str | Yes | User identifier | "user_001" |
| `question_id` | str | Yes | Question identifier | "q_001" |
| `question_type` | str | Yes | "multiple_choice", "true_false", "short_answer" | "short_answer" |
| `user_answer` | str | Yes | User's response text | "RAG combines retrieval and generation" |
| `correct_answer` | str | Conditional | Required for MC/TF | "B" |
| `correct_keywords` | list[str] | Conditional | Required for short_answer | ["RAG", "retrieval", "generation"] |
| `difficulty` | int | No | 1-10 (for hint to LLM) | 7 |
| `category` | str | No | Question category | "LLM" |

### Output Format

```python
{
    "attempt_id": str,                  # UUID of this grading attempt
    "session_id": str,                  # Input session_id
    "question_id": str,                 # Input question_id
    "user_id": str,                     # Input user_id
    "is_correct": bool,                 # True if score >= 80 (SA) or exact match (MC/TF)
    "score": int,                       # 0-100 numeric score
    "explanation": str,                 # Explanation text (>= 500 chars)
    "keyword_matches": list[str],       # Keywords found in short answer (for SA only)
    "feedback": str | None,             # Additional feedback for partial credit (70-79)
    "graded_at": str                    # ISO 8601 timestamp
}
```

### Scoring Logic by Question Type

#### Multiple Choice

- **Method**: Exact string matching (case-insensitive after normalization)
- **is_correct**: `True` if user_answer.upper() == correct_answer.upper()`
- **score**: 100 if correct, 0 if incorrect

#### True/False

- **Method**: Exact string matching (case-insensitive)
- **Accepted values**: "True", "true", "False", "false"
- **is_correct**: `True` if answer matches (case-insensitive)
- **score**: 100 if correct, 0 if incorrect

#### Short Answer

- **Method**: LLM semantic evaluation + keyword matching
- **LLM scoring**: 0-100 based on:
  - 40 points: Presence of key keywords/concepts
  - 40 points: Semantic correctness and relevance
  - 20 points: Clarity and completeness
- **Keyword matching**: Simple substring matching (case-insensitive)
- **is_correct**: `score >= 80`
- **Partial credit**: 70-79 points (is_correct=False but score > 0)

### LLM Scoring Prompt (Short Answer)

```
Evaluate the following short answer response on a scale of 0-100.

User Answer: {user_answer}

Expected Keywords/Concepts: {keywords}

[Difficulty hint if provided]

Scoring criteria:
1. Presence of key keywords/concepts (40 points)
2. Semantic correctness and relevance (40 points)
3. Clarity and completeness (20 points)

Respond with ONLY a JSON object on a single line:
{"score": <number 0-100>, "reasoning": "<brief explanation>"}
```

### Explanation Generation

**LLM generates**:

1. **Explanation text** (>= 500 chars)
2. **Reference links** (>= 3 items with title + URL)

**Tone adjustment**:

- If correct: "affirmative and educational"
- If incorrect: "constructive and helpful"

**Output structure**:

```python
{
    "explanation": str,                 # Generated text (>= 500 chars)
    "reference_links": [
        {"title": str, "url": str},     # At least 3 references
        ...
    ]
}
```

### Partial Credit Feedback

- **Score 70-79**: Encouragement message suggesting review
- **Score < 70**: Constructive message directing to key concepts
- **Score >= 80**: No feedback (is_correct=True)

### Score Thresholds

| Threshold | Meaning | is_correct | Partial Credit |
|-----------|---------|-----------|-----------------|
| >= 80 | Correct | True | None |
| 70-79 | Partial Credit | False | Yes |
| < 70 | Incorrect | False | None |

### Error Handling

- **Invalid inputs**: Raises `ValueError` or `TypeError`
- **LLM timeout/failure**: Returns `DEFAULT_LLM_SCORE = 50`
- **JSON parsing error**: Returns default score with error note
- **Missing conditional parameters**: Raises `ValueError` with requirement

### Keyword Matching (Short Answer)

```python
matched_keywords = []
for keyword in correct_keywords:
    if keyword.lower() in user_answer.lower():
        matched_keywords.append(keyword)
```

### Reference Link Fallback

If LLM fails to generate sufficient references, tool pads with:

```python
[
    {"title": "Reference Material 1", "url": "https://example.com/reference"},
    {"title": "Reference Material 2", "url": "https://example.com/reference"},
    {"title": "Reference Material 3", "url": "https://example.com/reference"}
]
```

### Notes

- Timeout: 15 seconds (configurable via TOOL_CONFIG)
- LLM model: Google Gemini 2.0 Flash
- Temperature: 0.7 (balance creativity/accuracy)
- Max tokens: 1024 (sufficient for explanation + JSON)
- Explanation minimum: 500 characters (enforced)
- Reference minimum: 3 links (enforced)

---

## Tool Integration & Registration

### Tool List in FastMCP Server

Location: `/home/bwyoon/para/project/slea-ssem/src/agent/fastmcp_server.py` (lines 359-366)

```python
TOOLS = [
    get_user_profile,           # Tool 1
    search_question_templates,  # Tool 2
    get_difficulty_keywords,    # Tool 3
    validate_question_quality,  # Tool 4
    save_generated_question,    # Tool 5
    score_and_explain,          # Tool 6
]
```

### Agent Configuration

Location: `/home/bwyoon/para/project/slea-ssem/src/agent/config.py`

```python
AGENT_CONFIG = {
    "max_iterations": 10,
    "early_stopping_method": "force",
    "verbose": True,
    "handle_parsing_errors": True,
    "return_intermediate_steps": True
}

TOOL_CONFIG = {
    "get_user_profile": 3,              # 3 seconds
    "search_question_templates": 5,     # 5 seconds
    "get_difficulty_keywords": 2,       # 2 seconds
    "validate_question_quality": 10,    # 10 seconds
    "save_generated_question": 10,      # 10 seconds
    "score_and_explain": 15             # 15 seconds
}
```

### LLM Configuration

```python
ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
    max_tokens=1024,
    top_p=0.95,
    timeout=30
)
```

---

## Pipeline Workflows

### Mode 1: Question Generation (Tools 1-5)

```
1. Tool 1 → Get user profile
2. Tool 2 → Search templates (optional, for few-shot examples)
3. Tool 3 → Get difficulty keywords
4. LLM → Generate questions (using profile + keywords + templates)
5. Tool 4 → Validate each generated question
6. Tool 5 → Save validated questions (Tool 4 score >= 0.70)
```

### Mode 2: Auto-Scoring (Tool 6)

```
1. Tool 6 → Score user answer
   - MC/TF: Exact match → 0 or 100
   - SA: LLM evaluate (0-100) + keyword match
2. Tool 6 → Generate explanation (>= 500 chars + 3+ refs)
3. Return: Grading result with feedback
```

---

## Data Contracts & Types

### Question Types

```python
QUESTION_TYPES = {"multiple_choice", "true_false", "short_answer"}
```

### Categories

```python
SUPPORTED_CATEGORIES = {"technical", "business", "general"}
```

### Difficulty Range

```python
DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 10
```

---

## Common Error Codes & Messages

| Error | Tool | Input | Handling |
|-------|------|-------|----------|
| `ValueError: user_id must be valid UUID format` | Tool 1 | Invalid user_id | Raise error, log for audit |
| `ValueError: interests cannot be empty` | Tool 2 | Empty interests list | Raise error |
| `ValueError: difficulty must be 1-10` | Tools 2,3 | Out of range difficulty | Raise error |
| `ValueError: category must be one of {technical, business, general}` | Tools 2,3 | Invalid category | Raise error |
| `ValueError: No templates found` | Tool 2 | Valid inputs, no matches | Return `[]` (not error) |
| `ValueError: stem cannot be empty` | Tool 4,5 | Empty stem | Raise error |
| `ValueError: Correct answer not found in choices` | Tool 4 | MC validation fails | Return issues list |
| `TypeError: user_answer must be string` | Tool 6 | Wrong type | Raise error |
| `ValueError: correct_answer required for multiple_choice` | Tool 6 | MC without answer | Raise error |

---

## Summary Table

| Tool | Purpose | Input Count | Output Type | Error Handling | Timeout |
|------|---------|------------|-------------|-----------------|---------|
| Tool 1 | Get user profile | 1 | dict | Fallback | 3s |
| Tool 2 | Search templates | 3 | list[dict] | Return [] | 5s |
| Tool 3 | Get keywords | 2 | dict | Fallback defaults | 2s |
| Tool 4 | Validate quality | 4-5 | dict\|list[dict] | Partial results | 10s |
| Tool 5 | Save question | 9 | dict | Queue for retry | 10s |
| Tool 6 | Score & explain | 5-9 | dict | Default score | 15s |

---

## References

- **Agent Implementation**: `/home/bwyoon/para/project/slea-ssem/src/agent/llm_agent.py`
- **Tool Implementations**: `/home/bwyoon/para/project/slea-ssem/src/agent/tools/`
- **FastMCP Server**: `/home/bwyoon/para/project/slea-ssem/src/agent/fastmcp_server.py`
- **LangChain Docs**: <https://python.langchain.com/docs/concepts/agents>
- **REQ Documentation**: See `docs/` directory for detailed requirements
