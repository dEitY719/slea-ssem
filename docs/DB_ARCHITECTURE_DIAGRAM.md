# SLEA-SSEM: Database Architecture Visual Guide

## 1. High-Level Data Flow Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                        Frontend (User Interaction)                  │
└────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend                          │
├─────────────────┬──────────────────┬──────────────────────────────┤
│  API Routes     │    Services      │  Agent Integration           │
│  ─────────────  │    ──────────    │  ──────────────────          │
│  /generate      │  QuestionGenSvc  │  ItemGenAgent (Google)       │
│  /autosave      │  AutosaveSvc     │  Tool 1-6 Pipeline          │
│  /answer/score  │  ScoringService  │  ReAct Format Output        │
│  /score         │  AdaptiveDiffSvc │                             │
│  /generate-...  │  RankingService  │                             │
│  /resume        │  HistoryService  │                             │
└────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ USERS & PROFILES                                             │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │ users ─────→ user_profile_surveys (이력, NEW만)             │ │
│  │              (자체평가, 관심분야, 경년)                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ TEST SESSIONS & QUESTIONS (진행 중)                         │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │ test_sessions ─────→ questions (round별 5문제)              │ │
│  │ (라운드별 독립)     (Agent 생성, difficulty/category)       │ │
│  │                     (answer_schema: MC/TF/SA별)             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ ANSWERS & SCORING (실시간)                                  │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │ questions ────→ attempt_answers (user_answer → score)       │ │
│  │                 (autosave → scoring 파이프라인)            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ RESULTS & HISTORY (완료 후)                                 │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │ test_sessions → test_results (round점수, 약점분석)          │ │
│  │                                 ↓                            │ │
│  │ attempts ─→ attempt_rounds ─→ attempt_answers (최종 기록)   │ │
│  │ (final_grade, rank, percentile)  (라운드별 상세)           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

## 2. Test Session Lifecycle (Round 1 → 2 Flow)

```
┌─────────────────────────────────────────────────────────────────────┐
│ ROUND 1 TEST SESSION (session_id = s1, round = 1)                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. test_sessions 생성                                              │
│     ├─ id: s1                                                       │
│     ├─ user_id: 1                                                   │
│     ├─ survey_id: survey-123 (사용자 설문)                          │
│     ├─ round: 1                                                     │
│     ├─ status: "in_progress"                                        │
│     └─ time_limit_ms: 1200000 (20분)                               │
│                                                                      │
│  2. questions 생성 (Agent via ItemGenAgent)                         │
│     ├─ Q1: {id: q1, session_id: s1, stem: "LLM이란?", ...}        │
│     ├─ Q2: {id: q2, session_id: s1, ...}                           │
│     ├─ Q3: {id: q3, session_id: s1, ...}                           │
│     ├─ Q4: {id: q4, session_id: s1, ...}                           │
│     └─ Q5: {id: q5, session_id: s1, ...}                           │
│                                                                      │
│  3. attempt_answers 생성 (사용자가 문제 풀 때마다)                 │
│     ├─ Q1: {session_id: s1, question_id: q1, user_answer: {...},   │
│     │       is_correct: false, score: 0.0, saved_at: now()}        │
│     ├─ Q2: {...}                                                    │
│     ├─ Q3: {...}                                                    │
│     ├─ Q4: {...}                                                    │
│     └─ Q5: {...}                                                    │
│                                                                      │
│  4. scoring (선택사항: 즉시 채점)                                   │
│     └─ attempt_answers 업데이트:                                    │
│        is_correct: true/false, score: 0.0-100.0                    │
│                                                                      │
│  5. test_results 생성 (라운드 완료 시)                              │
│     ├─ session_id: s1                                               │
│     ├─ round: 1                                                     │
│     ├─ score: 80.0 (4/5 * 100)                                     │
│     ├─ correct_count: 4                                             │
│     ├─ total_count: 5                                               │
│     └─ wrong_categories: {"LLM": 1}  ← 약점 분석                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                        [라운드 1 완료, 2로 진행]
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ ROUND 2 TEST SESSION (session_id = s2, round = 2) ← 다른 session_id │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 적응형 난이도 계산                                              │
│     └─ AdaptiveDifficultyService.get_adaptive_generation_params()  │
│        ├─ prev_score: 80.0 → adjusted_difficulty: 6.5 ↑           │
│        └─ wrong_categories: {"LLM": 1} → priority_ratio: {         │
│           "LLM": 2, "RAG": 1, Others: 2}                           │
│                                                                      │
│  2. test_sessions 생성 (Round 2)                                    │
│     ├─ id: s2 (다른 session_id!)                                    │
│     ├─ user_id: 1                                                   │
│     ├─ survey_id: survey-123 (같은 설문)                            │
│     ├─ round: 2                                                     │
│     └─ status: "in_progress"                                        │
│                                                                      │
│  3. questions 생성 (적응형, Agent 호출 시 prev_answers 포함)       │
│     ├─ Q1: {id: q6, session_id: s2, category: "LLM", ...}         │
│     ├─ Q2: {id: q7, session_id: s2, category: "LLM", ...}  ←2     │
│     ├─ Q3: {id: q8, session_id: s2, category: "RAG", ...}         │
│     ├─ Q4: {id: q9, session_id: s2, category: "Others", ...}      │
│     └─ Q5: {id: q10, session_id: s2, category: "Others", ...}     │
│        (우선 카테고리 LLM에 2문제, RAG에 1문제)                    │
│                                                                      │
│  4-5. [Round 1과 동일: attempt_answers, scoring, test_results]   │
│                                                                      │
│  6. test_results 생성 (Round 2 완료 시)                             │
│     ├─ session_id: s2                                               │
│     ├─ round: 2                                                     │
│     ├─ score: 85.0                                                  │
│     └─ wrong_categories: {"RAG": 2}                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                        [모든 라운드 완료]
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ FINAL ATTEMPT RECORD (영구 저장)                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. attempts 생성                                                    │
│     ├─ id: attempt-1                                                │
│     ├─ user_id: 1                                                   │
│     ├─ survey_id: survey-123                                        │
│     ├─ started_at: 2025-01-15 10:00:00                              │
│     ├─ finished_at: 2025-01-15 10:40:00                             │
│     ├─ final_grade: "Intermediate" (80점/85점 평균 = 82.5)        │
│     ├─ final_score: 82.5                                            │
│     ├─ percentile: 65                                               │
│     ├─ rank: 35                                                     │
│     ├─ total_candidates: 100                                        │
│     └─ status: "completed"                                          │
│                                                                      │
│  2. attempt_rounds 생성                                              │
│     ├─ {attempt_id: attempt-1, round_idx: 1, score: 80.0, ...}    │
│     └─ {attempt_id: attempt-1, round_idx: 2, score: 85.0, ...}    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. Answer Schema Structure by Question Type

```
┌─────────────────────────────────────────────────────────────────────┐
│ MULTIPLE CHOICE & TRUE/FALSE                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Question in DB:                                                     │
│  {                                                                   │
│    "id": "q1",                                                       │
│    "stem": "LLM은 무엇인가?",                                       │
│    "item_type": "multiple_choice",                                  │
│    "choices": ["A: 작은 모델", "B: 대규모 신경망", ...],           │
│    "answer_schema": {                                               │
│      "correct_key": "B",                                             │
│      "explanation": "LLM은 수십억 개의 파라미터를..."               │
│    }                                                                 │
│  }                                                                   │
│                                                                      │
│  User Answer:                                                        │
│  {                                                                   │
│    "selected_key": "B"  ← ScoringService가 correct_key와 비교      │
│  }                                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ SHORT ANSWER                                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Question in DB:                                                     │
│  {                                                                   │
│    "id": "q3",                                                       │
│    "stem": "LLM 학습의 주요 기법은?",                               │
│    "item_type": "short_answer",                                     │
│    "choices": null,                                                  │
│    "answer_schema": {                                               │
│      "keywords": ["토큰 예측", "강화학습", "자기감독"],            │
│      "explanation": "LLM은 주로 다음 토큰 예측으로..."             │
│    }                                                                 │
│  }                                                                   │
│                                                                      │
│  User Answer:                                                        │
│  {                                                                   │
│    "text": "토큰 예측과 강화학습을 사용합니다"                    │
│    ↓ ScoringService가 keywords와 매칭                              │
│    ← score: 0.0-100.0 (일치도 기반)                                │
│  }                                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 4. API Call Sequence Diagram

```
Frontend                    Backend API               Database
   │                            │                         │
   │─────POST /generate────────>│                         │
   │  {survey_id, round: 1}     │─create_agent()─┐       │
   │                            │                 │       │
   │                            │         <Gemini>│       │
   │                            │  (Agent returns │       │
   │                            │   5 questions)  │       │
   │                            │<────────────────┘       │
   │                            │─save Questions─────────>│
   │<─[session_id, 5 Qs]────────│                         │
   │                            │<────────────────────────│
   │                            │                         │
   │                (User answers Q1-Q5)                   │
   │                            │                         │
   │─POST /autosave Q1─────────>│─save AttemptAnswer────>│
   │  {session_id, q_id, ans}   │                         │
   │<─[saved_at]────────────────│<────────────────────────│
   │                            │                         │
   │─POST /answer/score Q1─────>│─score_answer()────────>│
   │  {session_id, q_id}        │─update AttemptAnswer───>│
   │<─[is_correct, score]───────│<────────────────────────│
   │                            │                         │
   │  [Repeat for Q2-Q5]        │                         │
   │                            │                         │
   │─POST /score Q1────────────>│─save_round_result()──>│
   │  (All Q answered)          │ [aggregate scores]     │
   │                            │─save TestResult───────>│
   │<─[round, score, wrong_cats]│<────────────────────────│
   │                            │                         │
   │─POST /generate-adaptive───>│─get adaptive params──>│
   │  {previous_session_id, r:2}│─create_agent()─┐      │
   │                            │                │      │
   │                            │        <Gemini>│      │
   │                            │ (prev_answers  │      │
   │                            │  included!)    │      │
   │                            │<────────────────┘      │
   │                            │─save new Questions───>│
   │<─[session_id, 5 Qs]────────│<────────────────────────│
   │                            │                         │
   │  [Repeat for Round 2]      │                         │
   │                            │                         │
   │─POST /final_result────────>│─aggregate attempts───>│
   │                            │ [compute rank]         │
   │<─[final_grade, rank, ...]──│<────────────────────────│
```

## 5. Entity Relationship Diagram (ERD)

```
┌──────────────────────────────────────────────────────────────────────┐
│                          SLEA-SSEM ERD                               │
└──────────────────────────────────────────────────────────────────────┘

      ┌─────────────┐
      │   users     │
      ├─────────────┤
      │ id (PK)     │
      │ ad_id       │
      │ nickname    │
      └──┬──────────┘
         │
         │ 1:N
         ├──────────────────────────┬─────────────────────┐
         │                          │                     │
         ↓                          ↓                     ↓
  ┌───────────────────┐   ┌──────────────────────┐   ┌──────────────┐
  │ user_profile_     │   │  test_sessions       │   │  attempts    │
  │ surveys           │   │                      │   │              │
  ├───────────────────┤   ├──────────────────────┤   ├──────────────┤
  │ id (PK, UUID)     │   │ id (PK, UUID)        │   │ id (PK)      │
  │ user_id (FK)      │   │ user_id (FK)         │   │ user_id (FK) │
  │ self_level        │   │ survey_id (FK)       │   │ survey_id    │
  │ interests (JSON)  │   │ round (1-2)          │   │ final_grade  │
  │ submitted_at      │   │ status               │   │ final_score  │
  └─────┬─────────────┘   │ time_limit_ms        │   │ rank         │
        │                 │ started_at           │   │ percentile   │
        │ 1:N             │ paused_at            │   └────┬─────────┘
        │                 └────────┬──────────────┘        │
        │                          │ 1:N                   │ 1:N
        │                          ├──────────────┬────────┘
        │                          │              │
        │                    ┌─────↓──────────────↓──────┐
        │                    │   questions               │
        │                    ├───────────────────────────┤
        │                    │ id (PK, UUID)             │
        │                    │ session_id (FK)           │
        │                    │ item_type                 │
        │                    │ stem                      │
        │                    │ choices (JSON)            │
        │                    │ answer_schema (JSON)      │
        │                    │ difficulty                │
        │                    │ category                  │
        │                    └─────┬─────────────────────┘
        │                          │ 1:N
        │                          │
        │                    ┌─────↓──────────────┐
        │                    │ attempt_answers    │
        │                    ├────────────────────┤
        │                    │ id (PK, UUID)      │
        │                    │ session_id (FK)    │
        │                    │ question_id (FK)   │
        │                    │ user_answer (JSON) │
        │                    │ is_correct         │
        │                    │ score              │
        │                    │ saved_at           │
        │                    └────────────────────┘
        │
        │ 1:N (for completed attempts)
        │
  ┌─────↓──────────────────┐
  │ attempt_rounds          │
  ├─────────────────────────┤
  │ id (PK, UUID)           │
  │ attempt_id (FK)         │
  │ round_idx               │
  │ score                   │
  │ time_spent_seconds      │
  └─────────────────────────┘

  ┌───────────────────────────────────┐
  │ test_results                      │
  │ (Round별 점수, 약점 분석)         │
  ├───────────────────────────────────┤
  │ id (PK, UUID)                     │
  │ session_id (FK → test_sessions)   │
  │ round (1, 2)                      │
  │ score (0-100%)                    │
  │ correct_count                     │
  │ total_count                       │
  │ wrong_categories (JSON)           │
  └───────────────────────────────────┘
```

## 6. prev_answers Data Example

```
Round 1 완료 후 → Test Result 생성:

{
  "id": "result-1",
  "session_id": "session-s1",
  "round": 1,
  "score": 80.0,
  "correct_count": 4,
  "total_count": 5,
  "wrong_categories": {
    "LLM": 1      ← LLM 카테고리에서 1문제 틀림
  }
}

Round 2 문제 생성 시 Agent에 전달되는 prev_answers:

{
  "prev_answers": [
    {
      "question_id": "q1",
      "category": "LLM",
      "difficulty": 5,
      "item_type": "multiple_choice"
    },
    {
      "question_id": "q2",
      "category": "RAG",
      "difficulty": 4,
      "item_type": "true_false"
    },
    ...
  ]
}

Agent 프롬프트 처리:
1. 이전 라운드 평균: 80점 → 다음 난이도 6-7로 상향
2. 약점 카테고리: LLM 1문제 오답 → Round 2에서 LLM에 2문제 배치
3. 결과: priority_ratio = {"LLM": 2, "RAG": 1, "Others": 2}
```

---

**참고**: 이 다이어그램들은 현재 구현 상태(DB Persistence + Answer Schema Population ✅)를 기반으로 작성되었습니다.
