# REQ-B-B2-Retake 사양서: 재응시 문항 생성

**Created**: 2025-11-18
**Status**: ⏳ Pending Review
**Priority**: M (Medium)

---

## 1. 요구사항 개요

### 1.1 문제점 분석

현재 시스템의 문제:

```
사용자가 Round 1을 완료한 후:

1. POST /questions/score → 채점 완료
2. POST /questions/session/{id}/complete → 세션 상태 = 'completed'

이 상태에서 재응시 시도:

3. POST /questions/generate-adaptive 호출
   └─ generate_questions_adaptive()에서:
      └─ prev_result = query(TestResult)
            .filter(..., TestResult.round == 0)  # Round 0 결과 찾기
            └─ ❌ No previous answers found
            └─ ❌ ValueError: "Round 0 results not found"
```

### 1.2 근본 원인

- `generate_questions_adaptive()`는 **이전 라운드의 TestResult 레코드가 존재해야만** 작동
- 재응시는 **동일 라운드를 다시 응시**하는 것이므로, "이전 라운드" 결과가 존재하지 않음
- 현재 로직에서는 `generate_questions_adaptive()` 만 있어서, 일반 Round 1 재응시를 처리할 수 없음

### 1.3 해결 방향

**핵심 원칙**: 재응시 = **새로운 TestSession 생성** (이전 세션과 독립적)

```
현재 API:
- POST /questions/generate          → Round 1 신규 응시 (새 세션 생성)
- POST /questions/generate-adaptive → Round 2+ (이전 라운드 결과 필수)

재응시 (Round 1 다시):
- POST /questions/generate 동일하게 사용 가능!
- 왜? 이미 새 TestSession을 생성하므로, completed 상태 무관

재응시 (Round 1 → Round 2 적응형):
- POST /questions/generate-adaptive 사용
- previous_session_id = Round 1 completed 세션 ID
```

---

## 2. 요구사항 명세

### 2.1 Backend (REQ-B-B2-Retake-1~4)

| REQ ID | 요구사항 | 구현 위치 | 기술 스택 |
|--------|---------|---------|---------|
| **REQ-B-B2-Retake-1** | 재응시 시 `POST /questions/generate` 동일하게 사용 | `src/backend/api/questions.py:295-341` | FastAPI |
| **REQ-B-B2-Retake-2** | 매번 새 TestSession 생성 (completed 무관) | `src/backend/services/question_gen_service.py:250-434` | SQLAlchemy |
| **REQ-B-B2-Retake-3** | Round 2+ 적응형: `POST /questions/generate-adaptive` 사용 | `src/backend/services/question_gen_service.py:502-664` | FastAPI |
| **REQ-B-B2-Retake-4** | 프론트엔드: 이전 정보 자동 로드 | `frontend/pages/retake.tsx` | React |

### 2.2 Frontend (REQ-F-B5-Retake-1~5)

| REQ ID | 요구사항 | 구현 위치 | 기술 스택 |
|--------|---------|---------|---------|
| **REQ-F-B5-Retake-1** | "재응시" 플로우: 이전 정보 로드 → 폼 미리 채우기 → 테스트 시작 | Frontend components | React |
| **REQ-F-B5-Retake-2** | 자기평가 수정 → `PUT /profile/survey` → 새 survey_id 획득 | Form handling | React/Axios |
| **REQ-F-B5-Retake-3** | 오류 처리 및 재시도 | Error boundaries | React |
| **REQ-F-B5-Retake-4** | Round 2 적응형: `previous_session_id` 정확히 전달 | API calls | Axios |
| **REQ-F-B5-Retake-5** | (선택) 확인 모달 표시 | Modal component | React |

---

## 3. 시스템 설계

### 3.1 재응시 플로우 (재응시 - 동일 라운드)

```
┌─────────────────────────────────────┐
│  사용자: 대시보드 "재응시" 버튼     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Frontend: 모달 확인                │
│  "레벨 테스트를 재응시하시겠습니까?"│
└────────┬────────────────────────────┘
         │ 확인 클릭
         ▼
┌─────────────────────────────────────┐
│  GET /profile/history               │
│  - 이전 응시 데이터 조회            │
│  - 최신 자기평가 정보 로드          │
└────────┬────────────────────────────┘
         │ 200 OK
         ▼
┌─────────────────────────────────────┐
│  Frontend: 자기평가 폼 표시         │
│  - 이전 정보 미리 채우기            │
│  - 수정 옵션 제공                   │
└────────┬────────────────────────────┘
         │ 사용자 입력/확인
         ▼
┌─────────────────────────────────────┐
│  (선택) PUT /profile/survey         │
│  - 수정한 자기평가 저장             │
│  - 새 survey_id 획득                │
└────────┬────────────────────────────┘
         │ 201 Created
         ▼
┌─────────────────────────────────────┐
│  POST /questions/generate           │
│  Body: {                            │
│    "survey_id": "...",              │
│    "round": 1                       │
│  }                                  │
└────────┬────────────────────────────┘
         │ Backend 처리
         ▼
┌─────────────────────────────────────┐
│  Backend:                           │
│  1. TestSession 생성                │
│     - id: UUID                      │
│     - user_id                       │
│     - survey_id                     │
│     - round: 1                      │
│     - status: 'in_progress'         │
│  2. Real Agent로 문항 생성          │
│  3. Question 레코드 저장            │
└────────┬────────────────────────────┘
         │ 201 Created
         ▼
┌─────────────────────────────────────┐
│  Response: {                        │
│    "session_id": "new-uuid",        │
│    "questions": [{...}, {...}],     │
│    "attempt": 1                     │
│  }                                  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Frontend: 테스트 화면 시작         │
│  - 새 session_id로 진행             │
│  - 이전 응시와 독립적               │
└─────────────────────────────────────┘
```

### 3.2 적응형 Round 2 플로우 (Round 1 완료 → Round 2 시작)

```
┌──────────────────────────────────────┐
│  Round 1 완료 + 점수 계산 완료      │
│  (status = 'completed')             │
└────────┬──────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  POST /questions/generate-adaptive   │
│  Body: {                             │
│    "previous_session_id": "r1-uuid", │
│    "round": 2                        │
│  }                                   │
└────────┬──────────────────────────────┘
         │ Backend 처리
         ▼
┌──────────────────────────────────────┐
│  Backend:                            │
│  1. Round 1 TestResult 조회 (by id) │
│  2. 난이도 조정 로직 실행            │
│  3. 새로운 TestSession 생성 (R2)    │
│  4. Real Agent로 적응형 문항 생성   │
│  5. Question 저장                   │
└────────┬──────────────────────────────┘
         │ 201 Created
         ▼
┌──────────────────────────────────────┐
│  Response: {                         │
│    "session_id": "new-r2-uuid",     │
│    "questions": [{...}, {...}],     │
│    "adaptive_params": {...}         │
│  }                                   │
└────────┬──────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  Frontend: Round 2 테스트 화면      │
└──────────────────────────────────────┘
```

---

## 4. 구현 체크리스트

### 4.1 Backend (이미 구현됨 - 확인만)

- [x] `generate_questions()` - 새 TestSession 생성 로직 (완료)
  - 위치: `src/backend/services/question_gen_service.py:250-434`
  - 동작: 매번 새 UUID로 TestSession 생성, completed 상태 무관

- [x] `generate_questions_adaptive()` - Round 2+ 로직 (완료)
  - 위치: `src/backend/services/question_gen_service.py:502-664`
  - 동작: previous_session_id로 Round 1 결과 분석, 난이도 조정

- [x] API 엔드포인트 (완료)
  - `POST /questions/generate` - 재응시 가능
  - `POST /questions/generate-adaptive` - Round 2+ 적응형

### 4.2 Frontend (구현 필요)

**파일**: `src/frontend/pages/retake.tsx` (신규 생성) 또는 기존 페이지 수정

**구현 항목**:

1. **재응시 모달/페이지 구성**
   - [ ] "레벨 테스트를 재응시하시겠습니까?" 확인 모달
   - [ ] 자기평가 폼 미리 채우기 로직
   - [ ] "테스트 시작" 버튼

2. **API 호출**
   - [ ] `GET /profile/history` - 이전 응시 데이터 조회
   - [ ] `PUT /profile/survey` (선택) - 자기평가 수정 시
   - [ ] `POST /questions/generate` - 새 문항 생성
   - [ ] Error handling & retry

3. **에러 처리**
   - [ ] 네트워크 오류 시 재시도 버튼
   - [ ] Timeout 처리
   - [ ] 사용자 친화적 에러 메시지

---

## 5. 데이터 흐름 (DB 관점)

### 5.1 Round 1 신규 응시

```
POST /questions/generate (survey_id, round=1)
  ↓
INSERT test_sessions (
  id: UUID,
  user_id: 1,
  survey_id: "survey-123",
  round: 1,
  status: 'in_progress',
  created_at: NOW()
)
  ↓
INSERT test_questions (multiple)
  ↓
... 테스트 진행 ...
  ↓
POST /questions/score
  ↓
INSERT attempt_answers
UPDATE test_sessions (status='completed')
INSERT test_results
```

### 5.2 Round 1 재응시

```
POST /questions/generate (survey_id, round=1)  ← 재응시도 동일 엔드포인트!
  ↓
INSERT test_sessions (  ← 새 UUID
  id: "new-uuid-xyz",
  user_id: 1,
  survey_id: "survey-123",  ← 기존 또는 새로 생성한 ID
  round: 1,
  status: 'in_progress',
  created_at: NOW()
)
  ↓
INSERT test_questions (새로운 문항들)
  ↓
... 테스트 진행 ...
  ↓
POST /questions/score
  ↓
INSERT attempt_answers
UPDATE test_sessions (status='completed')
INSERT test_results
```

### 5.3 Round 2 적응형 진행

```
POST /questions/generate-adaptive (previous_session_id="r1-uuid", round=2)
  ↓
SELECT test_result FROM test_results
  WHERE session_id='r1-uuid' AND round=1
  ↓
분석: 난이도 조정, 약점 카테고리 파악
  ↓
INSERT test_sessions (
  id: "new-r2-uuid",
  user_id: 1,
  survey_id: (Round 1과 동일),
  round: 2,
  status: 'in_progress'
)
  ↓
INSERT test_questions (적응형 문항들)
```

---

## 6. 인수 기준 (Acceptance Criteria)

### 6.1 Backend 인수 기준

| # | 기준 | 검증 방법 |
|---|------|---------|
| 1 | Round 1 완료 후 재응시 시 새 session_id를 획득한다. | `POST /questions/generate` → 응답에 새 session_id 포함 |
| 2 | 새로 생성된 세션의 status는 'in_progress'이다. | DB: SELECT status FROM test_sessions WHERE id='new-uuid' → 'in_progress' |
| 3 | 이전 세션(completed)은 변경되지 않는다. | DB: 이전 세션 status = 'completed' (유지) |
| 4 | Round 1 적응형 진행 시 `previous_session_id` 정확히 처리 | `POST /questions/generate-adaptive` → Round 1 결과 분석 → Round 2 문항 생성 |
| 5 | 새로운 문항들이 DB에 저장된다. | DB: SELECT COUNT(*) FROM test_questions WHERE session_id='new-uuid' → 5 |

### 6.2 Frontend 인수 기준

| # | 기준 | 검증 방법 |
|---|------|---------|
| 1 | "재응시" 버튼 클릭 → 자기평가 폼 표시 | UI: 폼에 이전 정보가 미리 채워짐 |
| 2 | 자기평가 수정 후 "테스트 시작" → 새 session_id 획득 | API 호출: `POST /questions/generate` → 새 session_id 반환 |
| 3 | 새로운 세션으로 테스트 화면 진입 | UI: session_id 변경 + 새 문항 표시 |
| 4 | 오류 발생 시 재시도 버튼 제공 | UI: "다시 시도" 버튼 클릭 → API 재호출 |
| 5 | Round 2 적응형: `previous_session_id` 정확히 전달 | API 호출: `POST /questions/generate-adaptive` Body 확인 |

---

## 7. 예시 시나리오

### 시나리오: 사용자 "bwyoon"의 재응시

**초기 상태**:

- Round 1 완료: session_id = "session-r1-uuid-001", status = 'completed'
- Test Result: score = 60, round = 1
- 자기평가: survey_id = "survey-001", interests = ["AI", "RAG"]

**사용자 액션**:

1. 대시보드 "재응시" 버튼 클릭
2. 모달 확인: "레벨 테스트를 재응시하시겠습니까?"
3. 자기평가 폼 표시:

   ```
   Level: Advanced (이전과 동일)
   Career: 8 years (이전과 동일)
   Interests: ["AI", "RAG", "Robotics"] (수정: Robotics 추가)
   ```

4. "테스트 시작" 클릭

**Backend 처리**:

1. (선택) PUT /profile/survey 호출 → 새 survey_id = "survey-002" 생성
2. POST /questions/generate 호출

   ```json
   {
     "survey_id": "survey-002",
     "round": 1,
     "domain": "AI"
   }
   ```

3. 새 TestSession 생성:

   ```
   id: "session-r1-uuid-002"
   user_id: 1
   survey_id: "survey-002"
   round: 1
   status: 'in_progress'
   ```

4. Real Agent로 새 문항 5개 생성
5. Test Questions 저장

**Response**:

```json
{
  "session_id": "session-r1-uuid-002",
  "questions": [
    {"id": "q-001", "stem": "...", ...},
    {"id": "q-002", "stem": "...", ...},
    ...
  ],
  "attempt": 1
}
```

**결과**:

- 이전 session: "session-r1-uuid-001", status = 'completed' (유지)
- 새 session: "session-r1-uuid-002", status = 'in_progress'
- 새로운 자기평가: "survey-002" (이전과 별도)
- 테스트 화면: 새 session_id로 시작

---

## 8. 검토 요청 항목

### 8.1 Backend 담당자 검토

- [ ] `generate_questions()` 로직이 재응시 케이스를 올바르게 처리하는가?
- [ ] 매번 새로운 UUID를 생성하여 기존 세션과 독립성을 보장하는가?
- [ ] DB 트랜잭션 처리가 안전한가?
- [ ] 오류 처리 및 재시도 로직이 적절한가?

### 8.2 Frontend 담당자 검토

- [ ] 자기평가 폼 UI는 재응시 케이스에 맞게 설계되었는가?
- [ ] API 호출 순서 및 에러 핸들링이 명확한가?
- [ ] 사용자 경험은 직관적인가?

### 8.3 QA 담당자 검토

- [ ] 테스트 시나리오가 포괄적인가?
- [ ] 엣지 케이스(timeout, 네트워크 오류 등)가 처리되는가?

---

## 다음 단계

검토 완료 후:

1. **Phase 2**: 테스트 설계 (TDD)
   - `tests/backend/test_question_gen_service_retake.py` 생성
   - 5개 테스트 케이스: Happy path, 에러, 엣지 케이스

2. **Phase 3**: 구현
   - Frontend: 재응시 플로우 구현
   - Backend: (이미 구현됨 - 확인만)

3. **Phase 4**: 최종 검증 및 커밋
   - Progress 파일 생성
   - Git commit
