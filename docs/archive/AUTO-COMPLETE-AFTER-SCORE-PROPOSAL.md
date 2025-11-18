# Proposal: Auto-Complete Session After Score

**Status**: 📋 **Design Proposal for Review**
**Date**: 2025-11-18
**Proposer**: User
**Scope**: UX Improvement + Data Consistency

---

## 1. 제안 요약

### 현재 플로우

```
questions score → (사용자가 별도로 호출) → questions complete
                ↓
              2 API calls needed
```

### 제안된 플로우

```
questions score → (자동) → questions complete
            ↓
          1 API call (사용자 perspective)
```

**목표**:

- ✅ 사용자 UX 개선 (명시적 complete 호출 제거)
- ✅ 데이터 일관성 보장 (자동)
- ✅ 누락 위험 제거
- ❌ Frontend 요구사항 단순화

---

## 2. 기술적 분석

### 2.1 현재 코드 구조

**CLI에서의 흐름** (`src/cli/actions/questions.py:1471`):

```python
def score_answer(context: CLIContext, *args: str) -> None:
    # 1. Batch score unscored answers
    for answer_data in unscored_answers:
        status_code, response = context.client.make_request(
            "POST",
            "/questions/answer/score",  # API: score individual answer
            json_data={"session_id", "question_id"}
        )

    # 2. Calculate round score
    context.console.print("[dim]Calculating round score...[/dim]")
    calculate_round_score(context, session_id)

    # 3. ❌ MISSING: Auto-complete not called
```

**Backend 엔드포인트** (`src/backend/api/questions.py:640`):

```python
@router.post("/answer/score")
def score_answer(request: ScoringRequest, db: Session):
    """Score a single answer"""
    scoring_service = ScoringService(db)
    result = scoring_service.score_answer(request.session_id, request.question_id)
    return ScoringResponse(**result)

# Separate endpoint for complete
@router.post("/session/{session_id}/complete")
def complete_session(session_id: str, db: Session):
    """Mark session as completed"""
    test_session.status = "completed"
    db.commit()
```

### 2.2 제안된 변경

#### Option A: Backend에서 자동 처리 (권장)

**변경점**: `/questions/score` 엔드포인트 수정

```python
@router.post("/questions/score")
def calculate_round_score(session_id: str, db: Session):
    """
    Calculate round score AND auto-complete session
    """
    # 1. Calculate score (existing logic)
    round_score = calculate_score(session_id, db)

    # 2. Auto-complete: Check if all answers scored
    test_session = db.query(TestSession).filter_by(id=session_id).first()

    # NEW: Auto-complete if all answers are scored
    if all_answers_scored(session_id, db):
        test_session.status = "completed"
        db.commit()
        logger.info(f"Auto-completed session {session_id}")

    return {
        "score": round_score,
        "status": "completed",  # NEW: indicate session status
        "auto_completed": True   # NEW: inform client
    }
```

**장점**:

- ✅ Backend에서 한 번에 처리 (원자성)
- ✅ 사용자/Frontend 관여 없음
- ✅ 데이터 일관성 보장
- ✅ 기존 score API 활용 가능

**단점**:

- ⚠️ API 책임이 늘어남 (점수 계산 + 상태 관리)

---

#### Option B: CLI에서 자동 처리

**변경점**: CLI의 `score_answer()` 함수 수정

```python
def score_answer(context: CLIContext, *args: str) -> None:
    # ... existing batch score logic ...

    # Calculate round score
    calculate_round_score(context, session_id)

    # NEW: Auto-complete after score
    context.console.print("[dim]Completing session...[/dim]")
    status_code, response = context.client.make_request(
        "POST",
        f"/questions/session/{session_id}/complete"
    )

    if status_code == 200:
        context.console.print("[green]✓ Session completed[/green]")
```

**장점**:

- ✅ Backend 변경 최소화
- ✅ 기존 `/session/complete` API 활용
- ✅ 책임 분리 명확

**단점**:

- ⚠️ CLI만 auto-complete (다른 클라이언트는 수동)
- ⚠️ CLI를 우회한 API 호출은 여전히 누락 가능

---

#### Option C: 하이브리드 (최적)

**Backend**: 조건부 auto-complete

```python
@router.post("/questions/score")
def calculate_round_score(
    session_id: str,
    auto_complete: bool = True,  # NEW: configurable flag
    db: Session
):
    # Calculate score
    round_score = calculate_score(session_id)

    # NEW: Auto-complete if flag is True (default)
    if auto_complete and all_answers_scored(session_id):
        test_session.status = "completed"
        db.commit()

    return {"score": round_score, "auto_completed": auto_complete}
```

**CLI**: Auto-complete 호출

```python
def score_answer(context: CLIContext, *args: str) -> None:
    # ... existing logic ...

    # Calculate round score with auto_complete=True
    calculate_round_score(context, session_id, auto_complete=True)
```

**장점**:

- ✅ Backend에서도 자동 처리
- ✅ API 호출자가 제어 가능 (필요시)
- ✅ CLI에서도 명시적으로 처리
- ✅ 모든 시나리오 커버

**단점**:

- ⚠️ 복잡도 약간 증가

---

## 3. 설계 검토

### 3.1 Single Responsibility Principle (SRP)

**현재 설계**:

```
score_answer()     → Score individual answer (SRP ✅)
calculate_round_score() → Calculate total score (SRP ✅)
complete_session()  → Mark session as completed (SRP ✅)
```

**변경 후 (Option A)**:

```
calculate_round_score() → Calculate score + Auto-complete (?SRP)
                    ↑
            책임이 2개로 증가 (위험)
```

**개선 (Option C)**:

```
calculate_round_score()  → Calculate score (primary)
                        → Auto-complete (secondary, configurable)
                        ↑
                책임이 명확 + 선택적
```

### 3.2 데이터 일관성

| 시나리오 | 현재 | Option A | Option B | Option C |
|---------|------|----------|----------|----------|
| 모든 답변 채점됨 | ⚠️ 수동 | ✅ 자동 | ✅ 자동 (CLI만) | ✅ 자동 |
| API 직접 호출 | ⚠️ 누락 | ✅ 자동 | ⚠️ 누락 | ✅ 자동 |
| Partial score | ⚠️ 정의 안 함 | ? | ? | ✅ 설정 가능 |

### 3.3 API 호환성

**Breaking Change 우려**:

```
기존 API 사용자:
  POST /questions/score?session_id=xxx

응답:
  { "score": 85, "correct_count": 17, "total_count": 20 }

변경 후 (Option A):
  { "score": 85, "correct_count": 17, "total_count": 20,
    "status": "completed", "auto_completed": true }

→ Breaking Change 아님 (필드 추가만)
```

---

## 4. 구현 계획

### Phase 1: 조건부 검사 추가 (1시간)

```python
def all_answers_scored(session_id: str, db: Session) -> bool:
    """Check if all questions in session have been scored"""
    unscored = db.query(TestResponse).filter(
        TestResponse.session_id == session_id,
        TestResponse.score.is_(None)
    ).count()
    return unscored == 0
```

### Phase 2: Backend 수정 (1시간)

```python
@router.post("/questions/score")
def calculate_round_score(
    session_id: str,
    auto_complete: bool = True,
    db: Session
):
    # ... existing score calculation ...

    # NEW: Auto-complete if all scored
    if auto_complete and all_answers_scored(session_id, db):
        test_session = db.query(TestSession).filter_by(id=session_id).first()
        test_session.status = "completed"
        db.commit()
        logger.info(f"Auto-completed session {session_id}")

    return {
        "score": round_score,
        "correct_count": ...,
        "total_count": ...,
        "auto_completed": auto_complete
    }
```

### Phase 3: CLI 수정 (30분)

```python
def score_answer(context: CLIContext, *args: str) -> None:
    # ... existing batch score logic ...

    # Calculate round score (auto_complete enabled by default)
    calculate_round_score(context, session_id, auto_complete=True)
```

### Phase 4: 테스트 (2시간)

```python
# New test cases
def test_score_auto_completes_session():
    """Score calculation should auto-complete session"""

def test_score_respects_auto_complete_flag():
    """Should NOT auto-complete if auto_complete=False"""

def test_score_only_completes_if_all_scored():
    """Should only auto-complete when all answers scored"""
```

### Phase 5: Frontend 요구사항 제거 (30분)

```
현재:
  "After score calculation, Frontend must call complete endpoint"

개선:
  "Score calculation automatically completes session"
  (Frontend에서 complete 호출 선택사항으로 변경)
```

---

## 5. 위험도 분석

### 5.1 데이터 무결성 위험 🟡

**위험**: Partial scoring 시 조기 complete

```
예: 3개 문항 중 2개만 채점됨
    → calculate_round_score() 호출
    → all_answers_scored() = False
    → ✅ Complete 안 함 (안전)
```

**완화 방안**:

- ✅ `all_answers_scored()` 엄격한 검사
- ✅ 로그 추적 (auto_complete 여부)
- ✅ 모니터링 (unexpected auto-complete)

### 5.2 API 호환성 위험 🟢

**위험**: 기존 API 사용자 영향

```
응답 형식 변경:
  Before: { "score": 85, "correct_count": 17, "total_count": 20 }
  After:  { "score": 85, "correct_count": 17, "total_count": 20,
            "auto_completed": true }

→ Breaking Change 아님 (하위 호환)
```

### 5.3 비즈니스 로직 위험 🟡

**위험**: Complete가 자동 = 사용자 모름

```
상황: 사용자가 실수로 채점
     → 자동 complete
     → 수정 불가

완화:
  1. CLI에서 명시적 로그 ("Session completed")
  2. Response에 auto_completed flag
  3. 필요시 admin revert API 추가
```

---

## 6. 최종 권장안 ✅

### 선택: **Option C (하이브리드)**

**이유**:

1. ✅ SRP 유지 (auto-complete은 secondary responsibility)
2. ✅ 데이터 일관성 보장
3. ✅ API 유연성 (flag로 제어 가능)
4. ✅ 전체 시나리오 커버
5. ✅ Breaking change 없음

### 구현 일정

| Phase | 작업 | 시간 |
|-------|------|------|
| 1 | 조건부 검사 함수 | 1h |
| 2 | Backend `/questions/score` 수정 | 1h |
| 3 | CLI 자동 호출 | 0.5h |
| 4 | 테스트 작성 | 2h |
| 5 | Frontend 문서 업데이트 | 0.5h |
| **총합** | | **5h** |

---

## 7. Frontend 요구사항 변경

### 변경 전

```
Flow:
  1. questions score (endpoint 호출)
  2. ⚠️ REQUIRED: questions complete (endpoint 호출)
  3. GET /profile/ranking (최종 점수 조회)

문제: 2번이 누락되면 ranking이 부정확
```

### 변경 후

```
Flow:
  1. questions score (endpoint 호출 → 자동 complete 포함)
  2. ✅ OPTIONAL: questions complete (필요 없음, 자동 처리됨)
  3. GET /profile/ranking (최종 점수 조회)

개선: 누락 위험 제거, 데이터 일관성 보장
```

### Frontend 문서 업데이트 항목

```markdown
## Score Calculation

When you call the score endpoint:
```

POST /questions/score?session_id={session_id}

```

The following happens automatically:
1. ✅ All answers are scored using AI (Tool 6)
2. ✅ Round total score is calculated
3. ✅ **Session is automatically completed** (NEW)
   - status changed to "completed"
   - Ready for ranking calculation
4. ✅ Response includes "auto_completed": true

Therefore:
- ✅ You DO NOT need to call `/session/complete` manually
- ✅ Session status is guaranteed to be "completed" after score
- ✅ User can immediately view ranking on profile page
```

---

## 8. 마이그레이션 가이드

### 기존 Frontend 코드 (계속 동작)

```javascript
// Old approach (still works, but redundant)
await api.post('/questions/score', { session_id })
await api.post(`/session/${session_id}/complete`)  // No-op now
```

### 새로운 Frontend 코드 (권장)

```javascript
// New approach (cleaner)
const response = await api.post('/questions/score', { session_id })
console.log(response.auto_completed) // true - session already completed

// Complete is now optional (if needed for any reason)
if (response.auto_completed) {
  console.log('Session automatically completed')
}
```

---

## 9. 체크리스트

### 구현 전

- [ ] Backend 팀 리뷰
- [ ] Frontend 팀 동의 (요구사항 변경)
- [ ] Test 계획 수립

### 구현 중

- [ ] all_answers_scored() 구현 + 테스트
- [ ] /questions/score 수정 + 테스트
- [ ] CLI score_answer() 수정
- [ ] 통합 테스트
- [ ] 문서 업데이트

### 구현 후

- [ ] 모니터링 (auto_complete 성공률)
- [ ] 운영팀 교육 (새로운 플로우)
- [ ] Frontend 배포 (요구사항 제거)
- [ ] 기존 코드 정리 (redundant complete 호출)

---

## 결론

✅ **Option C 권장**:

- **구현 난이도**: 낮음 (5시간)
- **위험도**: 낮음 (하위 호환, 조건부 처리)
- **효과**: 높음 (UX 개선, 데이터 일관성)
- **의존성**: 없음 (독립적 개선)

이 변경으로:

1. ✅ 사용자가 complete를 호출하지 않아도 된다
2. ✅ CLI 테스트 시 누락 위험 제거
3. ✅ 데이터 일관성 자동 보장
4. ✅ Frontend 요구사항 단순화

**Ready to implement?** 👍
