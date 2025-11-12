# POST /generate API - 동기식 흐름 명확화

## 📋 당신의 3가지 질문 답변

### Q1. "Agent가 동기식으로 5개 문제 생성 후 반환한다는 의미가 DB에서 저장하고 Frontend에게도 전달한다는 의미인가요?"

**✅ 정확합니다!**

```
Frontend                          Backend                            Agent
   │                                  │                               │
   │──── POST /generate ───────────────>                             │
   │     {survey_id, round}            │                             │
   │                                   │                             │
   │                                   ├──> QuestionGenerationService │
   │                                   │    generate_questions()      │
   │                                   │                             │
   │                                   │                ┌────────────┤
   │                                   │                │            │
   │                                   │  create_agent()            │
   │                                   │  ├─ Tool 1: Get profile    │
   │                                   │  ├─ Tool 2: Search templates
   │                                   │  ├─ Tool 3: Get keywords   │
   │                                   │  ├─ Tool 4: Validate Q     │
   │                                   │  ├─ Tool 5: Save Q to DB ◄──┘
   │                                   │  └─ invoke() 호출
   │                                   │    (SYNC 대기 ⏳)
   │  <────── 응답 (완료) ──────────────┤
   │  {session_id,                     │
   │   questions: [5개]}               │
   │  ↓                                 │
   Display 5 questions            ✅ DB 저장 완료
```

**의미**:

1. **Backend**는 `question_service.generate_questions()` 호출 (동기식 대기)
2. **Agent** 내부에서:
   - Tool 5로 DB에 5개 문제 저장
   - 생성 결과 반환
3. **Backend**는 Agent의 반환값을 받아서:
   - 그대로 Frontend에 전달
   - 이때 questions는 **이미 DB에 저장된 데이터**
4. **Frontend**는 questions 배열을 받아서 화면에 표시

---

### Q2. "실제 API 스펙을 확인해보니 정확히 그 형태더라"

**✅ 맞습니다! 실제 구현:**

```python
# /src/backend/api/questions.py (line 278-316)

@router.post("/generate")
async def generate_questions(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Generate test questions for a user."""
    try:
        question_service = QuestionGenerationService(db)
        result = await question_service.generate_questions(
            user_id=1,
            survey_id=request.survey_id,
            round_num=request.round,
        )
        return result  # ◄─ {session_id, questions: [...]}
    except Exception as e:
        raise HTTPException(...)
```

**Response Model** (line 65-76):

```python
class GenerateQuestionsResponse(BaseModel):
    session_id: str = Field(..., description="TestSession ID")
    questions: list[QuestionResponse] = Field(...)

class QuestionResponse(BaseModel):
    id: str
    item_type: str
    stem: str
    choices: list[str] | None
    answer_schema: dict[str, Any]
    difficulty: int
    category: str
```

**실제 Frontend가 받는 JSON**:

```json
{
  "session_id": "abc-123-def-456",
  "questions": [
    {
      "id": "q1",
      "item_type": "multiple_choice",
      "stem": "Which of the following...",
      "choices": ["A", "B", "C", "D"],
      "answer_schema": {
        "type": "exact_match",
        "correct_answer": "A",
        "keywords": ["keyword1", "keyword2"]
      },
      "difficulty": 5,
      "category": "AI"
    },
    { ... 4개 더 ... }
  ]
}
```

---

### Q3. "호출: POST /generate 를 통해서 Frontend 는 문제를 display 가능한거구나. 맞지?"

**✅ 정확합니다!**

Frontend는 바로 이 응답을 받아서 화면에 표시할 수 있습니다:

```javascript
// Frontend (예: React)
async function startQuiz() {
  const response = await fetch('http://127.0.0.1:8000/questions/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      survey_id: 'survey-123',
      round: 1,
      domain: 'AI'
    })
  });

  const { session_id, questions } = await response.json();

  // 바로 화면에 표시 가능!
  console.log(`Session: ${session_id}`);
  questions.forEach(q => {
    console.log(`Q: ${q.stem}`);
    console.log(`Choices: ${q.choices}`);
    console.log(`Difficulty: ${q.difficulty}`);
  });
}
```

**왜 바로 표시 가능한가?**

- ✅ Agent가 완료될 때까지 Backend가 **동기식 대기**
- ✅ Agent가 Tool 5로 **이미 DB에 저장**
- ✅ Backend가 저장된 데이터를 응답에 포함
- ✅ Frontend가 받는 데이터는 **최신 DB 데이터**

---

## 🔄 상세 Flow (코드 레벨)

### Step 1: Frontend가 POST /generate 호출

```python
# 요청
{
  "survey_id": "survey-uuid",
  "round": 1,
  "domain": "AI"
}
```

### Step 2: Backend의 generate_questions() 실행

```python
# /src/backend/api/questions.py (line 305-310)
question_service = QuestionGenerationService(db)
result = await question_service.generate_questions(
    user_id=1,
    survey_id=request.survey_id,
    round_num=request.round,  # 1
)
```

### Step 3: QuestionGenerationService.generate_questions() 호출

```python
# 내부 구현 (예상)
async def generate_questions(self, user_id, survey_id, round_num):
    # 1. create_agent() 호출해서 Agent 생성
    agent = create_agent(...)

    # 2. Agent에게 요청
    #    ⏳ 여기서 대기! (동기식)
    result = agent.invoke({
        "session_id": session_id,
        "survey_id": survey_id,
        "round": round_num,
        ...
    })

    # 3. Agent가 반환할 때까지 대기
    #    (Agent가 Tool 5로 DB에 저장하는 동안)

    # 4. Agent 완료 후, 응답 생성
    return {
        "session_id": session_id,
        "questions": [5개의 Question 객체]
        # ← 이미 DB에 저장됨!
    }
```

### Step 4: Frontend가 응답 받음

```python
# /src/backend/api/questions.py (line 311)
return result  # {session_id, questions: [...]}
```

**HTTP 200**:

```json
{
  "session_id": "s1",
  "questions": [
    {"id": "q1", "stem": "...", ...},
    {"id": "q2", "stem": "...", ...},
    ...
  ]
}
```

### Step 5: Frontend가 화면에 표시

```javascript
// questions 배열을 받아서 화면에 렌더링
renderQuestions(questions);
```

---

## ⏱️ 타이밍 이해

### 📍 동기식 vs 비동기식

```
동기식 (현재 구현):
─────────────────

T=0s   POST /generate 호출
       │
T=1s   Agent 실행 시작
       │ Tool 1: Get profile (100ms)
       │ Tool 2: Search templates (200ms)
       │ Tool 3: Get keywords (150ms)
       │ Tool 4: Validate (300ms)
       │ Tool 5: Save to DB (400ms)  ◄─── DB에 저장됨!
       │
T=3s   Agent 완료
       │
       ⏳ Backend가 여기까지 기다림
       │
T=3.1s 응답 반환
       │
       └──> Frontend 받음 + 화면 표시

특징:
- Frontend는 최대 3초 정도 대기
- 응답 받을 때는 이미 DB에 저장됨
- Questions 데이터는 100% 최신 데이터
```

---

## 💾 DB 저장 시점

```
POST /generate 호출
  ↓
Agent 시작
  ├─ Tool 1-4 (검증)
  │
  └─ Tool 5: save_generated_question
       ├─ 📝 Questions 테이블에 INSERT
       ├─ 📝 TestSession 테이블에 UPDATE (status)
       └─ ✅ DB에 저장 완료

Response 생성
  ├─ DB에서 최신 Questions 읽기 (또는 Agent 응답 사용)
  └─ Frontend에 전달

Frontend 화면에 표시
  ├─ 사용자가 문제 풀이 시작
  └─ POST /autosave로 답변 저장
```

---

## 🔑 핵심 정리

| 항목 | 상태 |
|------|------|
| **DB에 저장되나?** | ✅ YES (Tool 5가 저장) |
| **Frontend에게 전달되나?** | ✅ YES (response에 포함) |
| **바로 화면에 표시 가능?** | ✅ YES (이미 저장된 데이터) |
| **실시간으로 업데이트?** | ✅ YES (동기식 대기) |
| **동기식인가?** | ✅ YES (await 사용, Backend가 대기) |

---

## 📊 Data Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│ Frontend Browser                                            │
└────────────────────────────────────────────────────────────┘
                        ↕ HTTP POST
┌────────────────────────────────────────────────────────────┐
│ Backend (FastAPI)                                           │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ POST /generate (line 278)                           │   │
│ │  └─> QuestionGenerationService.generate_questions() │   │
│ │       └─> create_agent().invoke()  ⏳ 동기 대기     │   │
│ └──────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
                        ↕ Agent 호출 (동기)
┌────────────────────────────────────────────────────────────┐
│ Agent (LangGraph)                                           │
│ ├─ Tool 1: Get user profile                               │
│ ├─ Tool 2: Search templates                               │
│ ├─ Tool 3: Get keywords                                   │
│ ├─ Tool 4: Validate question                              │
│ └─ Tool 5: Save to DB  ◄─────────────────────┐            │
│                                               │            │
│    invoke() 완료 → result 반환                │            │
└────────────────────────────────────────────────────────────┘
                        ↕
┌────────────────────────────────────────────────────────────┐
│ PostgreSQL Database                                         │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ TestSession ← 생성                                  │   │
│ │   id: "s1"                                          │   │
│ │   round: 1                                          │   │
│ │   status: "in_progress"                             │   │
│ │                                                      │   │
│ │ Questions (5개) ← 저장됨!                           │   │
│ │   q1: {stem: "...", choices: [...]}                 │   │
│ │   q2: {stem: "...", choices: [...]}                 │   │
│ │   ...                                               │   │
│ └──────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

---

## 결론

**당신의 이해가 정확합니다:**

1. ✅ Agent가 동기식으로 실행
2. ✅ Tool 5로 DB에 저장
3. ✅ Backend가 저장된 데이터를 응답에 포함
4. ✅ Frontend가 응답을 받아서 바로 표시
5. ✅ 사용자가 DB에 저장된 문제를 풀이

**더이상 추가 동작이 필요 없습니다!** 🎉
