# Agent 테스트 & 백엔드 통합 시나리오

**문서 작성 날짜**: 2025-11-11
**버전**: 1.0
**상태**: 👨‍💼 검토 대기 중 (동료 A, B 의견 통합)

---

## 목차

1. [개요](#개요)
2. [동료 의견 요약](#동료-의견-요약)
3. [REQ ID 체계](#req-id-체계)
4. [Phase별 세부 계획](#phase별-세부-계획)
5. [타임라인 & 진행 추적](#타임라인--진행-추적)

---

## 개요

### 현재 상황

- **완성됨**: Agent 구현 (`src/agent/llm_agent.py` 900+줄)
- **완성됨**: Agent 테스트 (`tests/agent/test_llm_agent.py` 1290줄, Mock 기반)
- **완성됨**: FastAPI 백엔드 (Mock 데이터 사용)
- **필요함**: 실제 LLM 통합, 백엔드 연결, E2E 테스트

### 목표

1. ✅ **Phase 0**: Agent가 실제 Google Gemini LLM과 정상 동작하는지 확인
2. ✅ **Phase 1**: CLI에서 직접 Agent를 테스트할 수 있는 명령어 추가
3. ✅ **Phase 2**: FastAPI 백엔드가 Agent를 호출하도록 통합
4. ✅ **Phase 3**: 전체 workflow (Frontend → Agent → Backend → DB) 테스트

### 워크플로우 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│ 최종 완성된 워크플로우                                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (레벨테스트 버튼)                                   │
│         ↓                                                     │
│  FastAPI Endpoint (/api/v1/items/generate)                   │
│         ↓                                                     │
│  QuestionGenerationService.generate_questions()             │
│         ↓                                                     │
│  ItemGenAgent.generate_questions()  ← Agent 호출             │
│         ↓                                                     │
│  Google Gemini LLM + FastMCP Tools (1-5)                    │
│         ↓                                                     │
│  Database (test_sessions, test_questions)                   │
│         ↓                                                     │
│  HTTP Response (JSON with generated items)                  │
│                                                               │
│  ─────────────────────────────────────────────────────────  │
│                                                               │
│  단일 채점 워크플로우:                                        │
│  User Answer → Tool 6 (score_and_explain) → Score + Explanation
│                                                               │
│  배치 채점 워크플로우:                                        │
│  Multiple Answers → Tool 6 (Parallel) → Batch Results       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 동료 의견 요약

### 동료 A (CLI 구조 개선) ✅

**핵심**: Agent는 SSE 서버가 아니라 일회성 객체. CLI 명령어로 직접 호출 가능.

**주요 제안**:

- `./tools/dev.sh cli agent generate-questions --survey-id "..."` 형태의 명령어 추가
- 기존 CLI 구조 (`src/cli/main.py`, `src/cli/actions/`) 활용
- Phase 1에서 실행

### 동료 B (Agent 검증 & 백엔드 통합) ✅

**핵심**: Agent 동작 확인 → Backend 통합 순서로 진행

**주요 제안**:

- Phase 0: Python 스크립트로 Agent 최소 재현 (inline script)
- `LANGCHAIN_DEBUG=1` 또는 `LANGCHAIN_TRACING_V2=1`로 Thought→Action→Observation 추적
- Phase 2: `QuestionGenerationService`의 Mock을 `await create_agent()` 호출로 변경
- SSE/Streaming은 선택사항 (`astream_events` 지원)

---

## REQ ID 체계

### REQ ID 규칙 (CLAUDE.md 준수)

| 포맷 | 용도 | 예시 |
|------|------|------|
| `REQ-A-[Feature]-[Number]` | Agent 관련 | `REQ-A-Agent-Sanity-0` |
| `REQ-CLI-[Domain]-[Number]` | CLI 기능 | `REQ-CLI-Agent-1` |
| `REQ-B-[Feature]-[Number]` | Backend 관련 | `REQ-B-Scoring-1` |

### 세부 REQ ID 정의

#### 🔵 Phase 0: Agent 기본 동작 확인

**REQ-A-Agent-Sanity-0: Agent 기본 동작 검증 (Sanity Check)**

```yaml
설명: 실제 Google Gemini LLM을 사용하여 Agent가 정상 작동하는지 확인
사용 예:
  export GEMINI_API_KEY="your_key"
  export LANGCHAIN_DEBUG=1
  uv run python scripts/test_agent_sanity_check.py
기대 출력:
  ✅ Agent initialized
  📝 Generating questions...
  [Tool 1 호출] get_user_profile
  [Tool 3 호출] get_difficulty_keywords
  [Tool 5 호출] save_generated_question (3 items)
  ✅ Generation Complete: 3 items generated

Acceptance Criteria:
  - [ ] GEMINI_API_KEY 환경변수 확인
  - [ ] Agent 초기화 성공
  - [ ] LLM API 연결 성공
  - [ ] Tools 호출 확인 (LANGCHAIN_DEBUG 출력)
  - [ ] 문항 3개 이상 생성
  - [ ] JSON 응답 파싱 성공

Priority: 🔴 HIGH (모든 다음 단계의 기초)
Dependencies: []
Status: ⏳ Backlog
```

---

#### 🟢 Phase 1: CLI 명령어 확장 (계층적 구조)

### CLI 메뉴 구조 (최종)

```
slea-ssem CLI 📋

Commands:

  survey                          자기평가 Survey 관리
    schema                        Survey 폼 스키마 조회
    submit                        Survey 데이터 제출 및 저장

  agent                           Agent 문항 생성 & 채점
    generate-questions            📝 문항 생성 (Tool 1-5 자동 체인)
    score-answer                  📋 답변 채점 (Tool 6)
    batch-score                   📊 배치 채점 (Tool 6 병렬)
    tools                         🔧 개별 Tool 디버깅
      tool-1                      Tool 1: User Profile 조회
      tool-2                      Tool 2: 질문 템플릿 검색
      tool-3                      Tool 3: 난이도별 키워드 조회
      tool-4                      Tool 4: 문항 품질 검증
      tool-5                      Tool 5: 문항 저장
      tool-6                      Tool 6: 채점 & 해설

  clear                           터미널 화면 정리
  exit                            CLI 종료
  help                            도움말 표시
```

---

**REQ-CLI-Agent-1: agent 명령 그룹 및 계층적 메뉴 구조 구현**

```yaml
설명: CLI에 agent 명령 그룹 추가 (계층적 구조)
      - agent generate-questions (워크플로우)
      - agent score-answer (단일 채점)
      - agent batch-score (배치 채점)
      - agent tools (개별 Tool 디버깅)

사용 예:
  ./tools/dev.sh cli agent --help
  ./tools/dev.sh cli agent tools --help
  ./tools/dev.sh cli agent tools tool-1 --help

기대 출력 (agent --help):
  Usage: agent [OPTIONS] COMMAND [ARGS]...

  Agent-based question generation and scoring

  Options:
    --help  Show this message and exit.

  Commands:
    batch-score           📊 배치 채점 (복수 답변, 병렬)
    generate-questions    📝 문항 생성 (Tool 1-5 체인)
    score-answer          📋 답변 채점 (Tool 6)
    tools                 🔧 개별 Tool 디버깅

Acceptance Criteria:
  - [ ] agent 명령 그룹 등록
  - [ ] 4개 하위 명령 인식 (generate-questions, score-answer, batch-score, tools)
  - [ ] agent --help 실행 가능
  - [ ] agent [command] --help 실행 가능
  - [ ] 각 명령 설명 명확
  - [ ] tools 하위에 tool-1~6 리스트 표시

Priority: 🔴 HIGH
Dependencies: [REQ-A-Agent-Sanity-0]
Status: ⏳ Backlog
```

**REQ-CLI-Agent-2: agent generate-questions 명령 (전체 파이프라인)**

```yaml
설명: Tool 1-5를 자동으로 체인하여 문항을 생성하는 명령
      이 명령은 백엔드의 /api/v1/items/generate와 동일한 동작 수행

사용 예:
  # Round 1 (기본)
  ./tools/dev.sh cli agent generate-questions --survey-id "survey_123"

  # Round 2 (적응형, 이전 답변 포함)
  ./tools/dev.sh cli agent generate-questions \
    --survey-id "survey_123" \
    --round 2 \
    --prev-answers '[{"item_id":"q1","score":85},{"item_id":"q2","score":60}]'

기대 출력:
  🚀 Initializing Agent... (GEMINI_API_KEY required)
  ✅ Agent initialized

  📝 Generating questions...
     survey_id=survey_123, round=1

  ✅ Generation Complete
     round_id: round_20251111_123456_001
     items generated: 3
     failed: 0
     agent_steps: 12

  📋 Generated Items:
  ┏━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
  ┃ ID         ┃ Type        ┃ Difficult ┃ Validation
  ┣━━━━━━━━━━━━╋━━━━━━━━━━━━━╋━━━━━━━━━━━╋━━━━━━━━━━┫
  ┃ q_00001... ┃ short_answer┃ 5        ┃ 0.92
  ┃ q_00002... ┃ mult_choice ┃ 7        ┃ 0.89
  ┃ q_00003... ┃ true_false  ┃ 3        ┃ 0.95
  ┗━━━━━━━━━━━━┛━━━━━━━━━━━━━┛━━━━━━━━━━━┛━━━━━━━━━━┛

  📄 First Item Details:
     Stem: What is a transformer in NLP?
     Answer Schema: keyword_match
     Keywords: [transformer, attention, neural]

Acceptance Criteria:
  - [ ] --survey-id 파라미터 필수
  - [ ] --round 파라미터 기본값 1 (1~2)
  - [ ] --prev-answers JSON 파싱 (Round 2 용)
  - [ ] LANGCHAIN_DEBUG 환경변수 지원
  - [ ] Agent 호출 성공
  - [ ] 문항 3개 이상 생성
  - [ ] Rich Table 포맷 출력
  - [ ] round_id, agent_steps, failed_count 표시
  - [ ] 에러 처리 (GEMINI_API_KEY 없음, API 타임아웃, 파싱 에러)
  - [ ] Markdown 문법 사용 (Tool 1-5 단계 출력 필요시)

Priority: 🔴 HIGH
Dependencies: [REQ-CLI-Agent-1, REQ-A-Agent-Sanity-0]
Status: ⏳ Backlog
```

**REQ-CLI-Agent-3: agent score-answer 명령 (단일 답변 채점)**

```yaml
설명: Tool 6을 호출하여 단일 답변을 채점하는 명령

사용 예:
  ./tools/dev.sh cli agent score-answer \
    --round-id "round_123" \
    --item-id "q_001" \
    --user-answer "Transformers use attention mechanism"

  # 추가 정보 포함
  ./tools/dev.sh cli agent score-answer \
    --round-id "round_123" \
    --item-id "q_001" \
    --user-answer "My answer" \
    --question-type "short_answer" \
    --correct-answer "Expected answer" \
    --correct-keywords "key1,key2,key3"

기대 출력:
  🚀 Initializing Agent...
  ✅ Agent initialized

  📋 Scoring answer...
     item_id=q_001, type=short_answer, response_time=5000ms

  ✅ Scoring Complete
     score: 75.5 / 100
     correct: ✓ (partial)
     explanation: Good understanding of transformer attention mechanism...

  📊 Details:
     Extracted Keywords: [transformer, attention, mechanism]
     Feedback: Consider mentioning positional encoding for completeness
     Graded At: 2025-11-11T14:30:00Z

Acceptance Criteria:
  - [ ] --round-id 파라미터 필수
  - [ ] --item-id 파라미터 필수
  - [ ] --user-answer 파라미터 필수
  - [ ] --question-type 기본값 'short_answer'
  - [ ] Score 0-100 범위 표시
  - [ ] is_correct 불린값 표시 (✓/✗)
  - [ ] explanation 문자열 출력
  - [ ] extracted_keywords 리스트 출력
  - [ ] feedback 옵션값 표시 (있을 경우)
  - [ ] 에러 처리 (필수 파라미터 누락, LLM 오류)

Priority: 🟡 MEDIUM
Dependencies: [REQ-CLI-Agent-1, REQ-A-Agent-Sanity-0]
Status: ⏳ Backlog
```

**REQ-CLI-Agent-4: agent batch-score 명령 (배치 채점)**

```yaml
설명: 여러 답변을 병렬로 채점하는 명령 (Tool 6 병렬 호출)

사용 예:
  ./tools/dev.sh cli agent batch-score \
    --round-id "round_123" \
    --answers-file "answers.json"

  # answers.json 형식:
  {
    "answers": [
      {"item_id": "q_001", "user_answer": "Answer 1", "response_time_ms": 5000},
      {"item_id": "q_002", "user_answer": "Answer 2", "response_time_ms": 4000},
      {"item_id": "q_003", "user_answer": "Answer 3", "response_time_ms": 6000}
    ]
  }

기대 출력:
  🚀 Initializing Agent...
  ✅ Agent initialized

  📊 Batch Scoring...
     round_id=round_123, items=3

  ⏳ Processing (parallel)...
  ✅ q_001: 90.0 ✓
  ✅ q_002: 75.5 ✓ (partial)
  ✅ q_003: 45.0 ✗

  📈 Batch Results:
  ┏━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━┓
  ┃ Item   ┃ Score┃ Correct┃ Keywords┃
  ┣━━━━━━━━╋━━━━━━╋━━━━━━━╋━━━━━━━━━┫
  ┃ q_001  ┃ 90.0 ┃ ✓      ┃ [k1,k2]┃
  ┃ q_002  ┃ 75.5 ┃ ~ (partial) ┃ [k3]┃
  ┃ q_003  ┃ 45.0 ┃ ✗      ┃ []     ┃
  ┗━━━━━━━━┛━━━━━━┛━━━━━━━┛━━━━━━━━━┛

  📊 Round Statistics:
     Round Score: 70.2 (average)
     Correct Count: 1 + 1 partial = ~2
     Total Count: 3
     Avg Response Time: 5000ms

Acceptance Criteria:
  - [ ] --round-id 파라미터 필수
  - [ ] --answers-file 파라미터 필수 (JSON 파일)
  - [ ] 병렬 처리 (순차 아님)
  - [ ] 진행 상황 실시간 출력
  - [ ] 최종 통계 표시 (round_score, correct_count, avg_time)
  - [ ] Rich Table로 결과 표시
  - [ ] 부분 정답 처리 (partial 표시)
  - [ ] 에러 처리 (파일 없음, JSON 파싱 에러)

Priority: 🟡 MEDIUM
Dependencies: [REQ-CLI-Agent-3, REQ-A-Agent-Sanity-0]
Status: ⏳ Backlog
```

**REQ-CLI-Agent-5: agent tools [tool-name] 명령 (개별 Tool 디버깅)**

```yaml
설명: 각 Tool을 개별적으로 테스트하는 디버깅 명령어
      Tool 1-5: 개별 입력/출력 확인
      Tool 6: 채점 단계별 검증

하위 명령:
  tool-1 (get-user-profile)
  tool-2 (search-templates)
  tool-3 (get-keywords)
  tool-4 (validate-question)
  tool-5 (save-question)
  tool-6 (score-explain)

사용 예:
  # Tool 1: User Profile 조회
  ./tools/dev.sh cli agent tools tool-1 --survey-id "survey_123"

  # Tool 3: 키워드 조회
  ./tools/dev.sh cli agent tools tool-3 \
    --user-level "intermediate" \
    --difficulty 5 \
    --category "AI"

  # Tool 6: 단일 채점 (디버깅)
  ./tools/dev.sh cli agent tools tool-6 \
    --question-type "short_answer" \
    --user-answer "my answer" \
    --correct-keywords "key1,key2"

기대 출력 (Tool 1):
  🔧 Testing Tool 1: get_user_profile

  Input:
    survey_id: survey_123

  Output:
  {
    "user_level": "intermediate",
    "experience_years": 5,
    "interests": ["AI", "NLP"],
    "previous_scores": [85, 90, 78]
  }

  ✅ Tool execution successful

기대 출력 (Tool 6):
  🔧 Testing Tool 6: score_and_explain

  Input:
    question_type: short_answer
    user_answer: my answer
    correct_keywords: [key1, key2]

  Output:
  {
    "is_correct": true,
    "score": 85.0,
    "explanation": "Good answer with keywords...",
    "extracted_keywords": ["key1", "key2"],
    "feedback": "Could improve by...",
    "graded_at": "2025-11-11T14:30:00Z"
  }

  ✅ Tool execution successful

Acceptance Criteria:
  - [ ] 6개 Tool별 명령어 구현 (tool-1~6)
  - [ ] 각 Tool의 입력 파라미터 명시
  - [ ] JSON 포맷으로 출력
  - [ ] 실행 성공/실패 상태 표시
  - [ ] 각 Tool에 --help 지원
  - [ ] 에러 처리 및 메시지 출력
  - [ ] Tool 실행 시간 표시 (diagnostic용)

Priority: 🟡 MEDIUM (개발자 디버깅 목적)
Dependencies: [REQ-CLI-Agent-1]
Status: ⏳ Backlog
```

---

#### 🟣 Phase 2: FastAPI 백엔드 통합

**REQ-A-Agent-Backend-1: QuestionGenerationService Agent 통합**

```yaml
설명: QuestionGenerationService.generate_questions()가 Mock 데이터 대신 실제 Agent를 호출
현재: Mock 데이터 반환
변경: await create_agent().generate_questions() 호출

수정 위치:
  - src/backend/services/question_gen_service.py (generate_questions 메서드)

코드 변경:
  # Before (현재)
  def generate_questions(self, survey_id: str, round_num: int):
      return mock_questions  # Mock 데이터

  # After (변경 후)
  async def generate_questions(self, survey_id: str, round_num: int):
      agent = await create_agent()
      request = GenerateQuestionsRequest(
          survey_id=survey_id,
          round_idx=round_num,
          prev_answers=self._get_previous_answers(survey_id, round_num-1)
      )
      response = await agent.generate_questions(request)
      # Save to DB
      self._save_to_db(response)
      return response

Acceptance Criteria:
  - [ ] generate_questions이 async로 변경
  - [ ] create_agent() 호출 성공
  - [ ] GenerateQuestionsRequest 생성 및 전달
  - [ ] 이전 라운드 답변 (prev_answers) 조회
  - [ ] Agent 응답을 DB에 저장
  - [ ] 기존 API 응답 포맷 유지
  - [ ] 에러 처리 (LLM 타임아웃, DB 오류 등)
  - [ ] 타입 힌트 완벽
  - [ ] Docstring 작성
  - [ ] 단위 테스트 통과

Priority: 🔴 HIGH (가장 중요한 통합)
Dependencies: [REQ-CLI-Agent-2, REQ-A-Agent-Sanity-0]
Status: ⏳ Backlog
```

**REQ-A-Agent-Backend-2: ScoringService Agent Tool 6 통합**

```yaml
설명: ScoringService.score_answer()가 Mock 대신 Agent Tool 6를 호출
현재: Mock 채점 (정확 매칭만)
변경: await create_agent().score_and_explain() 호출

수정 위치:
  - src/backend/services/scoring_service.py (score_answer 메서드)

코드 변경:
  async def score_answer(self, session_id: str, question_id: str, user_answer: str):
      agent = await create_agent()
      request = ScoreAnswerRequest(
          round_id=session_id,
          item_id=question_id,
          user_answer=user_answer,
          question_type=question.item_type,
          correct_answer=question.correct_answer,
      )
      response = await agent.score_and_explain(request)
      self._save_to_db(response)
      return response

Acceptance Criteria:
  - [ ] score_answer이 async로 변경
  - [ ] create_agent() 호출
  - [ ] ScoreAnswerRequest 구성 (질문 정보 포함)
  - [ ] Tool 6 응답 처리 (score, explanation, keywords)
  - [ ] 채점 결과 DB 저장
  - [ ] 기존 ScoringService 인터페이스 유지
  - [ ] 에러 처리 (LLM 오류, 질문 없음 등)
  - [ ] 배치 채점도 지원 (submit_answers)
  - [ ] 모든 테스트 통과

Priority: 🟡 MEDIUM (Phase 2의 선택사항)
Dependencies: [REQ-CLI-Agent-3, REQ-A-Agent-Sanity-0]
Status: ⏳ Backlog
```

---

#### 🟠 Phase 3: E2E 통합 테스트

**REQ-A-Agent-Integration-1: E2E 통합 테스트 스위트**

```yaml
설명: 전체 workflow (CLI → FastAPI → Agent → DB) 통합 테스트
테스트 시나리오:
  1. CLI에서 문항 생성 요청
  2. FastAPI 엔드포인트 호출
  3. Agent가 LLM 호출
  4. DB에 저장
  5. 채점 워크플로우
  6. 배치 채점

테스트 위치:
  - tests/integration/test_agent_backend_e2e.py

테스트 케이스:
  1. test_generate_questions_e2e
     - Flow: API → Service → Agent → DB
     - Verify: 문항 3개 생성, DB 저장, 응답 포맷

  2. test_score_single_answer_e2e
     - Flow: API → Service → Tool 6 → DB
     - Verify: 점수, 설명, 키워드 추출

  3. test_batch_scoring_e2e
     - Flow: API → Service → Tool 6 (Parallel) → DB
     - Verify: 배치 결과, 라운드 통계

  4. test_adaptive_questioning_e2e
     - Flow: Round 1 → Score → Round 2 (난이도 조정)
     - Verify: 난이도 변화

  5. test_error_handling_e2e
     - GEMINI_API_KEY 없음
     - LLM 타임아웃
     - DB 오류

Acceptance Criteria:
  - [ ] 4개 이상의 통합 테스트 케이스
  - [ ] 각 테스트가 실제 DB 사용 (테스트 DB)
  - [ ] 각 테스트가 실제 Agent 호출 (Mock 제외)
  - [ ] API 응답 포맷 검증
  - [ ] DB 데이터 무결성 검증
  - [ ] 에러 케이스 포함
  - [ ] 테스트 실행 시간 < 5분
  - [ ] 모든 테스트 통과 (tox -e py311)

Priority: 🟡 MEDIUM
Dependencies: [REQ-A-Agent-Backend-1, REQ-A-Agent-Backend-2]
Status: ⏳ Backlog
```

---

## Phase별 세부 계획

### Phase 0️⃣: Agent 기본 동작 확인 (REQ-A-Agent-Sanity-0)

**준비 작업**:

```bash
# 1. 환경변수 설정
export GEMINI_API_KEY="your_actual_key"
export LANGCHAIN_DEBUG=1  # 또는 LANGCHAIN_TRACING_V2=1

# 2. 프로젝트 준비
uv sync
```

**구현 (30분)**:

1. `scripts/test_agent_sanity_check.py` 생성
   - `create_agent()` 호출
   - `GenerateQuestionsRequest` 생성
   - `agent.generate_questions()` 실행
   - JSON 출력

2. 실행:

   ```bash
   uv run python scripts/test_agent_sanity_check.py
   ```

3. 검증:
   - 로그 출력 확인
   - Tool 호출 추적 (Tool 1, 3, 5)
   - 최종 출력 JSON 포맷

**산출물**:

- `scripts/test_agent_sanity_check.py`
- `docs/progress/REQ-A-Agent-Sanity-0.md` (Phase 1-4 문서)

---

### Phase 1️⃣: CLI 명령어 확장 (REQ-CLI-Agent-1, 2, 3)

**파일 구조**:

```
src/cli/
├── main.py                    ← 수정: agent 명령 등록
└── actions/
    └── [NEW] agent.py         ← 생성: agent 명령 구현
```

**Task 1-1: CLI 구조 파악 (10분)**

- `src/cli/main.py` 읽기 (명령 그룹 구조)
- `src/cli/actions/questions.py` 참고 (구현 패턴)
- `run.py` 확인 (진입점)

**Task 1-2: agent.py 구현 (30분)**

```python
# src/cli/actions/agent.py

async def generate_questions(survey_id, round_idx, prev_answers):
    """Agent 호출 및 결과 출력"""
    agent = await create_agent()
    request = GenerateQuestionsRequest(...)
    response = await agent.generate_questions(request)
    _display_response(response)

async def score_answer(round_id, item_id, user_answer, ...):
    """Tool 6 호출 및 채점 결과 출력"""
    agent = await create_agent()
    request = ScoreAnswerRequest(...)
    response = await agent.score_and_explain(request)
    _display_score(response)
```

**Task 1-3: main.py 수정 (10분)**

```python
from src.cli.actions import agent

@main.group()
def agent_cmd():
    """Agent-based operations"""
    pass

@agent_cmd.command()
@click.option("--survey-id", required=True)
@click.option("--round", default=1, type=int)
def generate_questions(survey_id, round):
    asyncio.run(agent.generate_questions(survey_id, round))

main.add_command(agent_cmd, name="agent")
```

**Task 1-4: 테스트 (10분)**

```bash
./tools/dev.sh cli agent --help
./tools/dev.sh cli agent generate-questions --survey-id "test_001" --round 1
./tools/dev.sh cli agent score-answer --round-id "r1" --item-id "q1" --user-answer "test"
```

**산출물**:

- `src/cli/actions/agent.py`
- `src/cli/main.py` 수정
- `docs/progress/REQ-CLI-Agent-{1,2,3}.md` (각각 Phase 1-4 문서)

---

### Phase 2️⃣: FastAPI 백엔드 통합 (REQ-A-Agent-Backend-1, 2)

**Task 2-1: QuestionGenerationService 수정 (1시간)**

**파일**: `src/backend/services/question_gen_service.py`

**주요 변경**:

```python
# Before (현재 - Mock)
class QuestionGenerationService:
    def generate_questions(self, survey_id: str, round_num: int) -> dict:
        return MOCK_QUESTIONS

# After (변경 후 - Agent)
class QuestionGenerationService:
    async def generate_questions(self, survey_id: str, round_num: int) -> dict:
        # 1. Agent 생성
        agent = await create_agent()

        # 2. 요청 생성 (이전 답변 포함)
        prev_answers = self._get_previous_answers(survey_id, round_num - 1)
        request = GenerateQuestionsRequest(
            survey_id=survey_id,
            round_idx=round_num,
            prev_answers=prev_answers,
        )

        # 3. Agent 호출
        response = await agent.generate_questions(request)

        # 4. DB 저장
        session = self._create_test_session(survey_id, round_num)
        questions = self._save_questions_to_db(session, response.items)

        # 5. 응답 반환
        return {
            "session_id": session.id,
            "questions": [self._format_q(q) for q in questions],
            "time_limit_seconds": response.time_limit_seconds,
            "agent_steps": response.agent_steps,
        }
```

**추가 메서드**:

```python
def _get_previous_answers(self, survey_id: str, prev_round: int) -> list[dict]:
    """이전 라운드 답변 조회"""
    # DB에서 previous_round의 test_responses 조회
    # Return: [{"item_id": "q1", "score": 85}, ...]

def _create_test_session(self, survey_id: str, round_num: int) -> TestSession:
    """새 TestSession 생성"""
    # TestSession ORM 객체 생성 및 저장

def _save_questions_to_db(self, session, items) -> list[Question]:
    """생성된 문항을 Question 테이블에 저장"""
    # GeneratedItem → Question ORM 변환
    # DB 저장

def _format_question(self, q: Question) -> dict:
    """Question ORM → API 응답 포맷"""
    return {
        "id": q.id,
        "item_type": q.item_type,
        "stem": q.stem,
        "choices": q.choices,
        "answer_schema": {...},
        "difficulty": q.difficulty,
        "category": q.category,
    }
```

**Task 2-2: API 엔드포인트 검증 (15분)**

**파일**: `src/backend/api/questions.py`

```python
@router.post("/generate")
async def generate_questions(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
) -> GenerateQuestionsResponse:
    """Generate questions using Agent"""
    service = QuestionGenerationService(db)
    result = await service.generate_questions(
        request.survey_id,
        request.round
    )
    return GenerateQuestionsResponse(**result)
```

**Task 2-3: ScoringService 수정 (선택사항, 1시간)**

**파일**: `src/backend/services/scoring_service.py`

```python
async def score_answer(
    self,
    session_id: str,
    question_id: str,
    user_answer: str,
    response_time_ms: int = 0,
) -> dict:
    """Score answer using Agent Tool 6"""
    agent = await create_agent()

    # 질문 정보 조회
    question = self.db.query(Question).filter_by(id=question_id).first()
    if not question:
        raise ValueError(f"Question {question_id} not found")

    # 채점 요청
    request = ScoreAnswerRequest(
        round_id=session_id,
        item_id=question_id,
        user_answer=user_answer,
        question_type=question.item_type,
        correct_answer=question.correct_answer,
        correct_keywords=question.correct_keywords,
        difficulty=question.difficulty,
        category=question.category,
        response_time_ms=response_time_ms,
    )

    # Agent 호출
    response = await agent.score_and_explain(request)

    # DB 저장
    self._save_attempt_answer(session_id, question_id, user_answer, response)

    return response.model_dump()

async def submit_answers(
    self,
    session_id: str,
    answers: list[tuple[str, str]],  # (question_id, user_answer)
) -> dict:
    """Batch scoring using Tool 6 (parallel)"""
    # 여러 답변을 병렬로 채점
    # Return: batch results + round statistics
```

**Task 2-4: 유닛 테스트 작성 (1시간)**

**파일**: `tests/backend/test_question_gen_service_agent.py`

```python
@pytest.mark.asyncio
async def test_generate_questions_calls_agent(db_session):
    """QuestionGenerationService가 Agent를 호출하는지 확인"""
    service = QuestionGenerationService(db_session)

    with patch("src.backend.services.question_gen_service.create_agent") as mock_create:
        mock_agent = AsyncMock()
        mock_create.return_value = mock_agent

        mock_agent.generate_questions.return_value = GenerateQuestionsResponse(
            round_id="r123",
            items=[...],  # 3개 문항
            time_limit_seconds=1200,
        )

        result = await service.generate_questions("survey_123", 1)

        # Assertions
        mock_agent.generate_questions.assert_called_once()
        assert len(result["questions"]) == 3
        assert "session_id" in result

@pytest.mark.asyncio
async def test_generate_questions_saves_to_db(db_session):
    """생성된 문항이 DB에 저장되는지 확인"""
    # ... Agent 호출 후 DB에 Question 레코드 확인
```

**산출물**:

- `src/backend/services/question_gen_service.py` 수정
- `src/backend/services/scoring_service.py` 수정 (선택사항)
- `src/backend/api/questions.py` 검증
- `tests/backend/test_question_gen_service_agent.py` 생성
- `docs/progress/REQ-A-Agent-Backend-{1,2}.md` (Phase 1-4 문서)

---

### Phase 3️⃣: E2E 통합 테스트 (REQ-A-Agent-Integration-1)

**Task 3-1: 통합 테스트 스위트 작성 (1.5시간)**

**파일**: `tests/integration/test_agent_backend_e2e.py`

```python
import pytest
from httpx import AsyncClient
from src.backend.main import app
from src.agent.llm_agent import GenerateQuestionsRequest

class TestAgentBackendIntegration:
    """E2E integration tests: CLI → API → Agent → DB"""

    @pytest.mark.asyncio
    async def test_generate_questions_e2e(self, client: AsyncClient, db_session):
        """API → Service → Agent → DB 전체 흐름"""
        # 1. Survey 생성
        # 2. POST /questions/generate
        # 3. 응답 검증
        # 4. DB 검증
        pass

    @pytest.mark.asyncio
    async def test_score_answer_e2e(self, client: AsyncClient, db_session):
        """단일 답변 채점"""
        pass

    @pytest.mark.asyncio
    async def test_batch_scoring_e2e(self, client: AsyncClient, db_session):
        """배치 채점"""
        pass

    @pytest.mark.asyncio
    async def test_adaptive_questioning_e2e(self, client: AsyncClient, db_session):
        """Round 1 → Round 2 (적응형)"""
        pass
```

**Task 3-2: CLI 기반 E2E 테스트 (30분)**

**파일**: `scripts/test_e2e_cli.sh`

```bash
#!/bin/bash
set -e

echo "🚀 E2E Test: Agent Integration"

# 1. 서버 시작
./tools/dev.sh up &
SERVER_PID=$!
sleep 3

# 2. 문항 생성
./tools/dev.sh cli agent generate-questions \
  --survey-id "e2e_test_$(date +%s)" \
  --round 1

# 3. 답변 채점
./tools/dev.sh cli agent score-answer \
  --round-id "test_round" \
  --item-id "test_item" \
  --user-answer "test answer"

# 4. 정리
kill $SERVER_PID
echo "✅ E2E Test Complete"
```

**Task 3-3: 테스트 실행 및 검증 (30분)**

```bash
# 통합 테스트 실행
pytest tests/integration/test_agent_backend_e2e.py -v

# 모든 테스트 실행
tox -e py311

# 포맷 검사
./tools/dev.sh format
```

**산출물**:

- `tests/integration/test_agent_backend_e2e.py`
- `scripts/test_e2e_cli.sh`
- `docs/progress/REQ-A-Agent-Integration-1.md` (Phase 1-4 문서)

---

## 타임라인 & 진행 추적

### 예상 소요 시간

| Phase | REQ ID | 소요시간 | 난이도 | 상태 |
|-------|--------|---------|--------|------|
| **0** | REQ-A-Agent-Sanity-0 | 30분 | ⭐ | ⏳ Backlog |
| **1** | REQ-CLI-Agent-1 | 20분 | ⭐ | ⏳ Backlog |
| **1** | REQ-CLI-Agent-2 | 40분 | ⭐⭐ | ⏳ Backlog |
| **1** | REQ-CLI-Agent-3 | 30분 | ⭐⭐ | ⏳ Backlog |
| **1** | REQ-CLI-Agent-4 | 30분 | ⭐⭐ | ⏳ Backlog |
| **1** | REQ-CLI-Agent-5 | 1시간 | ⭐⭐⭐ | ⏳ Backlog |
| **2** | REQ-A-Agent-Backend-1 | 1시간 30분 | ⭐⭐⭐ | ⏳ Backlog |
| **2** | REQ-A-Agent-Backend-2 | 1시간 (선택) | ⭐⭐⭐ | ⏳ Backlog |
| **3** | REQ-A-Agent-Integration-1 | 2시간 | ⭐⭐ | ⏳ Backlog |
| | **총계** | **약 8시간** | | |

### 진행 추적 방법

각 REQ 완료 후:

1. **진행 파일 생성**: `docs/progress/REQ-[ID].md`

   ```markdown
   # REQ-A-Agent-Sanity-0: Agent 기본 동작 검증

   ## Phase 1: 명세 (Specification)
   [자동 생성, 이 문서에서 복사]

   ## Phase 2: 테스트 설계
   [테스트 케이스 나열]

   ## Phase 3: 구현
   - [ ] 파일 생성/수정
   - [ ] 테스트 통과
   - [ ] 포맷 검사

   ## Phase 4: 요약
   - Modified: scripts/test_agent_sanity_check.py
   - Tests: ✅ PASS
   - Commit: abc123def456
   ```

2. **Progress 파일 업데이트**: `docs/DEV-PROGRESS.md`

   ```markdown
   | REQ-A-Agent-Sanity-0 | 4 | ✅ Done | Commit: abc123 |
   ```

3. **Git Commit**:

   ```bash
   git add docs/progress/REQ-A-Agent-Sanity-0.md docs/DEV-PROGRESS.md
   git commit -m "feat: REQ-A-Agent-Sanity-0 - Agent 기본 동작 검증

   - 실제 Google Gemini LLM 연결 검증
   - LANGCHAIN_DEBUG로 Tool 호출 추적
   - 문항 3개 이상 생성 확인

   🤖 Generated with Claude Code"
   ```

---

## 다음 단계: 시작하기

**준비**:

1. 이 문서 검토 (지금)
2. 동료 의견 통합 완료 ✅
3. REQ ID 체계 확정 ✅

**개발 시작**:

### Option A: Phase 0부터 순차 진행 (추천)

```bash
# Phase 0
uv run python scripts/test_agent_sanity_check.py

# Phase 1
./tools/dev.sh cli agent --help

# Phase 2
pytest tests/backend/test_question_gen_service_agent.py

# Phase 3
pytest tests/integration/test_agent_backend_e2e.py
```

### Option B: 병렬 진행 (빠름)

- Phase 0, 1, 2를 동시에 진행
- 약 3-4시간 소요

---

## 참고 자료

### 기존 코드 참고

- Agent 구현: `src/agent/llm_agent.py` (910줄)
- Agent 테스트: `tests/agent/test_llm_agent.py` (1290줄)
- CLI 구조: `src/cli/main.py`, `src/cli/actions/`
- BackEnd 서비스: `src/backend/services/`

### 문서

- CLAUDE.md: REQ-Based Workflow 정의
- CLAUDE.md § CLI Feature Requirement Workflow

### 동료 의견 원문

- 동료 A: CLI 구조 확장 (Task 1-1, 1-2, 1-3)
- 동료 B: Agent 검증 우선 (Phase 0, LANGCHAIN_DEBUG)

---

**작성자**: Claude Code
**마지막 수정**: 2025-11-11
**상태**: 👨‍💼 검토 대기 (승인 후 Phase 0 시작 권장)
