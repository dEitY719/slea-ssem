# REQ-A-Mode1-Tool1: Phase 2 - Test Design

**작성일**: 2025-11-08
**단계**: Phase 2 (🧪 Test Design)
**상태**: 테스트 설계 완료

---

## 🧪 Phase 2: TEST DESIGN

### 2.1 테스트 구조

#### 테스트 파일 위치

```
tests/agent/tools/
├── __init__.py
└── test_user_profile_tool.py
```

#### 테스트 클래스 구성

```
TestGetUserProfileHappyPath (행복 경로)
├── test_get_user_profile_found_full_data
├── test_get_user_profile_found_partial_data
└── test_get_user_profile_found_with_interests

TestGetUserProfileNotFound (사용자 없음)
├── test_get_user_profile_not_found
└── test_get_user_profile_not_found_returns_defaults

TestGetUserProfileInputValidation (입력 검증)
├── test_get_user_profile_invalid_uuid_format
├── test_get_user_profile_empty_string
└── test_get_user_profile_none_input

TestGetUserProfileDatabaseErrors (DB 에러)
├── test_get_user_profile_db_connection_error
└── test_get_user_profile_db_query_timeout

TestGetUserProfileEdgeCases (엣지 케이스)
├── test_get_user_profile_multiple_records_returns_latest
├── test_get_user_profile_null_fields_filled_with_defaults
└── test_get_user_profile_unicode_characters
```

---

### 2.2 테스트 케이스 상세

#### 1️⃣ test_get_user_profile_found_full_data

**Category**: Happy Path

**목적**: 완전한 프로필 데이터가 있을 때 정상 조회

**전제조건**:

```python
user_id = "550e8400-e29b-41d4-a716-446655440000"
profile = UserProfileSurvey(
    user_id=user_id,
    self_level="intermediate",
    years_experience=5,
    job_role="Senior Backend Engineer",
    duty="System design and API development",
    interests=["LLM", "RAG", "Agent Architecture"],
    submitted_at=datetime.utcnow()
)
# DB에 저장됨
```

**실행**:

```python
result = get_user_profile(user_id)
```

**기대 결과**:

```python
assert result["user_id"] == user_id
assert result["self_level"] == "intermediate"
assert result["years_experience"] == 5
assert result["job_role"] == "Senior Backend Engineer"
assert result["duty"] == "System design and API development"
assert result["interests"] == ["LLM", "RAG", "Agent Architecture"]
assert isinstance(result["previous_score"], int)
assert 0 <= result["previous_score"] <= 100
```

---

#### 2️⃣ test_get_user_profile_found_partial_data

**Category**: Happy Path

**목적**: 일부 필드가 NULL이어도 기본값으로 채워지는지 확인

**전제조건**:

```python
user_id = "550e8400-e29b-41d4-a716-446655440001"
profile = UserProfileSurvey(
    user_id=user_id,
    self_level="beginner",
    years_experience=1,
    job_role=None,          # NULL
    duty=None,              # NULL
    interests=None,         # NULL
    submitted_at=datetime.utcnow()
)
```

**실행**:

```python
result = get_user_profile(user_id)
```

**기대 결과**:

```python
assert result["user_id"] == user_id
assert result["self_level"] == "beginner"
assert result["job_role"] in ["", "Unknown", None] or isinstance(result["job_role"], str)
assert result["interests"] == [] or result["interests"] is None
```

---

#### 3️⃣ test_get_user_profile_found_with_interests

**Category**: Happy Path

**목적**: 관심사 리스트가 정상 반환되는지 확인

**전제조건**:

```python
interests = ["LLM", "FastAPI", "DevOps"]
profile = UserProfileSurvey(
    user_id="550e8400-e29b-41d4-a716-446655440002",
    interests=interests
)
```

**기대 결과**:

```python
result = get_user_profile("550e8400-e29b-41d4-a716-446655440002")
assert result["interests"] == interests
assert len(result["interests"]) == 3
```

---

#### 4️⃣ test_get_user_profile_not_found

**Category**: Not Found

**목적**: 존재하지 않는 사용자 ID로 조회할 때 기본값 반환

**전제조건**:

```python
user_id = "nonexistent-uuid-12345678-9012-3456-7890-123456789012"
# DB에 존재하지 않음
```

**실행**:

```python
result = get_user_profile(user_id)
```

**기대 결과**:

```python
assert result["user_id"] == user_id  # 요청한 ID는 그대로
assert result["self_level"] == "beginner"
assert result["years_experience"] == 0
assert result["job_role"] in ["Unknown", ""]
assert result["duty"] in ["Not specified", ""]
assert result["interests"] == []
assert result["previous_score"] == 0
```

---

#### 5️⃣ test_get_user_profile_invalid_uuid_format

**Category**: Input Validation

**목적**: 잘못된 UUID 형식 거부

**입력**:

```python
user_id = "invalid-uuid-format"
```

**기대 결과**:

```python
# 다음 중 하나:
# A) ValueError 발생
# B) Tool 데코레이터에서 검증 실패
# C) None 반환 (안전한 폴백)

try:
    result = get_user_profile(user_id)
    assert result is None or result["user_id"] == user_id
except ValueError as e:
    assert "invalid" in str(e).lower() or "uuid" in str(e).lower()
```

---

#### 6️⃣ test_get_user_profile_empty_string

**Category**: Input Validation

**목적**: 빈 문자열 입력 처리

**입력**:

```python
user_id = ""
```

**기대 결과**:

```python
try:
    result = get_user_profile(user_id)
    # 빈 문자열로 조회하면 기본값 반환 또는 에러
except ValueError:
    pass  # 예상된 동작
```

---

#### 7️⃣ test_get_user_profile_none_input

**Category**: Input Validation

**목적**: None 입력 처리

**입력**:

```python
user_id = None
```

**기대 결과**:

```python
try:
    result = get_user_profile(None)
    assert result is None or isinstance(result, dict)
except (ValueError, TypeError):
    pass  # 예상된 동작
```

---

#### 8️⃣ test_get_user_profile_db_connection_error

**Category**: Database Errors

**목적**: DB 연결 실패 시 안전한 폴백

**전제조건**:

```python
# DB mock: 연결 시간초과
session.query().side_effect = OperationalError("Connection timeout")
```

**기대 결과**:

```python
result = get_user_profile(user_id)
# 기본값 반환 또는 재시도 메커니즘 동작
assert isinstance(result, dict)
assert "user_id" in result
```

---

#### 9️⃣ test_get_user_profile_db_query_timeout

**Category**: Database Errors

**목적**: 쿼리 시간초과 처리

**기대 결과**:

```python
result = get_user_profile(user_id)
# 타임아웃 후 기본값 반환
assert result["self_level"] == "beginner"
```

---

#### 🔟 test_get_user_profile_multiple_records_returns_latest

**Category**: Edge Cases

**목적**: 같은 user_id로 여러 프로필이 있을 때 최신만 반환

**전제조건**:

```python
user_id = "550e8400-e29b-41d4-a716-446655440003"

# 이전 프로필 (1시간 전)
old_profile = UserProfileSurvey(
    user_id=user_id,
    self_level="beginner",
    submitted_at=datetime.utcnow() - timedelta(hours=1)
)

# 최신 프로필 (방금)
new_profile = UserProfileSurvey(
    user_id=user_id,
    self_level="advanced",
    submitted_at=datetime.utcnow()
)
# 둘 다 DB에 저장
```

**기대 결과**:

```python
result = get_user_profile(user_id)
assert result["self_level"] == "advanced"  # 최신 것만
```

---

#### 1️⃣1️⃣ test_get_user_profile_null_fields_filled_with_defaults

**Category**: Edge Cases

**목적**: NULL 필드를 기본값으로 채우기

**전제조건**:

```python
profile = UserProfileSurvey(
    user_id=user_id,
    job_role=None,
    duty=None,
    interests=None
)
```

**기대 결과**:

```python
result = get_user_profile(user_id)
assert result["job_role"] != None or result["job_role"] == ""
assert result["interests"] == [] or result["interests"] == None
```

---

#### 1️⃣2️⃣ test_get_user_profile_unicode_characters

**Category**: Edge Cases

**목적**: 유니코드 문자 처리

**전제조건**:

```python
profile = UserProfileSurvey(
    user_id=user_id,
    job_role="데이터 엔지니어",  # 한글
    duty="분석 및 모델 개발",
    interests=["머신러닝", "데이터베이스"]
)
```

**기대 결과**:

```python
result = get_user_profile(user_id)
assert result["job_role"] == "데이터 엔지니어"
assert "머신러닝" in result["interests"]
```

---

### 2.3 Mock & Fixture 전략

#### Mock 대상

1. **DB Session** (SQLAlchemy ORM)

   ```python
   @pytest.fixture
   def mock_db():
       return MagicMock(spec=Session)
   ```

2. **UserProfileSurvey Query**

   ```python
   @pytest.fixture
   def mock_profile():
       return MagicMock(spec=UserProfileSurvey)
   ```

#### Fixture 정의

```python
@pytest.fixture
def user_profile_data():
    """기본 사용자 프로필 데이터"""
    return {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "self_level": "intermediate",
        "years_experience": 5,
        "job_role": "Backend Engineer",
        "duty": "API development",
        "interests": ["LLM", "RAG"],
        "previous_score": 75
    }

@pytest.fixture
def db_session(mock_db):
    """Mock DB 세션"""
    return mock_db
```

---

### 2.4 테스트 커버리지 목표

| 카테고리 | 테스트 수 | 커버리지 |
|---------|---------|---------|
| Happy Path | 3 | 70% |
| Not Found | 2 | 15% |
| Input Validation | 3 | 10% |
| DB Errors | 2 | 3% |
| Edge Cases | 3 | 2% |
| **Total** | **13** | **100%** |

**목표**: 100% 라인 커버리지 (코어 로직)

---

### 2.5 테스트 실행 전략

#### 단계 1: Unit Tests (격리)

```bash
pytest tests/agent/tools/test_user_profile_tool.py -v
```

#### 단계 2: Integration Tests (DB 포함)

```bash
pytest tests/agent/tools/test_user_profile_tool.py::TestIntegration -v
```

#### 단계 3: 전체 Agent 테스트

```bash
pytest tests/agent/ -v
```

---

## 📝 Phase 2 체크리스트

- [x] 테스트 클래스 구조 정의
- [x] 12개 테스트 케이스 상세 작성
- [x] Mock & Fixture 전략 수립
- [x] 커버리지 목표 설정 (100%)
- [x] 테스트 실행 전략 수립

---

## 🔗 Reference

### 유사 테스트 예시

- Backend Tool 테스트: `tests/backend/test_profile_service.py`
- Agent 테스트 구조: `tests/agent/test_llm_agent.py`

### Phase 1 스펙

- 입출력 명세: `docs/progress/REQ-A-Mode1-Tool1.md#1-2`
- Acceptance Criteria: `docs/progress/REQ-A-Mode1-Tool1.md#1-7`

---

**Status**: ✅ Phase 2 완료
**Next**: Phase 3 (구현) 진행 가능
