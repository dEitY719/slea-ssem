# SLEA-SSEM Codebase Exploration Report

**Project**: SLEA-SSEM (S.LSI Education AI System)  
**Generated**: 2025-11-07  
**Exploration Scope**: Project structure, agents implementation, database models, API endpoints, Explain-Agent placement

---

## 1. DIRECTORY STRUCTURE OVERVIEW

```
slea-ssem/
├── src/
│   ├── backend/              # Backend FastAPI application
│   │   ├── api/              # REST API endpoints (routers)
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── profile.py    # User profile endpoints
│   │   │   ├── survey.py     # Self-assessment survey endpoints
│   │   │   └── questions.py  # Question generation & scoring endpoints
│   │   ├── models/           # SQLAlchemy ORM models
│   │   │   ├── user.py       # Base model + User
│   │   │   ├── question.py   # Question model
│   │   │   ├── test_session.py    # TestSession model
│   │   │   ├── attempt_answer.py  # AttemptAnswer model
│   │   │   ├── test_result.py     # TestResult model
│   │   │   └── user_profile.py    # UserProfile & UserProfileSurvey models
│   │   ├── services/         # Business logic services
│   │   │   ├── auth_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── survey_service.py
│   │   │   ├── question_gen_service.py   # Item-Gen-Agent placeholder
│   │   │   ├── scoring_service.py        # Scoring-Agent (✅ IMPLEMENTED)
│   │   │   ├── adaptive_difficulty_service.py
│   │   │   └── autosave_service.py
│   │   ├── validators/       # Input validation
│   │   │   └── nickname_validator.py
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database session
│   │   └── __init__.py
│   ├── agent/                # Agent implementations (MINIMAL)
│   │   └── __init__.py       # Currently empty - EXPANSION AREA
│   └── frontend/             # Frontend utilities (TBD)
├── tests/
│   └── backend/              # Backend test suite
│       ├── test_*_service.py     # Service tests
│       ├── test_*_endpoint.py    # API endpoint tests
│       └── conftest.py           # Pytest fixtures (important!)
├── docs/
│   ├── feature_requirement_mvp1.md  # Complete requirements
│   ├── DEV-PROGRESS.md              # Development tracking
│   └── progress/                    # Individual REQ progress files
├── alembic/                  # Database migrations
├── tools/
│   ├── dev.sh               # Development commands
│   └── commit.sh            # Interactive commit tool
├── CLAUDE.md                # Claude Code guidelines
├── AGENTS.md                # Multi-AI configuration
├── GEMINI.md                # Gemini configuration
├── pyproject.toml           # Python dependencies
└── tox.ini                  # Test configuration
```

---

## 2. EXISTING AGENTS IMPLEMENTATION

### Current Status: 2 of 3 Agents Implemented

#### 2.1 Item-Gen-Agent (Question Generation)

**Status**: ✅ IMPLEMENTED (REQ-B-B2-Gen, REQ-B-B2-Adapt)

**Location**: `/home/bwyoon/para/project/slea-ssem/src/backend/services/question_gen_service.py`

**Purpose**: Generate test questions dynamically based on user profile and interests

**Key Methods**:

- `generate_questions(user_id, survey_id, round_num)` - Generate 5 questions for Round 1
- `generate_questions_adaptive(user_id, session_id, round_num)` - Generate Round 2+ with difficulty adjustment
- Supports 3 question types: multiple_choice, true_false, short_answer

**LLM Integration**: Uses OpenAI/Claude to generate questions with:

- Dynamic difficulty (1-10 scale)
- User interest-based categorization
- Adaptive difficulty based on previous round scores (weak categories get prioritized)

**API Endpoints**:

- `POST /questions/generate` - Generate Round 1 questions
- `POST /questions/generate-adaptive` - Generate adaptive Round 2+ questions

---

#### 2.2 Scoring-Agent (Answer Evaluation)

**Status**: ✅ IMPLEMENTED (REQ-B-B3-Score)

**Location**: `/home/bwyoon/para/project/slea-ssem/src/backend/services/scoring_service.py`

**Purpose**: Score user answers in real-time with type-specific logic

**Key Methods**:

```python
score_answer(session_id, question_id) -> dict
    - Scores submitted answer within 1 second
    - Applies time penalty if session exceeds 20-minute limit
    - Returns: is_correct, score, feedback

_score_multiple_choice(user_answer, answer_schema) -> (bool, float)
    - Exact match: selected_key == correct_key
    - Returns: (is_correct: bool, score: 0 or 1)

_score_true_false(user_answer, answer_schema) -> (bool, float)
    - Normalizes boolean/string inputs
    - Exact match comparison
    - Returns: (is_correct: bool, score: 0 or 1)

_score_short_answer(user_answer, answer_schema) -> (bool, float)
    - Keyword-based matching (case-insensitive)
    - Partial credit: (matched_keywords / total_keywords) * 100
    - Returns: (is_correct: bool, score: 0-100)

_apply_time_penalty(base_score, test_session) -> (bool, float)
    - Penalty: (excess_ms / time_limit_ms) * base_score
    - Final score: max(0, score - penalty)

calculate_round_score(session_id, round_num) -> dict
    - Aggregates all attempt answers for a round
    - Calculates: score%, correct_count, wrong_categories
```

**API Endpoint**:

- `POST /questions/score` - Score a single answer
- Integrated with AutosaveService for real-time answer persistence

**Performance**: Completes within 1 second per question

---

#### 2.3 Explain-Agent (Answer Explanations)

**Status**: ❌ NOT YET IMPLEMENTED (REQ-B-B3-Explain)

**Requirement Spec** (from feature_requirement_mvp1.md):

```
REQ-B-B3-Explain-1: 
- Explain-Agent must generate per-question explanation:
  * 500+ character explanation (정답/오답 해설)
  * 3+ reference links
  * Performance: Complete within 2 seconds
```

**Expected Architecture** (based on existing patterns):

```
src/backend/services/explain_service.py
├── class ExplainService:
│   ├── generate_explanation(question_id, user_answer, is_correct) -> dict
│   │   - Retrieves question details from DB
│   │   - Calls LLM (Claude/OpenAI) with specialized prompt
│   │   - Parses response (explanation + reference links)
│   │   - Stores in database (new table: answer_explanations)
│   │   - Returns: explanation text, links, language
│   │
│   ├── get_explanation(question_id, answer_id) -> dict
│   │   - Retrieves cached explanation or generates if missing
│   │
│   └── _format_explanation(raw_llm_output) -> (explanation: str, links: list[str])
│       - Parses LLM response format
│       - Extracts links (URLs, DOI, etc.)
│       - Validates minimum length requirement
```

**Database Model** (to be created):

```python
class AnswerExplanation(Base):
    __tablename__ = "answer_explanations"
    
    id: str = PK
    question_id: str = FK(questions.id)
    answer_id: str = FK(attempt_answers.id, nullable=True)
    explanation: str  # 500+ chars
    reference_links: list  # 3+ URLs
    is_correct_explanation: bool  # Explanation for correct/incorrect answer
    language: str = "ko"  # Korean by default
    generated_by: str  # LLM model identifier
    created_at: datetime
```

**API Endpoint** (to be created):

```python
@router.post("/explanations/{question_id}")
def generate_explanation(
    question_id: str,
    answer_id: str = None,  # Optional: specific attempt answer
    db: Session = Depends(get_db)
) -> ExplanationResponse:
    """
    Generate explanation for a question.
    
    Returns:
    {
        "question_id": "uuid",
        "answer_id": "uuid",
        "is_correct": true/false,
        "explanation": "...",
        "reference_links": ["url1", "url2", "url3"],
        "generated_at": "ISO timestamp"
    }
    """
```

---

## 3. DATABASE MODELS (Test-Related)

### Core Models

**3.1 TestSession**

```python
class TestSession(Base):
    id: str (UUID, PK)
    user_id: int (FK → users)
    survey_id: str (FK → user_profile_surveys)
    round: int (1 or 2)
    status: str (in_progress, completed, paused)
    time_limit_ms: int (default: 1200000 = 20 mins)
    started_at: datetime
    paused_at: datetime
    created_at: datetime
    updated_at: datetime
```

**Purpose**: Track user test attempts and rounds

---

**3.2 Question**

```python
class Question(Base):
    id: str (UUID, PK)
    session_id: str (FK → test_sessions)
    item_type: str (multiple_choice, true_false, short_answer)
    stem: str (Question text, max 2000 chars)
    choices: list[str] (JSON, for MC/TF)
    answer_schema: dict (Correct answer + explanation)
    difficulty: int (1-10)
    category: str (AI, LLM, RAG, Semiconductor, etc.)
    round: int (1 or 2)
    created_at: datetime
```

**Purpose**: Store generated questions with metadata

---

**3.3 AttemptAnswer**

```python
class AttemptAnswer(Base):
    id: str (UUID, PK)
    session_id: str (FK → test_sessions)
    question_id: str (FK → questions)
    user_answer: dict | str (JSON user response)
    is_correct: bool
    score: float (0-100)
    response_time_ms: int (Time to answer)
    saved_at: datetime (Autosave timestamp)
    created_at: datetime
```

**Purpose**: Store user responses with scoring metadata

---

**3.4 TestResult**

```python
class TestResult(Base):
    id: str (UUID, PK)
    session_id: str (FK → test_sessions)
    round: int (1, 2, or 3)
    score: float (0-100 percentage)
    total_points: int (Points earned)
    correct_count: int
    total_count: int
    wrong_categories: dict ({"LLM": 1, "RAG": 2})
    created_at: datetime
```

**Purpose**: Store aggregated round results

---

### Missing Model for Explain-Agent

**AnswerExplanation** (needs to be created):

```python
class AnswerExplanation(Base):
    id: str (UUID, PK)
    question_id: str (FK → questions)
    answer_id: str (FK → attempt_answers, nullable)
    explanation: str (500+ chars)
    reference_links: list[str] (3+ URLs)
    is_correct_explanation: bool
    language: str ("ko" default)
    generated_by: str ("gpt-4", "claude-3", etc.)
    created_at: datetime
```

---

## 4. API ENDPOINT STRUCTURE

### Questions Endpoints (src/backend/api/questions.py)

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| `POST` | `/questions/generate` | Generate Round 1 questions | ✅ Done |
| `POST` | `/questions/generate-adaptive` | Generate Round 2+ questions | ✅ Done |
| `POST` | `/questions/autosave` | Save answer in real-time | ✅ Done |
| `GET` | `/questions/resume` | Resume paused session | ✅ Done |
| `POST` | `/questions/score` | Score single answer | ✅ Done |
| `POST` | `/questions/score?session_id=...` | Calculate round score | ✅ Done |
| `PUT` | `/questions/session/{session_id}/status` | Pause/resume session | ✅ Done |
| `GET` | `/questions/session/{session_id}/time-status` | Check time limit | ✅ Done |
| `POST` | `/questions/explanations` | **Generate explanation** | ❌ TODO |

### Related Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /auth/login` | Samsung AD authentication |
| `GET /profile` | Get user profile |
| `POST /profile/edit` | Edit profile (nickname, etc.) |
| `GET /survey/schema` | Get survey form schema |
| `POST /survey/submit` | Submit self-assessment survey |

---

## 5. SERVICE LAYER ARCHITECTURE

```
src/backend/services/
├── auth_service.py
│   ├── verify_azure_token()
│   └── create_session()
│
├── profile_service.py
│   ├── get_profile()
│   ├── create_profile()
│   └── edit_profile()
│
├── survey_service.py
│   ├── get_survey_schema()
│   └── save_survey()
│
├── question_gen_service.py          # Item-Gen-Agent
│   ├── generate_questions()
│   └── generate_questions_adaptive()
│
├── scoring_service.py               # Scoring-Agent
│   ├── score_answer()
│   ├── calculate_round_score()
│   └── _get_wrong_categories()
│
├── adaptive_difficulty_service.py
│   ├── calculate_difficulty_tier()
│   └── get_weak_categories()
│
├── autosave_service.py
│   ├── save_answer()
│   ├── get_session_state()
│   ├── pause_session()
│   └── resume_session()
│
└── explain_service.py               # Explain-Agent (TODO)
    ├── generate_explanation()
    ├── get_explanation()
    └── _format_explanation()
```

---

## 6. TEST STRUCTURE (pytest)

**Location**: `/home/bwyoon/para/project/slea-ssem/tests/backend/`

```
tests/backend/
├── conftest.py                          # Shared fixtures
│   ├── db_session                       # SQLAlchemy session
│   ├── test_user_fixture                # User record
│   ├── test_session_round1_fixture      # TestSession (Round 1)
│   ├── test_session_round2_fixture      # TestSession (Round 2)
│   ├── questions_for_session            # Question list
│   └── attempt_answers_for_session      # AttemptAnswer list
│
├── test_scoring_service.py              # 36 tests (100% pass)
│   ├── TestScoreCalculation
│   │   ├── test_calculate_round_score_all_correct
│   │   ├── test_calculate_round_score_partial_correct
│   │   └── test_calculate_round_score_all_wrong
│   ├── TestWeakCategoryIdentification
│   ├── TestMultipleChoiceScoring
│   ├── TestTrueFalseScoring
│   ├── TestShortAnswerScoring
│   └── TestTimePenalty
│
├── test_question_gen_service.py         # 12 tests (100% pass)
├── test_scoring_endpoints.py            # API endpoint tests
├── test_adaptive_difficulty_service.py  # 41 tests (100% pass)
├── test_autosave_service.py             # 33 tests (100% pass)
└── ... (other service/endpoint tests)
```

**Test Patterns**:

```python
def test_example(db_session: Session, test_session_round1_fixture: TestSession):
    """Test description with REQ ID."""
    # Arrange
    service = SomeService(db_session)
    
    # Act
    result = service.method()
    
    # Assert
    assert result["key"] == expected_value
```

---

## 7. RECOMMENDATIONS FOR EXPLAIN-AGENT PLACEMENT

### Option A: Recommended - Create Dedicated ExplainService (MVP Compliant)

**Location**: `/home/bwyoon/para/project/slea-ssem/src/backend/services/explain_service.py`

**Advantages**:

- Follows SOLID principles (Single Responsibility)
- Mirrors existing ScoringService pattern
- Easy to test independently
- Decouples explanation generation from scoring
- Can be called from multiple endpoints/services

**Structure**:

```python
# src/backend/services/explain_service.py

class ExplainService:
    def __init__(self, session: Session, llm_client):
        self.session = session
        self.llm_client = llm_client
    
    def generate_explanation(
        self,
        question_id: str,
        user_answer: dict | str,
        is_correct: bool,
        attempt_id: str = None
    ) -> dict:
        """Generate explanation for answer."""
        # Fetch question details
        # Call LLM with specialized prompt
        # Parse response (explanation + links)
        # Store in DB
        # Return result
    
    def get_explanation(self, question_id: str, attempt_id: str = None) -> dict:
        """Retrieve or generate explanation."""
        # Check cache first
        # Generate if missing
        # Return stored explanation
```

**API Endpoint** (new):

```python
# src/backend/api/questions.py

@router.post(
    "/explanations",
    status_code=201,
    summary="Generate Answer Explanation",
    description="Generate explanation for answered question"
)
def generate_explanation(
    request: ExplanationRequest,
    db: Session = Depends(get_db)
) -> ExplanationResponse:
    """Generate explanation for a submitted answer."""
    explain_service = ExplainService(db, llm_client)
    return explain_service.generate_explanation(...)
```

**Database Model** (new):

```python
# src/backend/models/answer_explanation.py

class AnswerExplanation(Base):
    __tablename__ = "answer_explanations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, ...)
    question_id: Mapped[str] = mapped_column(String(36), FK(...), ...)
    attempt_answer_id: Mapped[str] = mapped_column(String(36), FK(...), nullable=True)
    explanation: Mapped[str] = mapped_column(String(2000), nullable=False)
    reference_links: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_correct_explanation: Mapped[bool]  # Explanation for correct/incorrect
    language: Mapped[str] = mapped_column(String(10), default="ko")
    generated_by: Mapped[str] = mapped_column(String(50))  # LLM model
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, ...)
```

**Test File** (new):

```python
# tests/backend/test_explain_service.py

class TestExplanationGeneration:
    """REQ-B-B3-Explain-1: Generate explanations with references."""
    
    def test_generate_explanation_correct_answer(self, db_session):
        """Generate explanation for correct answer."""
        # Setup
        # Generate explanation
        # Assert: length >= 500, links >= 3
    
    def test_generate_explanation_incorrect_answer(self, db_session):
        """Generate explanation for incorrect answer."""
        # Similar test for wrong answers
    
    def test_explanation_performance_under_2s(self, db_session):
        """Explanation generation completes within 2 seconds."""
        # Measure generation time
        # Assert: elapsed < 2000ms
```

---

### Option B: Integrate with ScoringService

**Alternative approach**: Add explanation generation to ScoringService after scoring

**Cons**:

- Violates Single Responsibility Principle
- Makes ScoringService harder to test
- Increases coupling
- Less flexible for caching/optimization

**Not recommended for MVP**.

---

### Option C: Create Agent Module in src/agent/

**Alternative approach**: Create agent structure following multi-AI pattern

**Location**: `/home/bwyoon/para/project/slea-ssem/src/agent/explain_agent.py`

**Current Status**: `src/agent/__init__.py` is almost empty

**Consideration**: If future MVP versions adopt multi-agent orchestration (Agent Specialist badges, RAG-based generation), this structure would be beneficial. For MVP 1.0, ExplainService in backend/services/ is more pragmatic.

---

## 8. DEVELOPMENT PROGRESS STATUS (as of 2025-11-07)

### Completed (Phase 4 - Done)

- REQ-B-A1: Samsung AD authentication ✅
- REQ-B-A2: Nickname registration ✅
- REQ-B-A2-Edit: Profile editing ✅
- REQ-B-B1: Survey data collection ✅
- REQ-B-B2-Gen: Round 1 question generation ✅
- REQ-B-B2-Adapt: Adaptive difficulty (Round 2) ✅
- REQ-B-B2-Plus: Real-time autosave ✅
- REQ-B-B3-Score: Answer scoring ✅

### Pending (Phase 0 - Backlog)

- REQ-B-B3-Explain: **Answer explanations** ← EXPLAIN-AGENT
- REQ-B-B4: Grade calculation & ranking
- REQ-B-B4-Plus: Badge assignment
- REQ-B-B5: Test history & comparison
- REQ-B-B6: Content filtering

---

## 9. KEY FILES FOR IMPLEMENTATION

### Critical Files to Reference

| File | Purpose | Key Classes |
|------|---------|-------------|
| `/src/backend/services/scoring_service.py` | Scoring pattern | `ScoringService` |
| `/src/backend/api/questions.py` | Endpoint pattern | Request/Response models |
| `/src/backend/models/test_result.py` | Model pattern | Base + imports |
| `/tests/backend/test_scoring_service.py` | Test pattern | Test class structure |
| `/tests/conftest.py` | Fixtures | db_session, test fixtures |
| `docs/progress/REQ-B-B3-Score.md` | Progress format | Documentation template |

### LLM Integration Points

**Existing**:

- QuestionGenerationService uses OpenAI/Claude for question generation
- Prompt engineering already established

**For Explain-Agent**:

- Create `explain_prompt.py` with specialized prompt templates
- Use same LLM client from QuestionGenerationService
- Support both correct & incorrect answer explanations

---

## 10. IMPLEMENTATION CHECKLIST FOR EXPLAIN-AGENT

### Phase 1: Specification (Approval Required)

- [ ] Define exact LLM prompt for explanation generation
- [ ] Specify explanation format (HTML, markdown, plain text)
- [ ] Define reference link sources (Korean resources, docs, papers)
- [ ] Confirm 500-char minimum and 3+ links requirement
- [ ] Review question coverage (MC, TF, SA all need explanations)
- [ ] Approve performance SLA (< 2 seconds)

### Phase 2: Tests (TDD)

- [ ] Create `tests/backend/test_explain_service.py`
- [ ] Design 4-5 test cases:
  - [ ] Happy path: Generate explanation for correct MC answer
  - [ ] Happy path: Generate explanation for incorrect answer
  - [ ] Validation: Explanation length >= 500 chars
  - [ ] Validation: Reference links >= 3
  - [ ] Performance: Generation < 2000ms
  - [ ] Edge case: SA answer with special characters
  - [ ] Edge case: Question with technical terms

### Phase 3: Implementation

- [ ] Create `src/backend/services/explain_service.py`
- [ ] Create `src/backend/models/answer_explanation.py`
- [ ] Add Pydantic models in `src/backend/api/questions.py`
- [ ] Add endpoint `POST /questions/explanations`
- [ ] Create Alembic migration for `answer_explanations` table
- [ ] Integrate LLM client (Claude/OpenAI)
- [ ] Run tests: `pytest tests/backend/test_explain_service.py -v`
- [ ] Run style checks: `tox -e style`

### Phase 4: Documentation & Commit

- [ ] Create `docs/progress/REQ-B-B3-Explain.md`
- [ ] Update `docs/DEV-PROGRESS.md` (change Phase 0→4, Status→Done)
- [ ] Commit with message: `feat: Implement REQ-B-B3-Explain (Explain-Agent)`

---

## 11. SUMMARY: EXPLAIN-AGENT INTEGRATION POINTS

**Architecture**:

```
User Answer → ScoringService → ExplainService → LLM (Claude/OpenAI)
                   ↓                  ↓              ↓
            AttemptAnswer          Answer         Explanation
            (scored)            Explanation        (stored)
                                  (new table)
                ↓                      ↓
        TestResult (cached)    AnswerExplanation
```

**Data Flow**:

1. User submits answer → AutosaveService stores in AttemptAnswer
2. ScoringService scores the answer (1 sec performance)
3. Frontend/Backend triggers ExplainService.generate_explanation()
4. ExplainService queries Question + AttemptAnswer from DB
5. Calls LLM (Claude/OpenAI) with question context + answer
6. Parses LLM response (explanation text + reference links)
7. Validates: length >= 500, links >= 3
8. Stores in AnswerExplanation table
9. Returns to Frontend (or cached on subsequent requests)

**Minimal Requirements**:

- AnswerExplanation model + migration
- ExplainService class with generate_explanation() method
- One API endpoint POST /questions/explanations
- 4-5 tests in test_explain_service.py
- LLM integration (reuse existing OpenAI/Claude client)

---

## CONCLUSION

The codebase is well-structured with clear patterns for implementing the Explain-Agent:

1. **Agents pattern established**: Item-Gen-Agent and Scoring-Agent already implemented
2. **Service architecture**: ExplainService should follow same pattern as ScoringService
3. **Test infrastructure**: pytest with fixtures; conftest.py shared setup
4. **API patterns**: RESTful endpoints with Pydantic models for request/response
5. **Database models**: SQLAlchemy with UUID PKs and proper relationships
6. **LLM integration**: OpenAI/Claude client already available from QuestionGenerationService

**Recommended implementation location**:

- Service: `/src/backend/services/explain_service.py`
- Model: `/src/backend/models/answer_explanation.py`
- API: Add endpoint to `/src/backend/api/questions.py`
- Tests: `/tests/backend/test_explain_service.py`

**Estimated effort**: 1-2 days (2-3 dev hours for implementation + tests + docs)
