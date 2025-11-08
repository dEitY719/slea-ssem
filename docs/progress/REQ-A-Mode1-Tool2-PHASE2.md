# REQ-A-Mode1-Tool2: Phase 2 - Test Design

**작성일**: 2025-11-09
**단계**: Phase 2 (🧪 Test Design)
**상태**: 테스트 설계 완료, 코드 구현 대기

---

## 🧪 Phase 2: TEST DESIGN

### 2.1 테스트 설계 전략

#### 테스트 카테고리

| 카테고리 | 테스트 수 | 목표 |
|---------|---------|------|
| **Happy Path** | 4개 | 정상 동작 검증 |
| **Input Validation** | 3개 | 입력 검증 에러 처리 |
| **Database Errors** | 2개 | DB 에러 graceful handling |
| **Edge Cases** | 3개 | 경계값, 특수 문자 등 |
| **Performance** | 1개 | 응답 시간 < 500ms |

**총 테스트 수**: 13개

#### 테스트 설계 원칙

- ✅ Happy path: 데이터 있음 → 정렬된 결과 반환
- ✅ Data not found: 데이터 없음 → 빈 리스트 반환
- ✅ Input validation: 잘못된 입력 → ValueError/TypeError 발생
- ✅ DB errors: DB 실패 → 빈 리스트 반환 (graceful)
- ✅ Edge cases: 특수 문자, NULL 필드, 최대값 등 처리

---

### 2.2 Happy Path 테스트 (4개)

#### Test 1: test_search_templates_found_with_all_fields

**목적**: 모든 필드가 있는 정상적인 템플릿 검색

**입력**:

```python
interests = ["LLM", "RAG", "Agent Architecture"]
difficulty = 7
category = "technical"
```

**Mock DB 반환**:

```python
[
    QuestionTemplate(
        id="tmpl_001",
        stem="What is RAG?",
        type="short_answer",
        choices=None,
        correct_answer="A technique combining retrieval and generation",
        correct_rate=0.85,
        usage_count=50,
        avg_difficulty_score=7.3,
        domain="RAG"
    ),
    # ... (1-2개 더)
]
```

**기대 결과**:

```python
[
    {
        "id": "tmpl_001",
        "stem": "What is RAG?",
        "type": "short_answer",
        "choices": None or [],
        "correct_answer": "A technique...",
        "correct_rate": 0.85,
        "usage_count": 50,
        "avg_difficulty_score": 7.3
    },
    # ...
]
```

**검증**:

- 결과는 list[dict]
- 각 항목의 모든 필드 존재
- 결과가 correct_rate로 내림차순 정렬
- 최대 10개 이하

**REQ**: REQ-A-Mode1-Tool2, AC1

---

#### Test 2: test_search_templates_found_multiple_candidates

**목적**: 여러 템플릿이 조건을 만족할 때 상위 10개만 반환

**입력**:

```python
interests = ["LLM"]
difficulty = 5
category = "technical"
```

**Mock DB 반환**: 25개 문항 템플릿 (DB가 정렬하여 상위 10개만 반환)

**기대 결과**:

```python
len(result) == 10  # 정확히 10개
# 모두 correct_rate로 내림차순 정렬됨
for i in range(len(result)-1):
    assert result[i]["correct_rate"] >= result[i+1]["correct_rate"]
```

**검증**:

- 정확히 10개 반환 (초과 불가)
- correct_rate 내림차순 정렬
- 각 템플릿의 난이도가 5±1.5 범위

**REQ**: REQ-A-Mode1-Tool2, AC1

---

#### Test 3: test_search_templates_with_multiple_interests

**목적**: 여러 관심분야 중 하나라도 일치하는 템플릿 검색

**입력**:

```python
interests = ["FastAPI", "DevOps", "Kubernetes"]
difficulty = 6
category = "technical"
```

**Mock DB 반환**:

```python
[
    # domain="FastAPI" 템플릿
    # domain="Kubernetes" 템플릿
    # domain="Docker" 템플릿 (일치하지 않으면 제외)
]
```

**기대 결과**:

- FastAPI 관련 템플릿 포함
- Kubernetes 관련 템플릿 포함
- Docker만 있는 템플릿은 없음 (interests에 없음)

**검증**:

- 모든 결과의 domain이 interests 중 하나
- 여러 domain 조합 가능

**REQ**: REQ-A-Mode1-Tool2

---

#### Test 4: test_search_templates_with_difficulty_range

**목적**: 난이도 필터링 (difficulty ± 1.5) 검증

**입력**:

```python
interests = ["LLM"]
difficulty = 7
category = "technical"
```

**Mock DB 반환**: 난이도 스펙트럼 (3, 5, 5.5, 7, 7.5, 8.5, 9, 10)

**기대 결과**:

```python
# 모든 결과의 난이도가 5.5 ~ 8.5 범위
for result in results:
    assert 5.5 <= result["avg_difficulty_score"] <= 8.5
```

**검증**:

- difficulty - 1.5 ≤ avg_difficulty_score ≤ difficulty + 1.5
- 범위 밖의 템플릿은 DB 쿼리에서 필터됨

**REQ**: REQ-A-Mode1-Tool2, AC4

---

### 2.3 Data Not Found 테스트 (1개)

#### Test 5: test_search_templates_not_found

**목적**: 일치하는 템플릿 없을 때 빈 리스트 반환

**입력**:

```python
interests = ["VeryRareKeyword123"]
difficulty = 7
category = "technical"
```

**Mock DB 반환**: `[]` (빈 리스트)

**기대 결과**:

```python
result == []
# 예외 발생 없음
```

**검증**:

- 예외 발생 안 함 (ValueError, TypeError, Exception 없음)
- 빈 리스트 반환
- 파이프라인은 Tool 3으로 진행

**REQ**: REQ-A-Mode1-Tool2, AC2

---

### 2.4 Input Validation 테스트 (3개)

#### Test 6: test_search_templates_invalid_interests_type

**목적**: interests가 list가 아닌 경우 처리

**입력**:

```python
interests = "LLM"  # string instead of list
difficulty = 7
category = "technical"
```

**기대 결과**: `TypeError` 발생

**검증**:

```python
with pytest.raises(TypeError):
    search_question_templates(interests, difficulty, category)
```

**REQ**: REQ-A-Mode1-Tool2, AC3

---

#### Test 7: test_search_templates_invalid_difficulty

**목적**: difficulty가 범위를 벗어난 경우

**입력**:

```python
interests = ["LLM"]
difficulty = 11  # 범위 초과 (1-10)
category = "technical"
```

**기대 결과**: `ValueError` 발생

**검증**:

```python
with pytest.raises(ValueError):
    search_question_templates(interests, 11, category)
```

**REQ**: REQ-A-Mode1-Tool2, AC3

---

#### Test 8: test_search_templates_invalid_category

**목적**: category가 미지원 값인 경우

**입력**:

```python
interests = ["LLM"]
difficulty = 7
category = "unknown_category"
```

**기대 결과**: `ValueError` 발생

**검증**:

```python
with pytest.raises(ValueError):
    search_question_templates(interests, 7, "unknown_category")
```

**REQ**: REQ-A-Mode1-Tool2, AC3

---

### 2.5 Database Error 테스트 (2개)

#### Test 9: test_search_templates_db_connection_error

**목적**: DB 연결 실패 시 빈 리스트 반환

**입력**:

```python
interests = ["LLM"]
difficulty = 7
category = "technical"
```

**Mock DB 동작**: `.query()` 호출 시 `OperationalError` 발생

**기대 결과**:

```python
result == []  # 빈 리스트 반환, 예외 발생 없음
```

**검증**:

- 예외 발생 안 함
- 빈 리스트 반환
- 로그에 WARNING/ERROR 레벨 메시지 기록

**REQ**: REQ-A-Mode1-Tool2, AC5

---

#### Test 10: test_search_templates_query_timeout

**목적**: DB 쿼리 타임아웃 시 빈 리스트 반환

**입력**:

```python
interests = ["LLM"]
difficulty = 7
category = "technical"
```

**Mock DB 동작**: `.first()` 호출 시 `TimeoutError` 발생

**기대 결과**:

```python
result == []  # 빈 리스트 반환, 예외 발생 없음
```

**검증**:

- 예외 발생 안 함
- 빈 리스트 반환
- 로그 기록

**REQ**: REQ-A-Mode1-Tool2, AC5

---

### 2.6 Edge Cases 테스트 (3개)

#### Test 11: test_search_templates_with_empty_interests_list

**목적**: interests 리스트가 빈 경우

**입력**:

```python
interests = []  # 빈 리스트
difficulty = 7
category = "technical"
```

**기대 결과**: `ValueError` 발생 (1-10개 요소 필수)

**검증**:

```python
with pytest.raises(ValueError):
    search_question_templates([], difficulty, category)
```

**REQ**: REQ-A-Mode1-Tool2

---

#### Test 12: test_search_templates_with_unicode_characters

**목적**: 한글, 중국어 등 유니코드 문자 처리

**입력**:

```python
interests = ["머신러닝", "자연언어처리", "深度学习"]
difficulty = 7
category = "technical"
```

**Mock DB 반환**:

```python
[
    QuestionTemplate(
        id="tmpl_001",
        stem="머신러닝의 주요 개념은?",
        domain="머신러닝",
        # ...
    )
]
```

**기대 결과**:

```python
len(result) >= 1
assert result[0]["stem"] == "머신러닝의 주요 개념은?"
```

**검증**:

- 유니코드 문자가 손실되지 않음
- 정상적으로 검색 및 반환

**REQ**: REQ-A-Mode1-Tool2

---

#### Test 13: test_search_templates_sorting_by_correct_rate

**목적**: 결과가 correct_rate로 정렬됨

**입력**:

```python
interests = ["LLM"]
difficulty = 7
category = "technical"
```

**Mock DB 반환**:

```python
[
    QuestionTemplate(id="1", correct_rate=0.50, usage_count=10),
    QuestionTemplate(id="2", correct_rate=0.90, usage_count=100),
    QuestionTemplate(id="3", correct_rate=0.70, usage_count=50),
]
```

**기대 결과**:

```python
result == [
    {"id": "2", "correct_rate": 0.90, ...},  # 상위
    {"id": "3", "correct_rate": 0.70, ...},
    {"id": "1", "correct_rate": 0.50, ...},  # 하위
]
```

**검증**:

```python
for i in range(len(result)-1):
    assert result[i]["correct_rate"] >= result[i+1]["correct_rate"]
```

**REQ**: REQ-A-Mode1-Tool2, AC1

---

### 2.7 Mock 전략

#### Mock 대상

1. **`get_db()` 함수**
   - 반환: SQLAlchemy Session 모의 객체
   - 패턴: `patch("src.agent.tools.search_templates_tool.get_db")`

2. **`db.query(QuestionTemplate)` 체인**

   ```python
   mock_query = MagicMock()
   mock_db.query.return_value = mock_query
   mock_query.filter.return_value = mock_query
   mock_query.order_by.return_value = mock_query
   mock_query.all.return_value = [template1, template2, ...]
   ```

3. **SQLAlchemy 예외**
   - `OperationalError`: DB 연결 실패
   - `TimeoutError`: 쿼리 타임아웃
   - `Exception`: 일반 예외

#### Fixture 설계

```python
@pytest.fixture
def valid_search_params():
    return {
        "interests": ["LLM", "RAG"],
        "difficulty": 7,
        "category": "technical"
    }

@pytest.fixture
def mock_templates():
    """Create sample template objects"""
    return [
        MagicMock(
            id="tmpl_001",
            stem="What is RAG?",
            type="short_answer",
            choices=None,
            correct_answer="...",
            correct_rate=0.85,
            usage_count=50,
            avg_difficulty_score=7.3,
            domain="RAG"
        ),
        # ...
    ]

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)
```

---

### 2.8 테스트 커버리지 목표

| 항목 | 커버리지 |
|------|---------|
| **입력 검증** | 100% (3개 검증 경로) |
| **DB 쿼리** | 100% (happy path + error path) |
| **정렬 로직** | 100% |
| **에러 처리** | 100% (입력 오류, DB 오류) |
| **전체 라인** | >= 95% |

---

### 2.9 테스트 파일 구조

```python
# tests/agent/tools/test_search_templates_tool.py

import uuid
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.backend.models.question_template import QuestionTemplate
from src.agent.tools.search_templates_tool import search_question_templates


# Fixtures
@pytest.fixture
def valid_search_params() -> dict[str, Any]:
    """Valid search parameters"""
    return {...}

@pytest.fixture
def mock_templates() -> list[MagicMock]:
    """Sample template objects"""
    return [...]

@pytest.fixture
def mock_db() -> MagicMock:
    """Mock database session"""
    return MagicMock(spec=Session)


# Happy Path Tests
class TestSearchTemplatesHappyPath:
    def test_search_templates_found_with_all_fields(self, ...):
        ...

    # ... (3개 더)


# Data Not Found Tests
class TestSearchTemplatesNotFound:
    def test_search_templates_not_found(self, ...):
        ...


# Input Validation Tests
class TestSearchTemplatesInputValidation:
    def test_search_templates_invalid_interests_type(self):
        ...

    # ... (2개 더)


# Database Error Tests
class TestSearchTemplatesDatabaseErrors:
    def test_search_templates_db_connection_error(self, ...):
        ...

    def test_search_templates_query_timeout(self, ...):
        ...


# Edge Cases Tests
class TestSearchTemplatesEdgeCases:
    def test_search_templates_with_empty_interests_list(self):
        ...

    def test_search_templates_with_unicode_characters(self, ...):
        ...

    def test_search_templates_sorting_by_correct_rate(self, ...):
        ...
```

---

## 📊 Phase 2 요약

### 2.10 테스트 매트릭스

| Test # | 이름 | 카테고리 | 검증 대상 | REQ |
|--------|------|---------|---------|-----|
| 1 | found_with_all_fields | Happy | 정상 검색 | AC1 |
| 2 | found_multiple_candidates | Happy | 상위 10개 제한 | AC1 |
| 3 | with_multiple_interests | Happy | 다중 interests | AC1 |
| 4 | with_difficulty_range | Happy | 난이도 필터 | AC4 |
| 5 | not_found | NotFound | 빈 리스트 | AC2 |
| 6 | invalid_interests_type | Validation | TypeError | AC3 |
| 7 | invalid_difficulty | Validation | ValueError | AC3 |
| 8 | invalid_category | Validation | ValueError | AC3 |
| 9 | db_connection_error | DBError | 연결 실패 | AC5 |
| 10 | query_timeout | DBError | 타임아웃 | AC5 |
| 11 | empty_interests_list | EdgeCase | 빈 리스트 | AC3 |
| 12 | unicode_characters | EdgeCase | 유니코드 | - |
| 13 | sorting_by_correct_rate | EdgeCase | 정렬 검증 | AC1 |

---

### 2.11 다음 단계

- [ ] Phase 2 검토 및 승인
- [ ] Phase 3: 구현 코드 작성 (search_templates_tool.py)
- [ ] Phase 3: 테스트 실행 및 통과 확인 (13/13)
- [ ] Phase 4: 커밋 및 진행 상황 추적

---

**Status**: ✅ Phase 2 완료
**Next**: Phase 3 (구현 & 테스트 실행)
