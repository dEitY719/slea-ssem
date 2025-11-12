# SLEA-SSEM Architecture Diagrams

## System Architecture Overview

```
       ┌─────────────────────────────────┐
       │     Frontend (React/Vue)        │
       └──────────────┬──────────────────┘
          │ HTTP/REST
          ▼
    ┌──────────────────────────────────────────────────┐
    │           FastAPI Backend (src/backend/)          │
    │                                                   │
    │  ┌──────────────┬────────────┬──────────────┐   │
    │  │ /auth        │ /survey    │ /questions   │   │
    │  │ endpoints    │ endpoints  │ endpoints    │   │
    │  └──────────────┴────────────┴──────────────┘   │
    │                      ▲                            │
    │                      │ uses                       │
    │  ┌──────────────────────────────────┐            │
    │  │     Services Layer               │            │
    │  │  ├─ QuestionGenerationService   │            │
    │  │  ├─ ScoringService              │            │
    │  │  ├─ AutosaveService             │            │
    │  │  ├─ ExplainService              │            │
    │  │  ├─ AdaptiveDifficultyService   │            │
    │  │  ├─ RankingService              │            │
    │  │  └─ AuthService                 │            │
    │  └──────────────────────────────────┘            │
    │                      ▲                            │
    │                      │ ORM                        │
    │  ┌──────────────────────────────────┐            │
    │  │    SQLAlchemy ORM Models         │            │
    │  │  ├─ User                         │            │
    │  │  ├─ UserProfileSurvey           │            │
    │  │  ├─ TestSession                 │            │
    │  │  ├─ Question                    │            │
    │  │  ├─ AttemptAnswer               │            │
    │  │  ├─ TestResult                  │            │
    │  │  └─ Attempt / AttemptRound      │            │
    │  └──────────────────────────────────┘            │
    └──────────────────────────────────────────────────┘
          ▼
      ┌─────────────────────────────┐
      │   PostgreSQL Database       │
      │  (Production / Test DB)     │
      └─────────────────────────────┘
```

## Agent Architecture (LangChain ReAct)

```
    ┌─────────────────────────────────────┐
    │  LLM Agent (LangChain ReAct)        │
    │  src/agent/llm_agent.py             │
    │                                     │
    │  ├─ Mode 1: Question Generation    │
    │  └─ Mode 2: Auto-Scoring           │
    └──────────────────┬──────────────────┘
        │ orchestrates
      ┌────────────────┬┴────────────────┐
      │                │                │
      ▼                ▼                ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │Mode 1        │  │Mode 2        │  │Error Handler │
    │Pipeline      │  │Pipeline      │  │& Retry Logic │
    │              │  │              │  │              │
    │Orchestrates  │  │Orchestrates  │  │Retry:        │
    │Tools 1-5     │  │Tool 6        │  │Exponential   │
    └──────┬───────┘  └──────┬───────┘  │Backoff       │
     │                 │          │              │
     └────────┬────────┘          │Fallback:     │
        │                   │Timeout       │
        ▼                   │Response      │
    ┌──────────────────────────────────┐│              │
    │    Tool Registry                 │└──────────────┘
    │  fastmcp_server.py               │
    │                                  │
    │  ┌─ Tool 1: Get User Profile    │
    │  ├─ Tool 2: Search Templates    │
    │  ├─ Tool 3: Get Keywords        │
    │  ├─ Tool 4: Validate Question   │
    │  ├─ Tool 5: Save Question       │
    │  └─ Tool 6: Score & Explain     │
    │                                  │
    │  Each tool has:                  │
    │  ├─ LangChain @tool wrapper     │
    │  ├─ Pydantic I/O contracts      │
    │  └─ Error handling              │
    └──────────────────────────────────┘
```

## Mode 1: Question Generation Pipeline

```
Request: { survey_id, round_idx, user_id }
   │
   ▼
┌─────────────────────────────────────────────┐
│ Mode 1 Pipeline (mode1_pipeline.py)         │
└──────────────────┬──────────────────────────┘
      │
   ┌──────────────┼──────────────┐
   │              │              │
   ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Tool 1   │  │ Tool 2   │  │ Tool 3   │
│ Get User │  │ Search   │  │ Get      │
│ Profile  │  │Templates │  │Keywords  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
 │             │             │
 └─────────────┼─────────────┘
      ▼
  [Generate Question Loop]
      │
  ┌─────────┼─────────┐
  ▼                   ▼
  ┌──────────┐      ┌──────────┐
  │ Tool 4   │      │ Tool 5   │
  │Validate  │      │Save      │
  │Question  │      │Question  │
  └────┬─────┘      └────┬─────┘
    │                 │
    ├─ Pass (≥0.70)? ──┤
    │ Yes              ▼
    │            [DB Insert]
    │
    └─ Fail? ──────────┐
    Retry            │
        ▼
Response: { round_id, items[], agent_steps, failed_count }
```

## Mode 2: Parallel Answer Scoring Pipeline

```
Request: [{ session_id, user_id, question_id, user_answer }, ...]
   │
   ▼
┌─────────────────────────────────────────┐
│ Mode 2 Pipeline (mode2_pipeline.py)     │
│ Batch Size: configurable (e.g., 5)    │
└──────────────────┬──────────────────────┘
      │
      ▼
  [Batch Partitioning]
      │
    ┌──────────┴──────────┐
    ▼                     ▼
   ┌────────┐           ┌────────┐
   │Batch 1 │           │Batch 2 │
   │[...]   │           │[...]   │
   └───┬────┘           └───┬────┘
    │                    │
    ▼ (Parallel)         ▼ (Parallel)
   ┌────────────┐       ┌────────────┐
   │ Tool 6     │       │ Tool 6     │
   │ Score &    │       │ Score &    │
   │ Explain    │       │ Explain    │
   │ (5 times)  │       │ (5 times)  │
   └────┬───────┘       └────┬───────┘
  │                    │
  └──────────┬─────────┘
       ▼
  [Aggregate Results]
       │
       ▼
Response: [{ question_id, is_correct, score, explanation }, ...]
```

## Data Flow: Question Generation to Scoring

```
User submits profile survey
   │
   ▼
┌──────────────────────────────────┐
│ UserProfileSurvey (DB)           │
│ ├─ interests: ["LLM", "RAG"]     │
│ ├─ self_level: "intermediate"    │
│ └─ years_experience: 5           │
└──────────────────┬───────────────┘
      │ references
      ▼
   [POST /questions/generate]
      │
      ▼
   ┌─────────────────────────────┐
   │ QuestionGenerationService   │
   │ .generate_questions(...)    │
   └──────────────┬──────────────┘
      │ creates
      ▼
   ┌──────────────────────────────┐
   │ TestSession (DB)             │
   │ ├─ user_id                   │
   │ ├─ survey_id                 │
   │ ├─ round: 1                  │
   │ └─ status: "in_progress"     │
   └──────────────┬───────────────┘
      │ contains
      ▼
   ┌──────────────────────────────┐
   │ Question (DB) x 5            │
   │ ├─ stem: "What is..."        │
   │ ├─ choices: ["A", "B", ...]  │
   │ ├─ answer_schema             │
   │ ├─ difficulty: 5             │
   │ └─ category: "LLM"           │
   └──────────────┬───────────────┘
      │ presented to user
      ▼
    [User answers questions]
      │
    [POST /questions/autosave]
    (for each answer)
      │
      ▼
   ┌──────────────────────────────┐
   │ AttemptAnswer (DB)           │
   │ ├─ session_id                │
   │ ├─ question_id               │
   │ ├─ user_answer: "A"          │
   │ └─ response_time_ms: 5000    │
   └──────────────┬───────────────┘
      │ all answers collected
      ▼
    [POST /questions/answer/score]
    (for each question)
      │
      ▼
   ┌──────────────────────────────┐
   │ ScoringService               │
   │ .score_answer(...)           │
   │                              │
   │ ├─ Multiple Choice:          │
   │ │  exact match               │
   │ ├─ Short Answer:             │
   │ │  keyword matching          │
   │ └─ Score: 0-100              │
   └──────────────┬───────────────┘
      │ updates
      ▼
   ┌──────────────────────────────┐
   │ AttemptAnswer (DB) - Updated │
   │ ├─ is_correct: true/false    │
   │ └─ score: 85                 │
   └──────────────┬───────────────┘
      │ all answers scored
      ▼
    [POST /questions/score]
      │
      ▼
   ┌──────────────────────────────┐
   │ TestResult (DB)              │
   │ ├─ session_id                │
   │ ├─ round: 1                  │
   │ ├─ score: 75                 │
   │ ├─ correct_count: 4          │
   │ └─ wrong_categories: [...]   │
   └──────────────────────────────┘
```

## Testing Architecture

```
┌──────────────────────────────────────────────────────────┐
│  pytest (tests/)                                         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ conftest.py                                      │   │
│  │ - db_engine (PostgreSQL test)                   │   │
│  │ - db_session (fresh per test)                   │   │
│  │ - authenticated_user                            │   │
│  │ - user_profile_survey_fixture                   │   │
│  │ - test_session_round1_fixture                   │   │
│  │ - test_result_* (low/med/high score)           │   │
│  │ - Factory fixtures (create_*)                   │   │
│  │ - client (FastAPI TestClient)                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ tests/agent/                                     │   │
│  │ ├─ test_llm_agent.py                            │   │
│  │ ├─ test_fastmcp_server.py (Tools 1-6)          │   │
│  │ ├─ test_mode1_pipeline.py                       │   │
│  │ ├─ test_mode2_pipeline.py                       │   │
│  │ ├─ test_mode2_pipeline_parallel.py              │   │
│  │ └─ test_error_handling.py                       │   │
│  │                                                   │   │
│  │ Test Patterns:                                   │   │
│  │ ├─ Mocked LLM (predictable output)              │   │
│  │ ├─ Mocked DB (in-memory or test DB)             │   │
│  │ ├─ Happy path + error cases                     │   │
│  │ └─ Integration tests (full pipeline)            │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ tests/backend/                                   │   │
│  │ ├─ test_question_endpoint.py                    │   │
│  │ ├─ test_question_gen_service.py                 │   │
│  │ ├─ test_scoring_service.py                      │   │
│  │ ├─ test_ranking_service.py                      │   │
│  │ ├─ test_autosave_endpoints.py                   │   │
│  │ └─ ... (20+ test files)                         │   │
│  │                                                   │   │
│  │ Test Patterns:                                   │   │
│  │ ├─ Fixture-based DB setup                       │   │
│  │ ├─ HTTP endpoint testing                        │   │
│  │ ├─ Service logic testing                        │   │
│  │ └─ Dependency injection override                │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## File Dependency Graph (Key Files)

```
        FastAPI App (main.py)
          │
      ┌───────────────┼───────────────┐
      │               │               │
     auth.py        questions.py    survey.py
   router          router          router
      │               │
      │       ┌───────┼───────┐
      │       │       │       │
      │       ▼       ▼       ▼
      │  QuestionGen ScoringServ AutosaveServ
      │  Service     (scoring)   (autosave)
      │              │
      │     ┌────────┤────────┐
      │     │        │        │
      │     ▼        ▼        ▼
     AuthServ   models/  database.py
     (auth)    (ORM)    (SessionLocal)
       │
     ┌──────────┼──────────┐
     │          │          │
     ▼          ▼          ▼
  User    TestSession  Question
  model      model      model
         │
         ▼
       PostgreSQL DB
```

## Deployment Architecture (High-level)

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                     │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Python 3.11+                                    │ │
│  │  ├─ FastAPI (main.py)                           │ │
│  │  │  └─ uvicorn (ASGI server)                    │ │
│  │  │     Listens on 0.0.0.0:8000                  │ │
│  │  │                                               │ │
│  │  ├─ LangChain Agent (src/agent/)                │ │
│  │  │  └─ Available via service imports             │ │
│  │  │                                               │ │
│  │  ├─ SQLAlchemy ORM (src/backend/models/)        │ │
│  │  │  └─ Connects to PostgreSQL                    │ │
│  │  │                                               │ │
│  │  └─ Dependencies:                                │ │
│  │     ├─ langchain-core                           │ │
│  │     ├─ langgraph                                │ │
│  │     ├─ fastapi                                  │ │
│  │     ├─ sqlalchemy                               │ │
│  │     ├─ pydantic                                 │ │
│  │     └─ openai (or other LLM)                    │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Environment Variables                            │ │
│  │  ├─ DATABASE_URL (PostgreSQL)                    │ │
│  │  ├─ OPENAI_API_KEY (LLM)                         │ │
│  │  ├─ TEST_DATABASE_URL (test PostgreSQL)         │ │
│  │  └─ Other configs                                │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
  ▲                               │
  │                               │
   HTTP Requests                  PostgreSQL
   (from frontend)                (Data persistence)
```
