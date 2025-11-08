# REQ-A-Mode1-Tool3: Phase 2 - Test Design

**작성일**: 2025-11-09
**단계**: Phase 2 (🧪 Test Design)
**상태**: 테스트 설계 완료, 코드 구현 대기

---

## 🧪 Phase 2: TEST DESIGN

### 2.1 테스트 설계 전략

#### 테스트 카테고리

| 카테고리 | 테스트 수 | 목표 |
|---------|---------|------|
| **Happy Path (Cache/DB)** | 3개 | 캐시 HIT, MISS, 정상 조회 |
| **Input Validation** | 2개 | 입력 검증 에러 처리 |
| **Database Errors** | 2개 | DB 에러 시 기본값/캐시 반환 |
| **Edge Cases** | 4개 | 캐시 만료, NULL 필드, 유니코드 등 |
| **Caching Strategy** | 2개 | 캐시 동작 검증 |

**총 테스트 수**: 13개

#### 테스트 설계 원칙

- ✅ Happy path: DB 쿼리 성공 → 캐시 저장 후 결과 반환
- ✅ Cache HIT: 캐시에 있음 → DB 조회 없이 즉시 반환
- ✅ Input validation: 입력 오류 → ValueError/TypeError 발생
- ✅ DB errors: DB 실패 → 기본값 또는 캐시 반환 (예외 없음)
- ✅ Null fields: NULL 데이터 → 기본값으로 정규화

---

### 2.2 Happy Path 테스트 (3개)

#### Test 1: test_get_difficulty_keywords_db_hit

**목적**: DB 쿼리 성공 후 캐시에 저장

**입력**:

```python
difficulty = 7
category = "technical"
```

**Mock DB 반환**:

```python
DifficultyKeyword(
    id="kw_001",
    difficulty=7,
    category="technical",
    keywords=["LLM", "Transformer", "Attention Mechanism", ...],
    concepts=[
        {
            "name": "Retrieval Augmented Generation",
            "acronym": "RAG",
            "definition": "LLM과 외부 지식 데이터베이스 연결...",
            "key_points": ["Retrieval", "Augmented", "Generation"]
        },
        # ... (최대 10개)
    ],
    example_questions=[
        {
            "stem": "Transformer의 Attention 역할은?",
            "type": "short_answer",
            "difficulty_score": 7.5,
            "answer_summary": "입력 시퀀스의 단어 간 영향도 계산"
        },
        # ... (최대 5개)
    ]
)
```

**기대 결과**:

```python
{
    "difficulty": 7,
    "category": "technical",
    "keywords": ["LLM", "Transformer", "Attention Mechanism", ...],
    "concepts": [
        {
            "name": "Retrieval Augmented Generation",
            "acronym": "RAG",
            "definition": "...",
            "key_points": [...]
        },
        # ...
    ],
    "example_questions": [
        {
            "stem": "Transformer의 Attention 역할은?",
            "type": "short_answer",
            "difficulty_score": 7.5,
            "answer_summary": "..."
        },
        # ...
    ]
}
```

**검증**:

- 결과는 dict 타입
- 모든 필드 포함: difficulty, category, keywords, concepts, example_questions
- keywords: 5개 이상 20개 이하
- concepts: 최대 10개, 각 필드 완전
- example_questions: 최대 5개
- 캐시에 저장됨 (두 번째 호출 시 빠름)

**REQ**: REQ-A-Mode1-Tool3, AC1

---

#### Test 2: test_get_difficulty_keywords_cache_hit

**목적**: 캐시에서 데이터 조회 (DB 호출 없음)

**입력**:

```python
difficulty = 5
category = "business"
```

**설정**:

1. 첫 호출: DB에서 조회 후 캐시 저장 (별도의 테스트에서 수행됨)
2. 두 번째 호출: 캐시에서 직접 반환

**기대 결과**:

```python
# 첫 호출
result1 = get_difficulty_keywords(5, "business")

# 캐시 확인 (내부 검증 - mock 통해)
# DB query 호출되지 않음 (mock.call_count == 0)

# 두 번째 호출
result2 = get_difficulty_keywords(5, "business")

# 동일한 결과
assert result1 == result2
```

**검증**:

- DB query 호출되지 않음 (캐시 HIT)
- 응답 시간 < 10ms (캐시 HIT)
- 응답 데이터 동일

**REQ**: REQ-A-Mode1-Tool3, AC4

---

#### Test 3: test_get_difficulty_keywords_with_null_fields

**목적**: DB에서 조회한 데이터의 NULL 필드를 기본값으로 채우기

**입력**:

```python
difficulty = 10
category = "general"
```

**Mock DB 반환**:

```python
DifficultyKeyword(
    id="kw_002",
    difficulty=10,
    category="general",
    keywords=None,  # NULL
    concepts=None,  # NULL
    example_questions=None,  # NULL
)
```

**기대 결과**:

```python
{
    "difficulty": 10,
    "category": "general",
    "keywords": [default values],  # 기본값으로 채워짐
    "concepts": [default values],  # 기본값으로 채워짐
    "example_questions": [default values]  # 기본값으로 채워짐
}
```

**검증**:

- 모든 NULL 필드가 기본값으로 대체됨
- keywords, concepts, example_questions 모두 존재
- 응답은 완전함

**REQ**: REQ-A-Mode1-Tool3, AC5

---

### 2.3 Input Validation 테스트 (2개)

#### Test 4: test_get_difficulty_keywords_invalid_difficulty

**목적**: difficulty가 범위를 벗어난 경우

**입력**:

```python
difficulty = 11  # 범위 초과 (1-10)
category = "technical"
```

**기대 결과**: `ValueError` 발생

**검증**:

```python
with pytest.raises(ValueError):
    get_difficulty_keywords(11, "technical")
```

**REQ**: REQ-A-Mode1-Tool3, AC3

---

#### Test 5: test_get_difficulty_keywords_invalid_category

**목적**: category가 미지원 값인 경우

**입력**:

```python
difficulty = 7
category = "unknown_category"
```

**기대 결과**: `ValueError` 발생

**검증**:

```python
with pytest.raises(ValueError):
    get_difficulty_keywords(7, "unknown_category")
```

**REQ**: REQ-A-Mode1-Tool3, AC3

---

### 2.4 Database Error 테스트 (2개)

#### Test 6: test_get_difficulty_keywords_db_connection_error

**목적**: DB 연결 실패 시 기본값 반환

**입력**:

```python
difficulty = 7
category = "technical"
```

**Mock DB 동작**: `.query()` 호출 시 `OperationalError` 발생

**기대 결과**:

```python
result = {
    "difficulty": 7,
    "category": "technical",
    "keywords": [기본값],  # DEFAULT_KEYWORDS 사용
    "concepts": [기본값],
    "example_questions": [기본값]
}
# 예외 발생 없음
```

**검증**:

- 예외 발생 안 함
- 기본값 또는 캐시 반환
- 로그에 WARNING/ERROR 기록

**REQ**: REQ-A-Mode1-Tool3, AC2

---

#### Test 7: test_get_difficulty_keywords_query_timeout

**목적**: DB 쿼리 타임아웃 시 기본값 반환

**입력**:

```python
difficulty = 5
category = "business"
```

**Mock DB 동작**: `.first()` 호출 시 `TimeoutError` 발생

**기대 결과**:

```python
result = {기본값}  # DEFAULT_KEYWORDS
# 예외 발생 없음
```

**검증**:

- 예외 발생 안 함
- 기본값 반환
- 로그 기록

**REQ**: REQ-A-Mode1-Tool3, AC2

---

### 2.5 Edge Cases 테스트 (4개)

#### Test 8: test_get_difficulty_keywords_all_difficulty_levels

**목적**: 모든 난이도 레벨(1-10) 처리

**입력**: difficulty = 1, 5, 10 (각각 테스트)

**기대 결과**: 모든 난이도에서 정상 응답

**검증**:

```python
for diff in range(1, 11):
    result = get_difficulty_keywords(diff, "technical")
    assert result is not None
    assert result["difficulty"] == diff
```

**REQ**: REQ-A-Mode1-Tool3

---

#### Test 9: test_get_difficulty_keywords_all_categories

**목적**: 모든 카테고리 (technical, business, general) 처리

**입력**: category = "technical", "business", "general" (각각)

**기대 결과**: 모든 카테고리에서 정상 응답

**검증**:

```python
for cat in ["technical", "business", "general"]:
    result = get_difficulty_keywords(7, cat)
    assert result is not None
    assert result["category"] == cat
```

**REQ**: REQ-A-Mode1-Tool3

---

#### Test 10: test_get_difficulty_keywords_with_unicode_in_concepts

**목적**: 한글, 중국어 등 유니코드 처리

**입력**:

```python
difficulty = 7
category = "technical"
```

**Mock DB 반환**: concepts에 한글 포함

```python
{
    "name": "트랜스포머 아키텍처",
    "definition": "심층 신경망 모델...",
    "key_points": ["주목 메커니즘", "위치 인코딩", "다중 헤드"]
}
```

**기대 결과**: 유니코드 손실 없음

**검증**:

```python
result = get_difficulty_keywords(7, "technical")
assert "트랜스포머" in str(result)  # 유니코드 보존
```

**REQ**: REQ-A-Mode1-Tool3

---

#### Test 11: test_get_difficulty_keywords_response_completeness

**목적**: 응답의 모든 필드가 정의된 범위 내 데이터 포함

**입력**:

```python
difficulty = 7
category = "technical"
```

**기대 결과**: 응답의 각 필드가 요구사항 충족

**검증**:

```python
result = get_difficulty_keywords(7, "technical")
# keywords: 5-20개
assert 5 <= len(result["keywords"]) <= 20
# concepts: 최대 10개
assert len(result["concepts"]) <= 10
# 각 concept 필드 완전
for concept in result["concepts"]:
    assert "name" in concept
    assert "acronym" in concept
    assert "definition" in concept
    assert "key_points" in concept
    assert isinstance(concept["key_points"], list)
# example_questions: 최대 5개
assert len(result["example_questions"]) <= 5
```

**REQ**: REQ-A-Mode1-Tool3, AC1

---

### 2.6 Caching Strategy 테스트 (2개)

#### Test 12: test_cache_ttl_expiration

**목적**: 캐시 TTL 만료 후 DB 재조회

**입력**:

```python
difficulty = 3
category = "general"
```

**설정**:

1. 첫 호출: DB에서 조회, 캐시 저장 (TTL: 3600초)
2. TTL 만료 시뮬레이션: 시간 경과
3. 재호출: DB 재조회

**기대 결과**: TTL 만료 후 DB 다시 조회

**검증**:

```python
# 첫 호출
result1 = get_difficulty_keywords(3, "general")
# DB call count: 1

# TTL 만료 시뮬레이션 (mock time 또는 캐시 강제 제거)
# ...

# 재호출
result2 = get_difficulty_keywords(3, "general")
# DB call count: 2 (재조회됨)
```

**REQ**: REQ-A-Mode1-Tool3, AC4

---

#### Test 13: test_cache_graceful_degradation

**목적**: DB 실패 시 캐시 우선 사용

**입력**:

```python
difficulty = 6
category = "business"
```

**시나리오**:

1. 첫 호출: DB 정상 조회 후 캐시 저장
2. 두 번째 호출: DB 실패 발생
3. 기대: 캐시에서 조회 반환

**기대 결과**:

```python
# 첫 호출
result1 = get_difficulty_keywords(6, "business")  # DB에서 조회

# DB 실패 설정
mock_db.query.side_effect = OperationalError(...)

# 재호출
result2 = get_difficulty_keywords(6, "business")  # 캐시에서 반환
assert result1 == result2  # 동일한 데이터
# 예외 발생 안 함
```

**검증**:

- 캐시 존재: 캐시에서 반환
- 캐시 미존재: 기본값 반환
- 예외 발생 없음

**REQ**: REQ-A-Mode1-Tool3, AC2

---

### 2.7 Mock 전략

#### Mock 대상

1. **`get_db()` 함수**
   - 반환: SQLAlchemy Session 모의 객체
   - 패턴: `patch("src.agent.tools.difficulty_keywords_tool.get_db")`

2. **`db.query(DifficultyKeyword)` 체인**

   ```python
   mock_query = MagicMock()
   mock_db.query.return_value = mock_query
   mock_query.filter.return_value = mock_query
   mock_query.first.return_value = keyword_record
   ```

3. **SQLAlchemy 예외**
   - `OperationalError`: DB 연결 실패
   - `TimeoutError`: 쿼리 타임아웃

4. **캐시 시뮬레이션**
   - `unittest.mock.patch`로 캐시 딕셔너리 패치
   - 캐시 clear/set으로 TTL 시뮬레이션

#### Fixture 설계

```python
@pytest.fixture
def valid_keyword_record():
    """Sample DifficultyKeyword record"""
    return MagicMock(
        id="kw_001",
        difficulty=7,
        category="technical",
        keywords=["LLM", "Transformer", ...],
        concepts=[
            {
                "name": "RAG",
                "acronym": "RAG",
                "definition": "...",
                "key_points": [...]
            },
            # ...
        ],
        example_questions=[...]
    )

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

@pytest.fixture
def default_keywords():
    """DEFAULT_KEYWORDS fallback"""
    return {
        "difficulty": 5,
        "category": "general",
        "keywords": [...],
        "concepts": [...],
        "example_questions": [...]
    }
```

---

### 2.8 테스트 커버리지 목표

| 항목 | 커버리지 |
|------|---------|
| **입력 검증** | 100% (2개 경로) |
| **DB 쿼리** | 100% (성공 + 실패) |
| **캐시 로직** | 100% (HIT, MISS, 만료) |
| **기본값 폴백** | 100% |
| **NULL 필드 처리** | 100% |
| **전체 라인** | >= 95% |

---

### 2.9 테스트 파일 구조

```python
# tests/agent/tools/test_difficulty_keywords_tool.py

import uuid
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.backend.models.difficulty_keyword import DifficultyKeyword
from src.agent.tools.difficulty_keywords_tool import get_difficulty_keywords


# Fixtures
@pytest.fixture
def valid_keyword_record() -> MagicMock:
    """Sample DifficultyKeyword record"""
    return MagicMock(spec=DifficultyKeyword, ...)

@pytest.fixture
def mock_db() -> MagicMock:
    """Mock database session"""
    return MagicMock(spec=Session)

@pytest.fixture
def default_keywords() -> dict[str, Any]:
    """DEFAULT_KEYWORDS fallback"""
    return {...}


# Happy Path Tests (Cache & DB)
class TestGetDifficultyKeywordsHappyPath:
    def test_get_difficulty_keywords_db_hit(self, ...):
        ...

    def test_get_difficulty_keywords_cache_hit(self, ...):
        ...

    def test_get_difficulty_keywords_with_null_fields(self, ...):
        ...


# Input Validation Tests
class TestGetDifficultyKeywordsInputValidation:
    def test_get_difficulty_keywords_invalid_difficulty(self):
        ...

    def test_get_difficulty_keywords_invalid_category(self):
        ...


# Database Error Tests
class TestGetDifficultyKeywordsDatabaseErrors:
    def test_get_difficulty_keywords_db_connection_error(self, ...):
        ...

    def test_get_difficulty_keywords_query_timeout(self, ...):
        ...


# Edge Cases Tests
class TestGetDifficultyKeywordsEdgeCases:
    def test_get_difficulty_keywords_all_difficulty_levels(self):
        ...

    def test_get_difficulty_keywords_all_categories(self):
        ...

    def test_get_difficulty_keywords_with_unicode_in_concepts(self, ...):
        ...

    def test_get_difficulty_keywords_response_completeness(self, ...):
        ...


# Caching Strategy Tests
class TestGetDifficultyKeywordsCaching:
    def test_cache_ttl_expiration(self, ...):
        ...

    def test_cache_graceful_degradation(self, ...):
        ...
```

---

## 📊 Phase 2 요약

### 2.10 테스트 매트릭스

| Test # | 이름 | 카테고리 | 검증 대상 | REQ |
|--------|------|---------|---------|-----|
| 1 | db_hit | Happy | DB 조회 + 캐시 저장 | AC1 |
| 2 | cache_hit | Happy | 캐시 조회 | AC4 |
| 3 | null_fields | Happy | NULL 정규화 | AC5 |
| 4 | invalid_difficulty | Validation | ValueError | AC3 |
| 5 | invalid_category | Validation | ValueError | AC3 |
| 6 | db_connection_error | DBError | 기본값 반환 | AC2 |
| 7 | query_timeout | DBError | 기본값 반환 | AC2 |
| 8 | all_difficulty_levels | EdgeCase | 1-10 테스트 | - |
| 9 | all_categories | EdgeCase | 3가지 카테고리 | - |
| 10 | unicode_in_concepts | EdgeCase | 유니코드 | - |
| 11 | response_completeness | EdgeCase | 필드 범위 검증 | AC1 |
| 12 | cache_ttl_expiration | Caching | TTL 만료 | AC4 |
| 13 | cache_graceful_degradation | Caching | 캐시 폴백 | AC2 |

---

### 2.11 다음 단계

- [ ] Phase 2 검토 및 승인
- [ ] Phase 3: 구현 코드 작성 (difficulty_keywords_tool.py)
- [ ] Phase 3: 테스트 실행 및 통과 확인 (13/13)
- [ ] Phase 4: 커밋 및 진행 상황 추적

---

**Status**: ✅ Phase 2 완료
**Next**: Phase 3 (구현 & 테스트 실행)
