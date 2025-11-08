# REQ-A-Mode1-Tool1: Get User Profile

**작성일**: 2025-11-08
**개발자**: Claude Code
**상태**: Phase 1 (Specification)

---

## 📋 Phase 1: SPECIFICATION

### 1.1 요구사항 분석

**REQ ID**: REQ-A-Mode1-Tool1
**기능명**: Get User Profile (사용자 프로필 조회 도구)
**우선순위**: **M** (Must)
**MVP**: 1.0

#### 목적

LangChain @tool로 등록되어 Agent가 호출할 수 있는 도구.
사용자의 자기평가 정보를 데이터베이스에서 조회하여 문항 생성 시 난이도 조정에 사용.

#### 사용 시나리오

```
Agent: "사용자 user_123의 프로필을 조회해"
Tool 1 호출
↓
DB 쿼리: UserProfileSurvey.user_id = user_123의 최신 레코드
↓
응답: {
    "user_id": "user_123",
    "self_level": "intermediate",
    "years_experience": 3,
    "job_role": "Backend Engineer",
    "duty": "FastAPI 개발",
    "interests": ["LLM", "RAG"],
    "previous_score": 72
}
```

---

### 1.2 입출력 명세

#### 입력 (Input)

```python
user_id: str  # 사용자 ID (UUID 형식)
```

**검증 규칙**:

- `user_id`: 필수, UUID 형식 문자열
- 빈 문자열 거부
- 유효하지 않은 UUID 형식 거부

#### 출력 (Output - Success)

```python
{
    "user_id": str,                    # 조회한 사용자 ID
    "self_level": str,                 # "beginner" | "intermediate" | "advanced"
    "years_experience": int,           # 0~60 범위
    "job_role": str,                   # 직급/직책 (최대 100자)
    "duty": str,                       # 주요 업무 (최대 500자)
    "interests": list[str],            # ["LLM", "RAG", ...] (최대 20개)
    "previous_score": int              # 0~100 범위 (이전 시험 점수)
}
```

#### 출력 (Output - Error/Fallback)

사용자를 찾을 수 없을 때 기본값 반환:

```python
{
    "user_id": user_id,                # 요청한 user_id 그대로
    "self_level": "beginner",          # 기본값
    "years_experience": 0,             # 기본값
    "job_role": "Unknown",             # 기본값
    "duty": "Not specified",           # 기본값
    "interests": [],                   # 기본값
    "previous_score": 0                # 기본값
}
```

---

### 1.3 구현 위치 & 구조

#### 파일 위치

```
src/agent/tools/
├── __init__.py
└── user_profile_tool.py  (새 파일)
```

#### 함수 시그니처

```python
from langchain_core.tools import tool

@tool
def get_user_profile(user_id: str) -> dict:
    """Get user's self-assessment profile information.

    REQ: REQ-A-Mode1-Tool1

    Args:
        user_id: User ID (UUID)

    Returns:
        dict: User profile with self_level, experience, interests, previous_score
    """
    # 구현
```

#### 의존성

- `sqlalchemy.orm.Session` - DB 접근
- `src.backend.database.get_db` - DB 세션 팩토리
- `src.backend.models.user_profile.UserProfileSurvey` - 사용자 프로필 모델
- `src.backend.models.user.User` - 사용자 모델 (선택)

---

### 1.4 에러 처리

#### 시나리오 1: 사용자 없음

```
입력: user_id = "nonexistent-uuid"
↓
DB 쿼리 결과: None
↓
행동: 기본값 반환 (fallback)
↓
출력: { "user_id": "nonexistent-uuid", "self_level": "beginner", ... }
```

#### 시나리오 2: 유효하지 않은 UUID

```
입력: user_id = "invalid-format"
↓
검증 실패
↓
행동: ValueError 발생 → Agent가 처리
↓
출력: 에러 메시지
```

#### 시나리오 3: DB 연결 실패

```
입력: user_id = "valid-uuid"
↓
DB 쿼리 실패
↓
행동: 재시도 3회 (Agent 자동) → 기본값 반환
↓
출력: 기본값
```

#### 시나리오 4: 프로필 부분 누락

```
입력: user_id = "valid-uuid"
↓
DB 쿼리 성공, 하지만 interest가 NULL
↓
행동: 기본값으로 채우기
↓
출력: { ..., "interests": [] }
```

---

### 1.5 Backend 연동

#### 쿼리 로직

```python
# 최신 프로필 조회 (submitted_at 기준 내림차순)
latest_profile = db.query(UserProfileSurvey) \
    .filter(UserProfileSurvey.user_id == user_id) \
    .order_by(UserProfileSurvey.submitted_at.desc()) \
    .first()
```

#### 데이터 매핑

```python
UserProfileSurvey
├─ id (UUID)
├─ user_id (FK to User)
├─ self_level (str: "beginner"|"intermediate"|"advanced")
├─ years_experience (int)
├─ job_role (str)
├─ duty (str)
├─ interests (JSON array)
└─ submitted_at (datetime)

# 추가로 필요한 데이터:
# - previous_score: User 테이블 또는 TestResult 테이블에서 조회
```

---

### 1.6 성능 & 제약사항

#### 성능

- **DB 쿼리**: O(1) (user_id + submitted_at DESC index 사용)
- **응답 시간**: < 100ms (로컬), < 500ms (원격)
- **캐싱**: 불필요 (Agent 호출당 최신 데이터 필요)

#### 제약사항

- Tool 입력은 **user_id만** (권한 검사는 Agent에서 처리)
- 프로필이 없으면 기본값 반환 (예외 발생 X)
- 반환 데이터는 최신 프로필 1개만 (이력 X)

---

### 1.7 Acceptance Criteria

#### AC1: 유효한 사용자 프로필 조회

```gherkin
Given 사용자 프로필이 DB에 저장되어 있음
When get_user_profile("valid-user-id")가 호출됨
Then 다음 필드를 포함한 dict가 반환됨:
  - user_id = "valid-user-id"
  - self_level in ["beginner", "intermediate", "advanced"]
  - years_experience >= 0
  - job_role = 저장된 값
  - duty = 저장된 값
  - interests = 저장된 리스트 (or [])
  - previous_score >= 0
```

#### AC2: 존재하지 않는 사용자

```gherkin
Given 해당 user_id를 가진 프로필이 없음
When get_user_profile("nonexistent-id")가 호출됨
Then 기본값을 포함한 dict가 반환됨:
  - user_id = "nonexistent-id"
  - self_level = "beginner"
  - years_experience = 0
  - interests = []
```

#### AC3: 유효하지 않은 입력

```gherkin
Given user_id가 유효하지 않음 (비어있거나 잘못된 형식)
When get_user_profile(invalid_id)가 호출됨
Then ValueError가 발생하거나 @tool 데코레이터에서 검증됨
```

#### AC4: 최신 프로필만 반환

```gherkin
Given 같은 user_id로 2개 이상의 프로필 레코드가 있음
When get_user_profile(user_id)가 호출됨
Then 가장 최신의 (submitted_at이 가장 최신인) 레코드만 반환됨
```

---

### 1.8 테스트 전략 (Phase 2에서 상세 작성)

#### Unit Tests (독립적 테스트)

1. `test_get_user_profile_found` - 사용자 프로필 존재
2. `test_get_user_profile_not_found` - 사용자 없음 → 기본값
3. `test_get_user_profile_partial_data` - 일부 필드 NULL
4. `test_get_user_profile_invalid_uuid` - 유효하지 않은 UUID

#### Integration Tests

1. `test_get_user_profile_latest_only` - 여러 레코드 중 최신만
2. `test_get_user_profile_db_error` - DB 연결 오류 처리

---

## 📝 Phase 1 체크리스트

- [x] 요구사항 분석
- [x] 입출력 명세 정의
- [x] Backend 연동 확인
- [x] 에러 처리 시나리오 정의
- [x] Acceptance Criteria 작성
- [x] 테스트 전략 초안

---

## 🔗 Reference

### Backend API

- Profile 모델: `src/backend/models/user_profile.py:UserProfileSurvey`
- Profile 서비스: `src/backend/services/profile_service.py`

### Agent 구조

- FastMCP Tools: `src/agent/fastmcp_server.py`
- Tool 사용 예: Tool 2-6 구현 참고

### 관련 Requirements

- Parent: `REQ-A-Mode1-Pipeline`
- Sibling: `REQ-A-Mode1-Tool2~5`

---

**Status**: ✅ Phase 1 완료
**Next**: Phase 2 (테스트 설계) 진행 가능
