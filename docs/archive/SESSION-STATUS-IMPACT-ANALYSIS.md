# TestSession Status Management: Impact Analysis

**Date**: 2025-11-18
**Context**: CLI 테스트 중 `questions complete` 호출 누락 시나리오 분석

---

## 1. 현재 상황 분석

### 발생한 상황

```
Round 1:
  ✓ questions generate --count 3     (O)
  ✓ questions solve                   (O)
  ✓ questions score                   (O)
  ✗ questions complete                (MISSED!)  ← status still "in_progress"

Round 2:
  ✓ questions generate adaptive --count 4  (O)
  ✓ questions solve                        (O)
  ✓ questions score                        (O)
  ✓ questions complete                     (O)  ← status = "completed"
```

### 데이터베이스 상태

| Round | Session ID | Status | 영향 |
|-------|-----------|--------|------|
| 1 | session_1 | **in_progress** | ⚠️ 문제 발생 가능 |
| 2 | session_2 | **completed** | ✅ 정상 |

---

## 2. 기술적 영향 분석

### 2.1 Session Status가 미치는 영향

**TestSession 모델** (`src/backend/models/test_session.py`):

```python
status: Mapped[str] = Enum("in_progress", "completed", "paused")
```

**핵심 특징**:

- Round별로 독립적인 session 생성
- Round 1, Round 2는 별도의 session_id를 가짐
- 각 Round는 독립적으로 complete 가능

---

### 2.2 영향받는 서비스들

#### A. AutosaveService (가장 큰 영향)

**파일**: `src/backend/services/autosave_service.py`

```python
if test_session.status == "completed":
    raise ValueError(f"Session {session_id} is already completed")
```

**문제점**:

- ✅ `in_progress` → 계속 답변 저장 가능 (정상)
- ✅ `completed` → 추가 답변 저장 불가 (보호 작동)

**Round 1의 경우**:

```
status = "in_progress" (MISSED questions complete)
  ↓
사용자가 실수로 다시 답변을 시도하면
  ↓
답변 저장이 계속 가능 (의도하지 않은 동작)
```

---

#### B. RankingService (가장 심각한 영향) ⚠️

**파일**: `src/backend/services/ranking_service.py`

```python
.filter(
    and_(
        TestSession.user_id == user_id,
        TestSession.status == "completed",  # ← 이 조건이 핵심!
    )
)
```

**문제점**:

- Ranking 계산 시 `status == "completed"` 세션만 포함
- Round 1 (status = "in_progress") **제외됨**

**결과**:

```
시나리오: 사용자가 Round 1, Round 2 모두 완료

기대 동작:
  - 최종 점수 = (Round 1 점수 + Round 2 점수) / 2
  - 랭킹 = 두 라운드 모두 포함

실제 동작 (questions complete 누락 시):
  - 최종 점수 = Round 2 점수만 포함 ← ❌ WRONG
  - 랭킹 = Round 2만 포함 ← ❌ WRONG

결과: 사용자 순위가 부정확함 (잘못 높을 가능성)
```

---

#### C. QuestionGenerationService

**영향**: 없음 ✅

- Round 2 생성 시 Round 1의 status는 확인하지 않음
- 새로운 세션이 생성되므로 무관

---

### 2.3 각 기능별 영향도 매트릭스

| 기능 | 영향도 | 심각도 | 설명 |
|------|--------|--------|------|
| 추가 답변 저장 | 중간 | 보통 | 사용자 실수로 다시 답변 가능 |
| **최종 점수 계산** | **높음** | **높음** | Round 1 점수 제외됨 |
| **사용자 랭킹** | **높음** | **높음** | 부정확한 순위 계산 |
| 통계 분석 | 높음 | 보통 | Round별 통계에서 누락 |
| 학습 기록 (History) | 낮음 | 낮음 | 개별 문항 기록은 유지됨 |

---

## 3. 운영상 문제점

### 문제 1: 부정확한 최종 랭킹 📊

```
예시 상황:
  Alice: Round 1 점수 80점, Round 2 점수 70점
  Bob:   Round 1 점수 70점, Round 2 점수 90점

기대 결과:
  Alice 최종 = 75점 (평균), 순위 2위
  Bob   최종 = 80점 (평균), 순위 1위

실제 결과 (Round 1 missing):
  Alice 최종 = 70점 (Round 2만), 순위 2위
  Bob   최종 = 90점 (Round 2만), 순위 1위

→ 점수 차이가 부정확해짐 (부정적인 평가 가능성)
```

### 문제 2: 데이터 일관성 부족 ⚠️

```
test_sessions 테이블:
  - Round 1: status = "in_progress" (고아 상태)
  - Round 2: status = "completed"

test_responses 테이블:
  - Round 1의 모든 답변은 저장됨
  - 하지만 Round 1 session status ≠ "completed"

→ "모든 답변을 했는데 session은 in_progress"라는 모순
```

### 문제 3: 기능 검증 불가

```
GET /profile/ranking
  ↓
"Round 1 score = 0?" 이상한 결과 발생
  ↓
사용자 민원 발생
  ↓
운영팀 디버깅 어려움
```

---

## 4. 실제 영향 범위

### 영향받는 기능

**🔴 직접 영향 (높음)**:

1. ✗ 최종 점수 계산 → Round 1 점수 제외
2. ✗ 사용자 랭킹 → 부정확
3. ✗ 프로필 통계 (category별 점수) → 불완전

**🟡 간접 영향 (중간)**:

1. ✓ 추가 답변 저장 → 데이터 오염 가능
2. ✓ 학습 기록 조회 → 부분적으로 정상 (개별 기록은 있음)

**🟢 무영향 (낮음)**:

1. ✓ Round 2 생성 → 정상
2. ✓ 채점 → 정상 (이미 저장된 데이터 기반)
3. ✓ 문항 조회 → 정상

---

## 5. 프로덕션 환경에서의 위험도

### 현재 시스템 설계

**긍정적 측면**:

```
✅ Round 1, 2는 독립적 session ID
✅ complete 호출 전에 ranking 조회 방지 가능
✅ Frontend 통제로 missing complete 방지 가능
```

**부정적 측면**:

```
❌ Backend 검증 부족 (Round 1 답변 후 status 자동 업데이트 없음)
❌ 데이터 일관성 검사 없음
❌ 모니터링/알림 기능 없음
```

---

## 6. 해결 방안

### 단계별 개선안

#### Phase 1: 즉시 (CLI 테스트)

```
✓ questions complete 호출 필수 (현재 상태)
✓ API 문서에 명시
```

#### Phase 2: 단기 (1-2주)

```python
# AutosaveService: 마지막 답변 저장 시 자동 complete 검토
if is_last_answer(session_id):
    # Round 1, 2 모두 완료 가능
    test_session.status = "completed"
```

#### Phase 3: 중기 (1개월)

```python
# Session Status Validator (신규 서비스)
class SessionStatusValidator:
    def validate(self, session_id):
        """
        데이터 일관성 검사:
        1. status = "in_progress" && questions answered >= question_count
           → WARNING: 자동 complete 추천
        2. status = "completed" && questions answered < question_count
           → ERROR: 데이터 불일치
        """
```

#### Phase 4: 장기 (2개월)

```
- Monitoring Dashboard 추가
- Metrics: completed_ratio, avg_time_to_complete, etc.
- Alert: "incomplete sessions > threshold"
```

---

## 7. 임시 방안 (지금 바로)

### 1. API 엔드포인트 추가 (검증용)

```python
@router.get("/session/{session_id}/validate")
def validate_session(session_id: str, db: Session):
    """
    Session 데이터 일관성 검사
    - Returns: { valid: bool, issues: [...], recommendation: "complete?" }
    """
    test_session = db.query(TestSession).filter_by(id=session_id).first()
    responses = db.query(TestResponse).filter_by(session_id=session_id).count()

    if responses > 0 and test_session.status != "completed":
        return {
            "valid": False,
            "issue": "Session answered but not completed",
            "recommendation": "Call questions complete",
            "answered_count": responses
        }
```

### 2. CLI 개선

```bash
# 현재:
questions complete

# 개선된 버전:
questions complete --force  # 검증 후 강제 완료
questions validate          # 상태 확인 (새 명령어)
```

---

## 8. 결론

### 요약

| 항목 | 평가 |
|------|------|
| **현재 Frontend 사용 시** | ✅ 문제 없음 |
| **CLI 테스트 누락 시** | ⚠️ 부정확한 최종 점수 계산 |
| **프로덕션 영향** | ⚠️ 중간 (Frontend 통제 가정) |
| **권장 대응** | 🔧 Phase 2-3 개선 필요 |

### 핵심 포인트

```
Q: 운영상 어떤 문제가 있을까?

A: 1. 최종 점수 부정확 (Round 1 제외됨)
   2. 사용자 랭킹 부정확 (20-30% 차이 가능)
   3. 데이터 일관성 문제 (모순된 상태 가능)

그러나:
   ✅ Frontend 통제 시 방지 가능
   ✅ 개별 문항 기록은 완전함
   ✅ 돌이킬 수 없는 손실은 아님 (재계산 가능)
```

### 우선순위

```
필수 (지금): questions complete 호출 필수 (CLI 테스트)
권장 (1주): API 검증 엔드포인트 추가
개선 (1개월): Session Status Validator 구현
최적화 (2개월): Monitoring & Alerting 추가
```

---

## 부록: 관련 코드 위치

| 파일 | 줄번 | 설명 |
|------|------|------|
| `src/backend/models/test_session.py` | 59-63 | Status enum 정의 |
| `src/backend/api/questions.py` | 680-739 | complete_session 엔드포인트 |
| `src/backend/services/autosave_service.py` | - | status 검증 |
| `src/backend/services/ranking_service.py` | - | "completed" 필터링 |
| `src/cli/actions/questions.py` | - | CLI questions complete 구현 |

---

**최종 평가**: ⚠️ **주의 필요하나, Frontend 사용 시 큰 문제 없음**
