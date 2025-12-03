# Adaptive Question Generation Algorithm (Concept Guide)

**문서 목적**: Questions Generate Adaptive 의 동작 원리를 이해하기 위한 개념 설명서

**대상**: Backend 개발자, QA, Product Manager

---

## 📌 1. 개요 (Overview)

### 1.1 What is Adaptive Generation?

"적응형 문제 생성"은 사용자의 **Round 1 성과에 따라** Round 2의 문제 난이도와 주제를 **자동으로 조정**하는 기능입니다.

```
Round 1: 사용자가 5개 문제 풀이 → 점수 계산 (60점)
           ↓
AdaptiveDifficultyService: 60점 분석 → 약점 카테고리 파악
           ↓
Round 2: 약점 부분을 더 많이 출제 + 난이도 조정
```

### 1.2 Key Features

✅ **자동 난이도 조정** - Round 1 점수에 따라 Round 2 난이도 결정
✅ **약점 카테고리 강화** - 틀린 분야를 더 많이 출제
✅ **LLM 기반 생성** - Agent가 프롬프트를 받아 적응형 문제 생성
✅ **데이터 기반** - TestResult에서 실제 점수와 약점 분석

---

## 📊 2. 난이도 조정 알고리즘 (Difficulty Adjustment)

### 2.1 Score Tier Mapping

Round 1 점수에 따라 **3가지 티어**로 분류됩니다:

| 점수 범위 | 티어 | 의미 | Round 2 난이도 |
|---------|------|------|---|
| **0~40%** | `low` | 많이 어려움 | **낮춤** (난이도 -1) |
| **40~70%** | `medium` | 중간 수준 | **유지/소폭 올림** (난이도 +0.5) |
| **70~100%** | `high` | 잘함 | **올림** (난이도 +2) |

### 2.2 Difficulty Calculation Formula

```
Round 2 조정 난이도 = Round 1 평균난이도 + 조정값

조정값:
- Low Tier (0~40%):    -1.0  → 더 쉬운 문제로 기초 강화
- Medium Tier (40~70%): +0.5  → 약간 더 어려운 문제로 단계 상승
- High Tier (70~100%):  +2.0  → 훨씬 더 어려운 문제로 심화 학습

범위: 난이도는 1~10 사이로 고정 (min=1, max=10)
```

### 2.3 예시 시나리오

#### 시나리오 A: 점수 50점 (Low Tier)

```
Round 1 성과:
  - 점수: 50점
  - 평균 난이도: 5.0 (중간 수준 문제)
  - 틀린 문제: AI 카테고리 2개, RAG 카테고리 1개

적응형 조정:
  1. 점수 50점 → Low Tier 판정
  2. 난이도 조정: 5.0 - 1.0 = 4.0
  3. 결과: Round 2는 난이도 4.0 (더 쉬운) 문제 출제

사용자 경험:
  ✓ 기초 개념을 다시 확인하기 쉬운 문제
  ✓ 자신감 회복 가능
  ✓ 점차 난이도를 높여갈 수 있는 기회
```

#### 시나리오 B: 점수 60점 (Medium Tier)

```
Round 1 성과:
  - 점수: 60점
  - 평균 난이도: 5.0
  - 틀린 문제: LLM 카테고리 2개

적응형 조정:
  1. 점수 60점 → Medium Tier 판정
  2. 난이도 조정: 5.0 + 0.5 = 5.5
  3. 결과: Round 2는 난이도 5.5 (약간 더 어려운) 문제 출제

사용자 경험:
  ✓ 점진적인 난이도 상승으로 학습 곡선 최적화
  ✓ LLM 약점 부분을 더 깊이 있게 학습
```

#### 시나리오 C: 점수 85점 (High Tier)

```
Round 1 성과:
  - 점수: 85점
  - 평균 난이도: 6.0
  - 틀린 문제: Semantic Search 카테고리 1개

적응형 조정:
  1. 점수 85점 → High Tier 판정
  2. 난이도 조정: 6.0 + 2.0 = 8.0
  3. 결과: Round 2는 난이도 8.0 (매우 어려운) 문제 출제

사용자 경험:
  ✓ 심화 학습으로 전문 역량 개발
  ✓ 약점(Semantic Search) 부분 집중 학습
```

---

## 🎯 3. 약점 카테고리 우선순위 (Weak Category Prioritization)

### 3.1 개념

Round 1에서 틀린 카테고리를 **Round 2에서 더 많이 출제**합니다.

```
REQ: REQ-B-B2-Adapt-3 (약점 카테고리 ≥50%)

Round 2 문제 중 **최소 50% 이상**을 약점 카테고리에서 출제해야 합니다.
```

### 3.2 카테고리 할당 규칙

**Round 2 총 5개 문제 기준:**

```
weak_categories = {
  "AI": 2개 틀림,
  "RAG": 1개 틀림
}

계산:
  1. 약점 카테고리 최소 문제 수: max(3, (5+1)//2) = 3개 (60%)
  2. 일반 카테고리: 5 - 3 = 2개 (40%)

할당:
  - AI (약점): 3개
  - RAG (약점): 0개 (AI에서 3개 할당)
  - 기타 카테고리 (강점): 2개
```

### 3.3 할당 알고리즘 상세

```python
weak_categories = {"AI": 2, "RAG": 1}  # 틀린 개수
total_questions = 5

# Step 1: 약점 카테고리 최소 문제 수 계산
min_weak_questions = max(3, (5 + 1) // 2)  # = 3개 (≥50%)

# Step 2: 약점 카테고리에 공평하게 분배
weak_cats_count = 2  # AI, RAG
remaining = 3

for cat in ["AI", "RAG"]:
    cats_left = 2
    questions_for_cat = 3 // 2  # = 1
    allocation[cat] = 1
    remaining = 3 - 1 = 2

    cats_left = 1
    questions_for_cat = 2 // 1  # = 2
    allocation[cat] = 2
    remaining = 0

결과: {"AI": 1, "RAG": 2} (총 3개)
나머지 2개: 강점/일반 카테고리
```

### 3.4 예시

#### Case 1: 약점 1개 (AI 카테고리)

```
Round 1 결과:
  - 틀린 문제: AI (2개)
  - 맞은 문제: RAG (3개)

적응형 할당:
  - AI (약점): 3개 이상
  - RAG (강점): 2개 이하

Round 2 문제 구성:
  1. AI - 기초 개념 문제
  2. AI - 심화 문제
  3. AI - 고급 응용 문제
  4. RAG - 강점 유지 문제
  5. 기타 - 통합 문제
```

#### Case 2: 약점 2개 (AI, LLM)

```
Round 1 결과:
  - 틀린 문제: AI (1개), LLM (2개)
  - 맞은 문제: RAG (2개)

적응형 할당:
  - AI (약점): 2개
  - LLM (약점): 1개
  - RAG (강점): 2개

Round 2 문제 구성:
  1. AI - 약점 보완
  2. LLM - 약점 보완
  3. LLM - 심화 학습
  4. RAG - 강점 유지
  5. 기타 - 통합 평가
```

---

## 🤖 4. LLM Agent Prompting (LLM 프롬프트)

### 4.1 Agent가 받는 입력 정보

```python
# QuestionGenerationService.generate_questions_adaptive()에서

agent_request = GenerateQuestionsRequest(
    session_id=new_session_id,      # Round 2 세션 ID
    survey_id=prev_session.survey_id,  # 같은 설문
    round_idx=2,                    # Round 2
    prev_answers=[                  # ← 이전 라운드 정보
        {
            "question_id": "q1-uuid",
            "category": "AI",
            "difficulty": 5,
            "item_type": "multiple_choice"
        },
        # ... 5개 다 포함
    ],
    question_count=5,
    question_types=None,  # Agent가 선택
    domain="AI",  # 가장 약한 카테고리
)
```

### 4.2 Agent가 생성하는 LLM Prompt

```
[LLM에게 전달되는 프롬프트]

Generate high-quality exam questions for the following survey.

Session ID: 517db006-...
Survey ID: survey_001
Round: 2
Domain: AI  ← 약점 카테고리
Previous Answers:
  - Question 1 (AI, difficulty=5, multiple_choice)
  - Question 2 (AI, difficulty=5, multiple_choice)
  - Question 3 (LLM, difficulty=5, multiple_choice)
  - ...

Question Count: 5
Question Types: multiple_choice, true_false, short_answer

Generate 5 questions with:
1. Adjusted difficulty based on score
2. Focus on weak areas (AI category)
3. Appropriate for Round 2 (after Round 1 experience)
```

### 4.3 Agent의 생성 전략

| 상황 | Agent 동작 | LLM 프롬프트 키워드 |
|------|----------|---------|
| **Low Tier (50점)** | 기초 강화 + 약점 반복 | "simpler concepts", "review fundamentals", "build confidence" |
| **Medium Tier (60점)** | 점진적 심화 + 약점 보완 | "intermediate difficulty", "extend understanding", "bridge concepts" |
| **High Tier (85점)** | 심화 학습 + 약점 정밀화 | "advanced applications", "edge cases", "deep expertise" |

### 4.4 구체적 LLM 프롬프트 예시

#### 시나리오: 50점 (Low Tier) + AI 약점

```
Previous Performance:
- Score: 50/100 (Low Tier)
- Correct: 2/5
- Weak Areas: AI (2 errors)

Generate Round 2 questions:
1. Difficulty: DECREASE (4.0 instead of 5.0)
   → "Create simpler, foundational AI concepts"

2. Focus on AI (weak category)
   → "Generate 3+ questions about AI basics
      - Question 1: Basic definition & terminology
      - Question 2: Core concepts with examples
      - Question 3: Common misconceptions"

3. Supportive tone
   → "Frame questions to build confidence and understanding"

4. Answer schema
   → "Use exact_match for definitional questions
      → Use keyword_match for conceptual understanding"

Generate EXACTLY 5 questions.
```

#### 시나리오: 85점 (High Tier) + Semantic Search 약점

```
Previous Performance:
- Score: 85/100 (High Tier)
- Correct: 4/5
- Weak Areas: Semantic Search (1 error)

Generate Round 2 questions:
1. Difficulty: INCREASE (7.0 instead of 6.0)
   → "Create advanced, specialized RAG topics"

2. Focus on Semantic Search (weak area)
   → "Generate 3+ questions about:
      - Embedding space analysis
      - Vector similarity metrics
      - Real-world RAG optimization
      - Edge cases in semantic search"

3. Expert-level tone
   → "Frame questions for professional growth
      → Include practical scenarios"

4. Answer schema
   → "Use semantic_match for nuanced understanding
      → Use keyword_match for precise technical terms"

Generate EXACTLY 5 questions with advanced rigor.
```

---

## 🔄 5. 실행 흐름 (Execution Flow)

### 5.1 전체 시퀀스 다이어그램

```
Round 1 완료
    ↓
POST /questions/score
    ↓ (Score + Auto-Complete)
[DB 저장] TestResult(score=60)
TestSession(status="completed")
    ↓
사용자가 Round 2 시작 요청
    ↓
POST /generate-adaptive
    ├─ session_id: Round 1 session_id
    └─ round_num: 2
    ↓
QuestionGenerationService.generate_questions_adaptive()
    ├─ 1️⃣ Round 1 결과 조회
    │    └─ TestResult(score=60) ← DB에서 로드
    │
    ├─ 2️⃣ 적응형 파라미터 계산
    │    └─ AdaptiveDifficultyService.get_adaptive_generation_params()
    │       ├─ difficulty_tier: "low" (60점)
    │       ├─ adjusted_difficulty: 4.0 (5.0 - 1.0)
    │       ├─ weak_categories: {"AI": 2}
    │       └─ priority_ratio: {"AI": 3} (≥50%)
    │
    ├─ 3️⃣ 이전 답변 정보 조회
    │    └─ _get_previous_answers()
    │       └─ [{q_id, category, difficulty, item_type}, ...]
    │
    ├─ 4️⃣ LLM Agent 호출
    │    └─ agent.generate_questions(
    │         domain="AI",
    │         prev_answers=[...],
    │         difficulty=4.0,
    │         question_count=5
    │       )
    │
    ├─ 5️⃣ Agent가 LLM 프롬프트 생성 및 호출
    │    └─ "Generate 5 AI questions, difficulty 4.0,
    │         considering user's weakness in AI..."
    │
    ├─ 6️⃣ LLM이 5개 문제 생성
    │    └─ [GeneratedItem, GeneratedItem, ...]
    │
    ├─ 7️⃣ 생성된 문제를 DB에 저장
    │    └─ Question(session_id, item_type, difficulty, ...)
    │
    └─ 8️⃣ 응답 반환
         └─ {
              "session_id": new_session_id,
              "questions": [...],
              "adaptive_params": {
                "adjusted_difficulty": 4.0,
                "weak_categories": {"AI": 2},
                "priority_ratio": {"AI": 3}
              }
            }
```

### 5.2 코드 레벨 구현

```python
# src/backend/services/question_gen_service.py

async def generate_questions_adaptive(
    user_id: int,
    session_id: str,  # Round 1 session_id
    round_num: int = 2,
    question_count: int = 5,
) -> dict[str, Any]:

    # Step 1: Round 1 결과 조회
    prev_result = db.query(TestResult).filter(
        TestSession.user_id == user_id,
        TestResult.round == 1
    ).first()

    # Step 2: 적응형 파라미터 계산
    adaptive_service = AdaptiveDifficultyService(db)
    params = adaptive_service.get_adaptive_generation_params(
        prev_result.session_id
    )
    # params = {
    #   "adjusted_difficulty": 4.0,
    #   "weak_categories": {"AI": 2},
    #   "priority_ratio": {"AI": 3}
    # }

    # Step 3: 약점 카테고리 추출
    weak_categories = list(params["priority_ratio"].keys())
    domain = weak_categories[0]  # "AI"

    # Step 4: 이전 답변 정보
    prev_answers = self._get_previous_answers(user_id, round_num - 1)

    # Step 5: Agent에게 전달할 요청 생성
    agent_request = GenerateQuestionsRequest(
        session_id=new_session_id,
        survey_id=prev_session.survey_id,
        round_idx=round_num,
        prev_answers=prev_answers,  # ← 중요: 이전 정보 포함
        question_count=question_count,
        domain=domain,  # ← 중요: 약점 카테고리
    )

    # Step 6: LLM Agent 호출
    agent = await create_agent()
    agent_response = await agent.generate_questions(agent_request)
    # Agent 내부에서 LLM이 호출되고
    # 5개의 GeneratedItem 반환

    # Step 7: DB 저장
    for item in agent_response.items:
        question = Question(
            id=uuid4(),
            session_id=new_session_id,
            item_type=item.type,  # "multiple_choice"
            difficulty=item.difficulty,  # LLM이 설정
            category=item.category,  # "AI"
            # ...
        )
        db.add(question)

    db.commit()

    # Step 8: 응답 반환
    return {
        "session_id": new_session_id,
        "questions": [...],
        "adaptive_params": params  # ← 클라이언트도 볼 수 있음
    }
```

---

## 🧪 6. 테스트 케이스 (Test Cases)

### 6.1 Low Tier 검증

```python
# 시나리오: 50점(Low Tier) → 난이도 감소

def test_low_score_decreases_difficulty():
    # Given: Round 1 score = 50
    test_result = TestResult(score=50, round=1)

    # When: Adaptive generation
    adaptive = AdaptiveDifficultyService(db)
    adjusted = adaptive.calculate_round2_difficulty(
        round1_avg_difficulty=5.0,
        score=50
    )

    # Then: Difficulty decreased
    assert adjusted == 4.0  # 5.0 - 1.0
```

### 6.2 High Tier 검증

```python
# 시나리오: 85점(High Tier) → 난이도 증가

def test_high_score_increases_difficulty():
    # Given: Round 1 score = 85
    test_result = TestResult(score=85, round=1)

    # When: Adaptive generation
    adaptive = AdaptiveDifficultyService(db)
    adjusted = adaptive.calculate_round2_difficulty(
        round1_avg_difficulty=5.0,
        score=85
    )

    # Then: Difficulty increased
    assert adjusted == 7.0  # 5.0 + 2.0
```

### 6.3 약점 카테고리 할당 검증

```python
# 시나리오: 약점 2개 → ≥50% 할당

def test_weak_category_allocation():
    # Given: weak_categories = {"AI": 2, "RAG": 1}
    wrong_cats = {"AI": 2, "RAG": 1}

    # When: Calculate allocation
    adaptive = AdaptiveDifficultyService(db)
    allocation = adaptive.get_category_priority_ratio(
        wrong_categories=wrong_cats,
        total_questions=5
    )

    # Then: ≥50% from weak categories
    weak_total = sum(allocation.values())
    assert weak_total >= 3  # 60% of 5
```

---

## 📋 7. API 명세

### 7.1 Request

```bash
POST /generate-adaptive

Query Parameters:
  session_id: str  # Round 1 session_id
  round_num: int = 2  # Target round (default 2)
  count: int = 5  # Question count (default 5)
```

### 7.2 Response

```json
{
  "session_id": "abc123-uuid",
  "questions": [
    {
      "id": "q1-uuid",
      "item_type": "multiple_choice",
      "stem": "AI의 정의는?",
      "choices": ["A", "B", "C", "D"],
      "answer_schema": {"correct_key": "A"},
      "difficulty": 4,
      "category": "AI"
    },
    // ... 4개 더
  ],
  "adaptive_params": {
    "difficulty_tier": "low",
    "adjusted_difficulty": 4.0,
    "weak_categories": {"AI": 2},
    "priority_ratio": {"AI": 3},
    "score": 50,
    "correct_count": 2,
    "total_count": 5
  }
}
```

---

## 🔍 8. 자주 묻는 질문 (FAQ)

### Q1: Round 1이 70점이면 Round 2는 무조건 더 어려운 문제?

**A**: 예, High Tier(70점 이상)로 분류되어 난이도가 +2 증가합니다.

- Round 1 평균 난이도 5.0 → Round 2 난이도 7.0 목표

### Q2: 약점 카테고리가 없으면 어떻게 되나?

**A**: 모든 카테고리에서 균형잡힌 문제를 생성합니다.

```python
if not wrong_categories:
    priority_ratio = {}  # 공평한 분배
```

### Q3: `prev_answers`는 LLM이 꼭 봐야 하나?

**A**: 네, 중요합니다. LLM이 사용자의 이전 경험을 알아야

- 비슷한 난이도의 문제인지
- 같은 카테고리 반복인지
- 개념 이해도는 어느 정도인지
판단할 수 있습니다.

### Q4: 난이도 1~10 스케일이 문제마다 다르면?

**A**: 현재는 구현상 Simple Average를 사용합니다.

```python
round1_avg_difficulty = 5.0  # Default
# 실무에서는 실제 Round 1 문제의 평균값 사용
```

### Q5: Agent가 약점 카테고리를 무시하고 다른 카테고리로 출제하면?

**A**: Validation 후 재생성합니다.

- Question Validation (Tool 4) 에서 `category` 검증
- 약점 카테고리 조건 안 맞으면 점수 낮음
- Agent는 점수가 높아지도록 재시도

---

## 🎓 9. 요약 (Summary)

| 항목 | 설명 |
|------|------|
| **목적** | 사용자의 성과에 맞춰 Round 2 난이도와 주제를 자동 조정 |
| **난이도 조정** | 점수에 따라 -1.0 ~ +2.0 범위로 조정 |
| **약점 카테고리** | Round 2 문제의 ≥50%를 약점 분야에서 출제 |
| **LLM 역할** | Agent가 적응형 파라미터를 받아 맞춤형 문제 생성 |
| **이전 정보 활용** | `prev_answers`로 사용자 이력 맥락 제공 |
| **검증** | Question Validation으로 출제 조건 검증 |

---

## 📚 추가 참고

- `src/backend/services/adaptive_difficulty_service.py` - 난이도 조정 로직
- `src/backend/services/question_gen_service.py` - 적응형 생성 구현
- `src/agent/llm_agent.py` - LLM Agent 프롬프트 생성
- `tests/backend/test_adaptive_*.py` - 테스트 케이스

---

**작성일**: 2025-11-18
**버전**: 1.0
**상태**: 완성
