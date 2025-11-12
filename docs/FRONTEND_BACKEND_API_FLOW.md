# Frontend-Backend API 통신 플로우

## 📋 당신의 시나리오 검토 결과

### ✅ 맞는 부분

1. Frontend → Backend API로 agent 실행 요청 ✓
2. Backend가 Agent 실행 ✓
3. Agent: Tool 1로 사용자 프로필 확인 ✓
4. Agent: 문제 생성 및 DB 저장 ✓
5. Backend: DB에서 문제 N개 읽어서 Frontend 전달 ✓

### ❌ 수정이 필요한 부분

#### 1. "Agent가 Backend에 알림" (X)

- **현재**: POST /generate는 **동기식** 호출
- **의미**: Agent가 문제를 생성 완료할 때까지 기다림 → 완료되면 바로 응답
- **결과**: Backend가 명시적으로 다시 알림받을 필요 없음

```python
# Backend 코드 (현재 구현)
def generate_questions(request):
    # 1. Agent 호출 (동기식 대기)
    agent_result = create_agent().invoke(request)

    # 2. Agent 완료되면 바로 다음 줄 실행
    # 3. DB에서 문제 읽어서 반환
    return {
        "session_id": session_id,
        "questions": questions  # 이미 DB에 저장됨
    }
```

#### 2. 채점 방식은 **Hybrid** (선택 가능)

- **모두 풀고 1번 제출** OR **1문제마다 N번 제출** 모두 가능

```
방식 1: 실시간 채점 (선택)
  - 1문제 풀 때마다: POST /autosave → POST /answer/score
  - 장점: 사용자 즉시 피드백
  - Frontend: 각 문제마다 2개 API 호출

방식 2: 일괄 채점 (권장)
  - 1문제 풀 때마다: POST /autosave (저장만)
  - 모두 풀고: POST /score (라운드 완료, 일괄 채점)
  - 장점: 네트워크 요청 감소, Backend 부하 분산
  - Frontend: 마지막에만 POST /score 호출
```

#### 3. prev_answers는 "조회"가 아니라 "포함"

- **의미**: Round 2 생성 시 Round 1 결과를 **Agent 프롬프트에 포함**
- **목적**: Agent가 Round 1 약점을 고려해서 Round 2 난이도 조정
- **Flow**:

  ```
  Round 1 완료 (POST /score)
    ↓ TestResult 생성
    ↓ (correct_count=3, wrong_categories={AI: 2})
    ↓
  Round 2 시작 (POST /generate-adaptive)
    ↓ Backend가 Round 1 TestResult 조회
    ↓ Agent 프롬프트에 포함: "이전 라운드 AI 문제 2개 틀림"
    ↓
  Agent: AI 난이도 조정해서 문제 생성
  ```

---

## 🎯 Frontend 담당자에게 알려줄 API 사용 순서

### ROUND 1: 문제 풀이

```
📍 시점 1: 사용자가 "문제풀이 시작" 버튼 클릭
┗━ 호출: POST /generate
   ├─ 요청: {survey_id, round: 1, domain: "AI"}
   └─ 응답: {session_id, questions: [...]}
   └─ DB: TestSession + 5 Questions 자동 생성
   └─ 역할: Agent가 동기식으로 5개 문제 생성 후 반환

📍 시점 2: 사용자가 문제 1 풀고 답변 입력 완료
┗━ 호출: POST /autosave
   ├─ 요청: {session_id, question_id, user_answer, response_time_ms}
   └─ 응답: {saved_at}
   └─ DB: AttemptAnswer (user_answer만 저장)

📍 시점 3: 사용자가 모든 5개 문제 풀이 완료
┗━ 호출: POST /score
   ├─ 요청: {session_id}
   └─ 응답: {total_score, correct_count, wrong_categories}
   └─ DB: TestResult 생성 + TestSession.status = "completed"
   └─ 역할: Round 1 채점 완료, Round 2 적응형 난이도 결정

📍 선택 사항: 각 문제를 풀고 즉시 피드백 원할 때
┗━ 호출: POST /answer/score (시점 2.5 - 선택)
   ├─ 요청: {session_id, question_id}
   └─ 응답: {is_correct, score, explanation}
   └─ DB: AttemptAnswer (is_correct, score 업데이트)
   └─ 주의: autosave 이후에 호출 필요
```

### ROUND 2: 적응형 문제 풀이

```
📍 시점 4: Frontend가 Round 2 시작 버튼 클릭
┗━ 호출: POST /generate-adaptive
   ├─ 요청: {previous_session_id: "s1"}
   ├─ 응답: {session_id: "s2", questions: [...]}
   ├─ DB: TestSession (new, round=2) + 5 Questions (adaptive)
   ├─ 역할:
   │  - Backend가 TestResult(round=1) 조회
   │  - Agent에게 Round 1 약점 전달
   │  - Agent: 적응형 난이도로 5개 문제 생성
   └─ prev_answers 포함: [Round 1의 틀린 문제들 정보]

📍 시점 5-6: Round 1과 동일 (POST /autosave → POST /score)
┗━ 위의 "시점 2-3" 반복 (다만 session_id는 s2)

📍 시점 7: 최종 기록 저장 (자동)
┗━ Backend 자동: Attempt + AttemptRounds 생성
   ├─ final_grade 계산
   ├─ rank 계산 (다른 사용자와 비교)
   └─ 완료
```

---

## 📊 시간별 API 호출 시나리오

### 추천: 일괄 채점 방식 (Backend 부하 최소)

```
T=0s   | User: "문제풀이 시작" 클릭
       └─→ API #1: POST /generate
       ←─ {session_id, 5 questions}

T=30s  | User: 문제 1 풀이 완료 (답변 입력)
       └─→ API #2: POST /autosave (Q1)
       ←─ {saved_at}

T=60s  | User: 문제 2 풀이 완료
       └─→ API #3: POST /autosave (Q2)
       ←─ {saved_at}

T=90s  | User: 문제 3 풀이 완료
       └─→ API #4: POST /autosave (Q3)
       ←─ {saved_at}

T=120s | User: 문제 4 풀이 완료
       └─→ API #5: POST /autosave (Q4)
       ←─ {saved_at}

T=150s | User: 문제 5 풀이 완료 (마지막)
       └─→ API #6: POST /autosave (Q5)
       ←─ {saved_at}

       └─→ API #7: POST /score (라운드 완료)
       ←─ {total_score: 80, correct_count: 4, wrong_categories: {AI: 1}}
       ← TestResult 생성 + Round 2 난이도 결정

T=160s | User: "Round 2 시작" 클릭 (또는 자동 진행)
       └─→ API #8: POST /generate-adaptive
       ←─ {session_id: "s2", 5 adaptive questions}

... (Round 2 반복)
```

**총 API 호출: 8개 (Round 1: 7개 + Round 2 시작: 1개)**

---

### 선택: 실시간 채점 방식 (피드백 우선)

```
T=0s   | POST /generate → {session_id, 5 questions}

T=30s  | POST /autosave (Q1) + POST /answer/score (Q1)
       ← {saved_at} + {is_correct, score}

T=60s  | POST /autosave (Q2) + POST /answer/score (Q2)
       ← {saved_at} + {is_correct, score}

... (각 문제마다 2개 API)

T=150s | POST /autosave (Q5) + POST /answer/score (Q5)
       ← {saved_at} + {is_correct, score}

       └─→ POST /score (라운드 완료)
       ←─ {total_score, correct_count, wrong_categories}

... (Round 2 반복)
```

**총 API 호출: 12개 (Round 1: 11개 + Round 2 시작: 1개)**

---

## 🔍 prev_answers의 정확한 의미

### ❌ 틀린 이해
>
> "이전 라운드 답변을 조회해야 한다"

### ✅ 정확한 의미
>
> "이전 라운드의 결과 정보를 Agent 프롬프트에 포함해서 다음 라운드 난이도 조정에 사용"

### 구체적 예시

**Round 1 결과**:

```json
TestResult(round=1) = {
  "total_score": 60,
  "correct_count": 3,
  "wrong_categories": {
    "AI": 2,
    "ML": 0
  }
}
```

**Agent가 받는 프롬프트** (Round 2 생성 시):

```
"Previous Round Performance:
- Round 1 Score: 60/100
- Correct: 3/5
- Weak Areas: AI (2 errors)

Generate Round 2 questions:
- Increase difficulty in ML (already strong)
- FOCUS: AI category (weakness area)
- Difficulty Level: Intermediate-Advanced (based on 60% score)"
```

**Agent의 동작**:

- AI 문제: 더 쉬운 난이도 (취약 부분 강화)
- ML 문제: 더 어려운 난이도 (이미 잘함)
- 전체: 적응형 난이도 (60점 → 70점 목표)

---

## ✅ 최종 정리: 당신의 이해 검증

| 항목 | 당신의 생각 | 실제 구현 | 비고 |
|------|----------|---------|------|
| Frontend → Backend API | ✓ Backend API | ✓ POST /generate | 맞음 |
| Agent 실행 방식 | Backend 호출 | 동기식 (동기 대기) | 맞음 |
| Tool 1 프로필 확인 | ✓ | ✓ | 맞음 |
| 문제 생성 및 DB 저장 | ✓ | ✓ Agent 내부 | 맞음 |
| Agent가 Backend에 알림 | ? 필요한가 | 불필요 (동기식) | **수정** |
| 1문제씩 vs 모두 풀고 제출 | 혼란 | **둘 다 가능** (Hybrid) | **선택** |
| prev_answers 조회 | 조회 필요? | 프롬프트에 포함 | **용어 명확화** |

---

## 🎓 Frontend 담당자에게 전달할 메시지

```
안녕하세요!

SLEA-SSEM의 Frontend-Backend API 통신 플로우를 정리했습니다.

## 핵심 3가지:

1️⃣ API 호출 순서 (Round 1)
   ① POST /generate → session_id + 문제 5개 받기
   ② POST /autosave (5번) → 각 문제 답변 저장
   ③ POST /score → 라운드 완료 + 채점

2️⃣ 채점 방식 선택 (두 가지 모두 가능)

   방식 A (권장): 일괄 채점
   - autosave로 저장만 하고
   - 마지막에 /score로 일괄 채점
   - 네트워크 효율적

   방식 B: 실시간 채점
   - 각 문제마다 /answer/score로 즉시 채점
   - 사용자에게 즉각 피드백 가능
   - 네트워크 요청 2배

3️⃣ Round 2 (적응형)
   - POST /generate-adaptive로 Round 1 난이도 고려한 문제 받기
   - Round 1과 동일 절차 반복

자세한 내용은 첨부 문서를 참고해주세요.
```

---

## 📁 문서 네비게이션

당신의 이해를 위해:

- **이 문서**: Frontend-Backend 통신 플로우 (정확한 API 순서)
- `DB_QUICK_REFERENCE.md`: DB 구조 (5분 참고)
- `DB_STRUCTURE_AND_FLOW.md`: 상세 분석 (30분 깊이 있는 이해)
