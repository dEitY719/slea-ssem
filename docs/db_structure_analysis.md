# SLEA-SSEM: Frontend-Backend 통신 Flow 분석

## 1. DB 테이블 구조 (Entity Relationship)

### 1.1 핵심 테이블 관계도

```
users (1) ─┬─ (N) user_profile_surveys (설문 제출 이력)
           │
           └─ (N) test_sessions (테스트 세션 진행 중)
               │
               ├─ (N) questions (각 라운드별 문제들)
               │       │
               │       └─ (N) attempt_answers (사용자 답변)
               │
               ├─ (N) test_results (라운드별 점수 기록)
               │
               └─ (N) attempts (완료된 테스트 기록 - 영구 저장)
                   │
                   └─ (N) attempt_rounds (라운드별 점수)
                       │
                       └─ (N) attempt_answers (라운드별 답변)
```

### 1.2 테이블 상세 정보

**1. users** (사용자 기본 정보)

- id (PK, INTEGER)
- ad_id (Azure AD email, UNIQUE)
- nickname (UNIQUE)

**2. user_profile_surveys** (사용자 설문 - 이력 관리)

- id (PK, UUID)
- user_id (FK → users)
- self_level (Enum: Beginner/Intermediate/Advanced/Elite)
- years_experience (0-60)
- job_role (직책)
- duty (담당 업무)
- interests (JSON Array: ["LLM", "RAG", ...])
- submitted_at (설문 제출 시간)
- **설계 원칙**: 매번 새 레코드 생성 (업데이트 X), 최신 설문은 submitted_at DESC로 조회

**3. test_sessions** (진행 중인 테스트 세션)

- id (PK, UUID)
- user_id (FK → users)
- survey_id (FK → user_profile_surveys) ← 어느 설문을 바탕으로 생성되었는지
- round (1 또는 2, 적응형 테스트의 라운드 번호)
- status (Enum: "in_progress", "completed", "paused")
- time_limit_ms (20분 = 1200000ms)
- started_at (첫 답변 시간)
- paused_at (일시정지 시간)
- created_at, updated_at
- **역할**: 실시간 진행 중인 테스트 상태 관리

**4. questions** (생성된 문제들)

- id (PK, UUID)
- session_id (FK → test_sessions)
- item_type (Enum: "multiple_choice", "true_false", "short_answer")
- stem (문제 텍스트)
- choices (JSON: ["A: 선택지1", "B: 선택지2", ...])
- answer_schema (JSON):
  - multiple_choice: {correct_key: "A", explanation: "설명"}
  - true_false: {correct_key: "true", explanation: "설명"}
  - short_answer: {keywords: ["키워드1", "키워드2"], explanation: "설명"}
- difficulty (1-10)
- category ("LLM", "RAG", "Robotics" 등)
- round (1 또는 2)
- created_at

**5. attempt_answers** (사용자 답변 저장소 - 실시간 저장)

- id (PK, UUID)
- session_id (FK → test_sessions)
- question_id (FK → questions)
- user_answer (JSON: {"selected_key": "B"} 또는 {"answer": "true"} 또는 {"text": "답변"})
- is_correct (Boolean, 채점 후 설정)
- score (0.0-100.0, 채점 후 설정)
- response_time_ms (사용자가 문제 푸는데 걸린 시간)
- saved_at (자동 저장 시간)
- created_at
- **역할**: 세션 진행 중 답변을 즉시 저장 (autosave), 채점 데이터 보관

**6. test_results** (라운드별 최종 점수)

- id (PK, UUID)
- session_id (FK → test_sessions)
- round (1 또는 2)
- score (0-100%, 백분율)
- total_points (점수 합계)
- correct_count (맞힌 문제 수)
- total_count (전체 문제 수 = 5)
- wrong_categories (JSON: {"LLM": 1, "RAG": 2} ← 약점 분석)
- created_at
- **역할**: 라운드 완료 후 점수 기록, Round 2 적응형 생성에 사용

**7. attempts** (완료된 테스트 기록 - 영구 저장)

- id (PK, UUID)
- user_id (FK → users)
- survey_id (FK → user_profile_surveys)
- test_type ("level_test" 또는 "fun_quiz")
- started_at, finished_at
- final_grade (최종 학년: Beginner/Intermediate/Advanced/Elite)
- final_score (최종 점수: 0-100)
- percentile (백분위)
- rank (절대 순위)
- total_candidates (동일 주기 응시자 수)
- status ("in_progress", "completed", "abandoned")
- created_at
- **역할**: 모든 라운드 완료 후 최종 기록 + 랭킹 계산

**8. attempt_rounds** (라운드별 과정 기록)

- id (PK, UUID)
- attempt_id (FK → attempts)
- round_idx (라운드 번호)
- score (이 라운드의 점수)
- time_spent_seconds (이 라운드에 소요된 시간)
- created_at

**9. attempt_answers** (최종 기록용 - 현재는 사용 안 함)

- test_sessions의 attempt_answers와는 별개
- attempts에 속한 최종 답변 기록

---

## 2. API 엔드포인트 & Request/Response 흐름

### 2.1 Question Generation (Round 1)

**Endpoint**: `POST /generate`

**Request**:

```json
{
  "survey_id": "survey-uuid",
  "round": 1,
  "domain": "AI"  // or "food", "LLM", etc.
}
```

**Backend Flow**:

1. QuestionGenerationService.generate_questions() 호출
2. UserProfileSurvey 검증
3. TestSession 생성 (round=1, status="in_progress")
4. Real Agent 호출 (ItemGenAgent via create_agent())
   - GenerateQuestionsRequest 생성:
     - session_id, survey_id, round_idx=1
     - prev_answers=None (Round 1이므로)
     - question_count=5
     - domain="AI"
5. Agent가 5개 문제 생성 → questions 테이블에 저장
6. TestSession 생성됨

**Response**:

```json
{
  "session_id": "session-uuid",
  "questions": [
    {
      "id": "q1-uuid",
      "item_type": "multiple_choice",
      "stem": "LLM의 정의는?",
      "choices": ["A: 작은 모델", "B: 대규모 신경망", ...],
      "answer_schema": {
        "correct_key": "B",
        "explanation": "LLM은..."
      },
      "difficulty": 5,
      "category": "LLM"
    },
    ...
  ]
}
```

### 2.2 Answer Autosave (During Round)

**Endpoint**: `POST /autosave`

**Request**:

```json
{
  "session_id": "session-uuid",
  "question_id": "q1-uuid",
  "user_answer": {
    "selected_key": "B"  // or {"answer": true} or {"text": "..."}
  },
  "response_time_ms": 4500
}
```

**Backend Flow**:

1. AutosaveService.save_answer() 호출
2. TestSession.started_at 설정 (첫 저장 시)
3. AttemptAnswer 생성 또는 업데이트
   - is_correct=False, score=0.0 (아직 채점 안 함)
   - saved_at=now()
4. 시간 초과 확인 (time_limit_ms)
5. 초과하면 session 자동 일시정지

**Response**:

```json
{
  "saved": true,
  "session_id": "session-uuid",
  "question_id": "q1-uuid",
  "saved_at": "2025-01-15T10:30:00Z"
}
```

### 2.3 Individual Answer Scoring

**Endpoint**: `POST /answer/score`

**Request**:

```json
{
  "session_id": "session-uuid",
  "question_id": "q1-uuid"
}
```

**Backend Flow**:

1. ScoringService.score_answer() 호출
2. Question과 AttemptAnswer 조회
3. 질문 유형별 채점:
   - multiple_choice: selected_key == correct_key? → True/False
   - true_false: answer == correct_answer? → True/False
   - short_answer: user_answer 키워드 매칭 → 0.0-1.0
4. 시간 페널티 적용 (선택사항)
5. AttemptAnswer 업데이트: is_correct, score
6. DB 저장

**Response**:

```json
{
  "scored": true,
  "question_id": "q1-uuid",
  "user_answer": {"selected_key": "B"},
  "is_correct": true,
  "score": 100,
  "feedback": "정답입니다!",
  "time_penalty_applied": false,
  "final_score": 100,
  "scored_at": "2025-01-15T10:35:00Z"
}
```

### 2.4 Round Completion & Score Calculation

**Endpoint**: `POST /score` (query param: session_id)

**Request**:

```
POST /score?session_id=session-uuid
```

**Backend Flow**:

1. ScoringService.save_round_result() 호출
2. session의 모든 attempt_answers 조회
3. 전체 점수 계산:
   - correct_count = WHERE is_correct=true
   - score = correct_count / 5 * 100
4. 카테고리별 오답 분석:
   - wrong_categories = {"LLM": 1, "RAG": 0}
5. TestResult 생성:
   - round=1, score=80.0
   - correct_count=4, total_count=5
   - wrong_categories={...}
6. TestSession.status = "completed"

**Response**:

```json
{
  "session_id": "session-uuid",
  "round": 1,
  "score": 80.0,
  "correct_count": 4,
  "total_count": 5,
  "wrong_categories": {"LLM": 1, "RAG": 0}
}
```

### 2.5 Adaptive Round 2 Generation

**Endpoint**: `POST /generate-adaptive`

**Request**:

```json
{
  "previous_session_id": "session-uuid-round1",
  "round": 2
}
```

**Backend Flow**:

1. QuestionGenerationService.generate_questions_adaptive() 호출
2. TestResult(round=1) 조회 (이전 라운드 점수)
3. AdaptiveDifficultyService.get_adaptive_generation_params() 호출
   - prev_score 기반 difficulty 조정
   - wrong_categories 기반 priority_ratio 계산
     예: {"LLM": 2, "RAG": 1} ← LLM에 집중
4. 새로운 TestSession 생성 (round=2)
5. Mock 또는 Real Agent로 5개 문제 생성
   - 우선 카테고리 배치: LLM 2문제, RAG 1문제, 기타 2문제
   - 조정된 난이도 적용
6. Question 테이블에 저장

**Response**:

```json
{
  "session_id": "new-session-uuid",
  "questions": [...],
  "adaptive_params": {
    "previous_score": 80.0,
    "adjusted_difficulty": 6.5,
    "priority_ratio": {"LLM": 2, "RAG": 1}
  }
}
```

### 2.6 Session Resume (After Pause/Timeout)

**Endpoint**: `GET /resume?session_id=session-uuid`

**Backend Flow**:

1. AutosaveService.get_session_state() 호출
2. TestSession 조회
3. 모든 question 조회
4. 모든 attempt_answer 조회 (answered 리스트)
5. answered_count, next_question_index 계산

**Response**:

```json
{
  "session_id": "session-uuid",
  "status": "in_progress",
  "round": 1,
  "answered_count": 3,
  "total_questions": 5,
  "next_question_index": 3,
  "previous_answers": [
    {
      "question_id": "q1-uuid",
      "user_answer": {"selected_key": "B"},
      "saved_at": "2025-01-15T10:30:00Z"
    },
    ...
  ],
  "time_status": {
    "exceeded": false,
    "elapsed_ms": 300000,
    "remaining_ms": 900000
  }
}
```

---

## 3. Key Concepts Clarification

### 3.1 "prev_answers" 의미

**What it is**: Round 2에서 Round 1의 답변 기록을 참고하여 **적응형 문제 생성**을 위한 컨텍스트 정보

**When**:

- Round 1: prev_answers=None (이전 라운드 없음)
- Round 2: prev_answers = [Round 1에서의 질문/답변 정보]

**What it contains** (src/backend/services/question_gen_service.py line 431-439):

```python
prev_answers = [
    {
        "question_id": "q1-uuid",
        "category": "LLM",
        "difficulty": 5,
        "item_type": "multiple_choice"
    },
    ...
]
```

**How it's used**: Agent 프롬프트에 포함되어 다음 라운드 어려움도 조정에 반영

### 3.2 1문제씩 vs 라운드 완료 후 일괄 채점?

**Current Design**: **하이브리드**

1. **답변 저장**: 1문제씩 실시간 저장 (autosave)
   - AttemptAnswer에 user_answer만 저장
   - is_correct=False, score=0.0 (아직 채점 안 됨)

2. **실시간 채점** (선택사항):
   - `/answer/score` API로 1문제씩 즉시 채점 가능
   - is_correct, score 업데이트

3. **라운드 완료 후**:
   - `/score` API로 TestResult 생성
   - 모든 attempt_answer의 is_correct/score 기반 최종 점수 계산
   - wrong_categories 분석

**Frontend 구현 선택지**:

- Option A: 라운드 완료 후 일괄 채점 (간단, 유저는 라운드 끝까지 채점 기다림)
- Option B: 사용자 선택 후 즉시 채점 (좋은 UX, API 요청 5배 증가)

### 3.3 Session과 Round의 관계

```
1 User
├─ Round 1 Test Session (session_id=s1)
│  ├─ 5 Questions
│  ├─ 5 Attempt Answers
│  └─ 1 Test Result (round=1, score=80%)
│
└─ Round 2 Test Session (session_id=s2)  ← 다른 session_id!
   ├─ 5 Questions (적응형 난이도)
   ├─ 5 Attempt Answers
   └─ 1 Test Result (round=2, score=85%)

최종 Attempt 기록:
└─ 1 Attempt (final_score = round1+2 평균 또는 round2만)
   ├─ AttemptRound (round=1, score=80%)
   └─ AttemptRound (round=2, score=85%)
```

**Design Principle**:

- TestSession은 라운드별로 **독립적** (session_id가 다름)
- 라운드 간 적응형 정보는 TestResult 통해 조회
- 최종 기록은 Attempt에 통합 저장

---

## 4. Frontend-Backend 통신 Flow (정리)

### 4.1 표준 2-Round Test Flow

```
1. [Frontend] 설문 선택/제출
   ↓ (survey_id 획득)
   
2. [API] POST /generate
   ← Response: session_id, 5 questions
   
3. [Frontend] 문제 1부터 순서대로 표시
   
4. [Loop for Q1-Q5]
   a. 사용자 답변 입력
   b. [API] POST /autosave
   c. [Frontend] "저장됨" 표시
   d. [Optional] [API] POST /answer/score (즉시 채점)
   
5. [Frontend] 제출 버튼 클릭
   ↓
   
6. [API] POST /score?session_id=s1
   ← Response: round=1, score=80%, wrong_categories={...}
   
7. [Frontend] "Round 1 완료, Round 2로 진행?" 팝업
   
8. [API] POST /generate-adaptive
   ← Response: new_session_id, 5 adaptive questions
   
9. [Repeat steps 4-6 for Round 2]
   
10. [API] 최종 점수/랭킹 조회
    ← Response: final_grade, final_score, rank, percentile
```

### 4.2 Key Data Field Mapping

| Frontend 필요 | Backend Table | Field | Note |
|---|---|---|---|
| 현재 문제 | questions | id, stem, choices, difficulty | session_id로 필터 |
| 사용자 답변 | attempt_answers | user_answer | 실시간 저장 |
| 채점 결과 | attempt_answers | is_correct, score | API `/answer/score` 후 |
| 라운드 점수 | test_results | score, correct_count | `/score` API 후 |
| 약점 카테고리 | test_results | wrong_categories | Round 2 적응형 기반 |
| 재개 정보 | attempt_answers | 모든 레코드 | `/resume` API로 조회 |

---

## 5. 데이터 저장 경로 요약

### Answer 데이터 저장 경로

```
사용자 입력
  ↓
attempt_answers (user_answer만 저장, is_correct=False, score=0.0)
  ↓ [선택사항: 즉시 채점]
attempt_answers (is_correct, score 업데이트)
  ↓ [라운드 완료 후]
test_results (round, score, correct_count, wrong_categories 계산)
  ↓ [모든 라운드 완료 후]
attempts (final_grade, final_score, rank 저장)
attempt_rounds (라운드별 점수 저장)
```

### 적응형 난이도 조정 경로

```
Round 1 완료
  ↓
test_results(round=1) 생성 (wrong_categories 포함)
  ↓
[Round 2 요청]
  ↓
AdaptiveDifficultyService.get_adaptive_generation_params()
  ├─ prev_score 조회
  └─ wrong_categories 기반 priority_ratio 계산
  ↓
generate_questions_adaptive() (priority 카테고리에 더 많은 문제 할당)
  ↓
Round 2 questions 생성 (조정된 난이도 + 우선 카테고리)
```

---

## 6. 특이사항 & 주의점

1. **UserProfileSurvey는 이력 관리**
   - 매번 새 레코드 생성 (UPDATE 없음)
   - 최신 설문 = MAX(submitted_at)

2. **TestSession과 Attempt는 별개**
   - TestSession: 진행 중인 테스트 (started_at만 설정)
   - Attempt: 완료된 테스트 (finished_at, final_grade 설정)

3. **AttemptAnswer는 두 가지 역할**
   - session 진행 중: attempt_answers (session_id 기준)
   - 최종 기록: attempt 하위의 attempt_answers (attempt_id 기준)

4. **시간 초과 처리**
   - test_sessions.time_limit_ms (기본 20분)
   - autosave 후 check_time_limit() 호출
   - 초과 시 자동으로 session.status = "paused"

5. **이력 조회**
   - 이전 라운드 정보 필요: test_results 조회 (session_id로)
   - 사용자 모든 시도: attempts 조회 (user_id로)

---

## 7. API 엔드포인트 전체 목록

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| POST | /generate | Round 1 문제 생성 | JWT |
| POST | /autosave | 답변 실시간 저장 | JWT |
| POST | /answer/score | 1문제 채점 | JWT |
| POST | /score | 라운드 완료 점수 계산 | JWT |
| POST | /generate-adaptive | Round 2+ 적응형 문제 생성 | JWT |
| GET | /resume | 일시정지 후 재개 | JWT |
| PUT | /session/{id}/status | 세션 상태 변경 (pause/resume) | JWT |
| GET | /session/{id}/time-status | 남은 시간 확인 | JWT |
| POST | /explanations | 해설 생성 | JWT |
