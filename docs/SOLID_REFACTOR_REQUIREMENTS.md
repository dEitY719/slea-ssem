# SOLID 리팩토링 요구사항 - Answer Schema 처리 개선

**생성 일자**: 2025-11-24
**버전**: 1.0
**상태**: 작성 완료 (feature_requirement_mvp1.md 통합 대기)

---

## 개요

현재 `answer_schema` 포맷 처리가 Ad-hoc 방식으로 진행되어, 새로운 LLM 포맷 추가 시마다 기존 코드를 수정해야 합니다. 이는 SOLID 원칙(특히 Open/Closed 원칙)을 위반하며 반복되는 null 저장 버그를 야기합니다.

이 리팩토링은 **Transformer 패턴 + Value Object** 기반으로 타입 안정성과 유지보수성을 강화합니다.

---

## 요구사항 계층도

```
REQ-REFACTOR-SOLID-1: AnswerSchemaTransformer 클래스
    ├─ Agent 포맷 변환 (correct_keywords → keywords)
    ├─ Mock 포맷 변환 (correct_key → correct_answer)
    └─ 새로운 포맷 확장 가능 구조 (Open/Closed)

REQ-REFACTOR-SOLID-2: AnswerSchema Value Object
    ├─ 도메인 모델 정의 (타입 안전성)
    ├─ 팩토리 메서드 (from_agent_response, from_mock_data)
    └─ 변환 메서드 (to_db_dict, to_response_dict)

REQ-REFACTOR-SOLID-3: 포맷 문서화
    ├─ Agent 응답 포맷 정의
    ├─ Mock 포맷 정의
    ├─ Database 저장 포맷
    └─ 포맷 변환 플로우 다이어그램

REQ-REFACTOR-SOLID-4: 테스트 강화
    ├─ Transformer 테스트 (모든 포맷 조합)
    ├─ Value Object 테스트 (검증 로직)
    └─ Edge case 테스트 (null, empty, malformed)
```

---

## REQ-REFACTOR-SOLID-1: AnswerSchemaTransformer 클래스

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-REFACTOR-SOLID-1** | Agent 응답, Mock 데이터, Custom 포맷을 표준화된 AnswerSchema로 변환하는 확장 가능한 Transformer 패턴을 구현해야 한다. 새로운 포맷 추가 시 기존 코드 수정을 최소화하고 개방-폐쇄 원칙(Open/Closed)을 준수해야 한다. | **H** |

### Description

LLM Agent가 반환하는 `answer_schema` 형식이 다양하고(correct_keywords, correct_key, etc), 시간이 지남에 따라 새로운 형식이 추가될 수 있습니다. 현재는 각 서비스에서 포맷 변환 로직을 수동으로 처리하므로, 새로운 포맷 추가 시 여러 파일을 수정해야 합니다.

**Transformer 패턴** 기반으로 포맷별 변환 로직을 독립적인 클래스로 분리하면:
- 기존 변환 로직에 영향 없음 (Open/Closed 원칙)
- 새로운 포맷 추가 시 새 클래스만 구현 (Single Responsibility)
- 테스트 용이성 증대 (Dependency Inversion)

### 구현 위치

```
src/backend/models/answer_schema.py (신규 또는 기존 확장)
  ├─ class AnswerSchemaTransformer (추상 기본 클래스)
  │  └─ transform(raw_data: dict) → AnswerSchema
  │
  ├─ class AgentResponseTransformer(AnswerSchemaTransformer)
  │  └─ 변환 규칙: correct_keywords → keywords
  │
  ├─ class MockDataTransformer(AnswerSchemaTransformer)
  │  └─ 변환 규칙: correct_key → correct_answer
  │
  └─ class TransformerFactory
     └─ get_transformer(format_type: str) → AnswerSchemaTransformer
```

### 사용 예

```python
# AS-IS (현재 - Ad-hoc)
answer_schema = question_data.get("answer_schema", {})
if "correct_keywords" in answer_schema:
    keywords = answer_schema["correct_keywords"]
elif "correct_key" in answer_schema:
    keywords = answer_schema["correct_key"]
else:
    keywords = None
# 버그: keywords가 None으로 저장될 수 있음

# TO-BE (리팩토링 후)
from src.backend.models.answer_schema import AnswerSchemaTransformer, TransformerFactory

factory = TransformerFactory()
transformer = factory.get_transformer(format_type="agent_response")
answer_schema = transformer.transform(question_data.get("answer_schema", {}))
# Result: answer_schema는 항상 유효한 AnswerSchema 객체
```

### 기대 출력

**변환 전 (Raw Agent Response)**:
```json
{
  "question_id": "q_001",
  "answer_schema": {
    "correct_keywords": ["리튬이온", "배터리"],
    "explanation": "리튬이온 배터리는..."
  }
}
```

**변환 후 (Normalized AnswerSchema)**:
```python
AnswerSchema(
    question_type="short_answer",
    keywords=["리튬이온", "배터리"],
    explanation="리튬이온 배터리는...",
    source_format="agent_response"
)
```

**다양한 포맷 지원 예시**:
```python
# Agent 포맷
transformer = factory.get_transformer("agent_response")
schema = transformer.transform({
    "correct_keywords": ["answer1", "answer2"],
    "explanation": "..."
})

# Mock 포맷
transformer = factory.get_transformer("mock_data")
schema = transformer.transform({
    "correct_key": "answer",
    "explanation": "..."
})

# 향후 추가 포맷 (기존 코드 수정 불필요)
transformer = factory.get_transformer("custom_format")
schema = transformer.transform({...})
```

### 에러 케이스

- Invalid format type → `TransformerError: Unknown format type 'invalid'`
- Missing required field in raw_data → `ValidationError: Missing 'correct_keywords' in agent response`
- Malformed JSON structure → `TransformationError: Cannot parse answer_schema`
- Empty answer_schema dict → `ValidationError: answer_schema is empty`
- Type mismatch (expected list, got string) → `TypeValidationError: correct_keywords must be list, got str`

### Acceptance Criteria

- [ ] `AnswerSchemaTransformer` 추상 기본 클래스 구현 (transform 메서드)
- [ ] `AgentResponseTransformer` 구현 (correct_keywords → keywords)
- [ ] `MockDataTransformer` 구현 (correct_key → correct_answer)
- [ ] `TransformerFactory` 구현 (format_type으로 적절한 Transformer 선택)
- [ ] 모든 Transformer 클래스에 대한 단위 테스트 작성
- [ ] 새로운 포맷 추가 시 기존 코드 수정 불필요함을 검증
- [ ] type hints 및 docstring 완벽 (mypy strict 통과)
- [ ] question_gen_service, explain_service에서 변환 로직 교체

**Priority**: H
**Dependencies**:
- question_gen_service, explain_service (기존 코드)
- DatabaseModels (AnswerSchema 저장 구조)

**Status**: ⏳ Backlog
**Estimated Effort**: ~4-5 hours (구현 + 통합 + 테스트)

---

## REQ-REFACTOR-SOLID-2: AnswerSchema Value Object

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-REFACTOR-SOLID-2** | 다양한 포맷에서 변환된 answer_schema를 타입-안전한 Value Object로 정의하여, null 저장 버그를 방지하고 필드 접근을 일관되게 제공해야 한다. | **H** |

### Description

현재 `answer_schema`는 단순 dict로 다뤄지므로, 필드 존재 여부를 매번 확인해야 하고 타입 검증이 없습니다. 이로 인해 null 값이 DB에 저장되는 버그가 발생합니다.

**Value Object** 패턴으로 정의하면:
- 필드 검증 (생성 시점에 자동 실행)
- Immutable 객체 (의도치 않은 수정 방지)
- 타입 안전성 (mypy strict 모드)
- 도메인 언어로 표현 (keywords, explanation, source_format)

### 구현 위치

```
src/backend/models/answer_schema.py
  │
  └─ class AnswerSchema:
     ├─ fields:
     │  ├─ question_type: str (mc, short_answer, ox, etc)
     │  ├─ keywords: list[str] | None
     │  ├─ explanation: str
     │  ├─ source_format: str ("agent_response", "mock_data", ...)
     │  └─ created_at: datetime
     │
     ├─ @classmethod from_agent_response(data: dict) → AnswerSchema
     ├─ @classmethod from_mock_data(data: dict) → AnswerSchema
     ├─ @classmethod from_dict(data: dict, source: str) → AnswerSchema
     │
     ├─ def to_db_dict() → dict (데이터베이스 저장용)
     ├─ def to_response_dict() → dict (API 응답용)
     ├─ def __eq__, __hash__ (Value Object 패턴)
     │
     └─ @staticmethod validate(...) (검증 로직)
```

### 사용 예

```python
# AS-IS (현재)
answer_schema = {
    "correct_keywords": ["키워드1", "키워드2"],
    "explanation": "설명",
}
# 문제: dict이므로 필드 검증 없음, null 체크 필요

# TO-BE (리팩토링 후)
answer_schema = AnswerSchema.from_agent_response({
    "correct_keywords": ["키워드1", "키워드2"],
    "explanation": "설명",
})

# 타입 안전성
print(answer_schema.keywords)  # ["키워드1", "키워드2"] (자동 변환됨)
print(answer_schema.explanation)  # "설명"

# 데이터베이스 저장
db_dict = answer_schema.to_db_dict()
# {"keywords": [...], "explanation": "...", "source_format": "agent_response"}

# API 응답
api_dict = answer_schema.to_response_dict()
# {"keywords": [...], "explanation": "..."}  (source_format 제외)
```

### 기대 출력

**Value Object 생성 (from_agent_response)**:
```python
answer_schema = AnswerSchema.from_agent_response({
    "correct_keywords": ["배터리", "리튬이온"],
    "explanation": "리튬이온 배터리는 고에너지 밀도를 가진다.",
})

# 결과 (immutable)
answer_schema.keywords == ["배터리", "리튬이온"]
answer_schema.explanation == "리튬이온 배터리는..."
answer_schema.source_format == "agent_response"
```

**Value Object 생성 (from_mock_data)**:
```python
answer_schema = AnswerSchema.from_mock_data({
    "correct_key": "정답",
    "explanation": "이것이 정답이다.",
})

# 결과
answer_schema.keywords == ["정답"]  # correct_key → keywords로 변환
answer_schema.source_format == "mock_data"
```

**데이터베이스 저장 변환**:
```python
db_dict = answer_schema.to_db_dict()
# {
#   "keywords": ["배터리", "리튬이온"],
#   "explanation": "리튬이온 배터리는...",
#   "source_format": "agent_response",
#   "created_at": "2025-11-24T10:30:00Z"
# }

# DB에 저장
test_question.answer_schema = db_dict
session.commit()
```

### 에러 케이스

- Missing explanation → `ValidationError: 'explanation' is required`
- Empty keywords list (for short_answer) → `ValidationError: keywords cannot be empty for short_answer`
- Invalid question_type → `ValidationError: question_type must be one of [mc, short_answer, ox]`
- Non-string explanation → `TypeValidationError: explanation must be str, got int`
- Non-list keywords → `TypeValidationError: keywords must be list[str], got dict`

### Acceptance Criteria

- [ ] `AnswerSchema` dataclass (또는 BaseModel) 정의
- [ ] `from_agent_response()`, `from_mock_data()` 팩토리 메서드
- [ ] `to_db_dict()`, `to_response_dict()` 변환 메서드
- [ ] 필드 검증 로직 (Pydantic validator 또는 dataclass post_init)
- [ ] immutable 특성 (frozen=True 또는 @property)
- [ ] __eq__, __hash__ 구현 (Value Object)
- [ ] mypy strict 통과 (type hints 완벽)
- [ ] 모든 변환 메서드 단위 테스트
- [ ] test_question_gen_service에서 Value Object 사용 확인

**Priority**: H
**Dependencies**:
- REQ-REFACTOR-SOLID-1 (AnswerSchemaTransformer)
- Pydantic 또는 dataclasses (Python stdlib)

**Status**: ⏳ Backlog
**Estimated Effort**: ~3-4 hours (정의 + 검증 로직 + 테스트)

---

## REQ-REFACTOR-SOLID-3: 포맷 문서화 (ANSWER_SCHEMA_FORMATS.md)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-REFACTOR-SOLID-3** | Agent 응답 포맷, Mock 데이터 포맷, Database 저장 포맷을 명확히 문서화하고, 포맷 변환 플로우를 다이어그램으로 제시하여 향후 유지보수를 용이하게 해야 한다. | **M** |

### Description

현재 answer_schema 포맷이 명확히 문서화되어 있지 않아, 새로운 LLM 응답 형식이 나올 때마다 코드를 뒤져야 합니다. 이는 온보딩 시간을 증가시키고 버그의 원인이 됩니다.

**포맷 문서화**를 통해:
- 각 포맷의 예시 및 필드 설명
- 변환 규칙 명시 (correct_keywords → keywords)
- 플로우 다이어그램 (LLM → Transformer → Value Object → DB)
- 새로운 포맷 추가 체크리스트

### 생성할 문서

**파일**: `docs/ANSWER_SCHEMA_FORMATS.md`

### 문서 구성

```markdown
# Answer Schema Formats Guide

## 목차
1. Overview (포맷 다양성과 변환 필요성)
2. Agent Response Format (현재 LLM 응답 포맷)
3. Mock Data Format (테스트용 포맷)
4. Database Storage Format (DB에 저장되는 포맷)
5. Transformation Flow (변환 플로우 다이어그램)
6. Adding New Format (새로운 포맷 추가 체크리스트)
7. Examples (포맷별 예시)
8. Migration Guide (기존 코드 마이그레이션)
```

### 사용 예

문서의 "Transformation Flow" 섹션:
```
Agent Response (LLM 반환)
  {
    "correct_keywords": ["배터리", "리튬"],
    "explanation": "..."
  }
        ↓
AgentResponseTransformer.transform()
        ↓
AnswerSchema Value Object
  {
    keywords: ["배터리", "리튬"],
    explanation: "...",
    source_format: "agent_response"
  }
        ↓
answer_schema.to_db_dict()
        ↓
Database
  {
    keywords: ["배터리", "리튬"],
    explanation: "...",
    source_format: "agent_response"
  }
```

### 기대 출력

**문서 예시 섹션**:
```markdown
### Example 1: Agent Response Format

Raw LLM Response:
```json
{
  "question_id": "q_001",
  "answer_schema": {
    "correct_keywords": ["리튬", "배터리"],
    "explanation": "리튬이온 배터리는..."
  }
}
```

Transformation:
```python
transformer = factory.get_transformer("agent_response")
schema = transformer.transform(
    {"correct_keywords": ["리튬", "배터리"], ...}
)
```

Result (AnswerSchema):
```python
AnswerSchema(
    keywords=["리튬", "배터리"],
    explanation="리튬이온 배터리는...",
    source_format="agent_response"
)
```
```

### 에러 케이스

- 문서가 최신 포맷과 불일치 → 주기적 검토 필요
- 예시 코드가 작동하지 않음 → CI/CD에서 문서 예시 검증 (선택사항)

### Acceptance Criteria

- [ ] `docs/ANSWER_SCHEMA_FORMATS.md` 작성 (2000+ 단어)
- [ ] Agent 응답 포맷 예시 (3+ 사례)
- [ ] Mock 데이터 포맷 예시 (3+ 사례)
- [ ] Database 저장 포맷 스키마
- [ ] 변환 플로우 다이어그램 (Mermaid 또는 ASCII)
- [ ] 새로운 포맷 추가 체크리스트 (5+ 항목)
- [ ] 기존 코드 마이그레이션 예시 (AS-IS → TO-BE)
- [ ] 프로젝트 README.md에서 링크 추가

**Priority**: M
**Dependencies**:
- REQ-REFACTOR-SOLID-1, REQ-REFACTOR-SOLID-2 (완성 후 문서화)

**Status**: ⏳ Backlog
**Estimated Effort**: ~2-3 hours (문서 작성 + 검증)

---

## REQ-REFACTOR-SOLID-4: 테스트 강화 (test_answer_schema_transformers.py)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-REFACTOR-SOLID-4** | Transformer 및 Value Object의 모든 포맷 조합, 검증 로직, Edge case에 대한 포괄적 단위 테스트를 작성하여, 변환 신뢰성을 보장해야 한다. | **H** |

### Description

SOLID 리팩토링의 효과를 검증하려면 다양한 포맷, 엣지 케이스, 에러 조건에 대한 체계적인 테스트가 필요합니다. 이를 통해:
- Transformer 신뢰성 검증
- 새로운 포맷 추가 시 회귀 방지
- 문서 또는 예시 코드의 정확성 확인

### 테스트 파일

**파일**: `tests/backend/test_answer_schema_transformers.py`

### 테스트 구조

```python
class TestAnswerSchemaTransformer:
    # ✅ Happy Path (정상 변환)
    def test_agent_response_transformer_basic()
    def test_mock_data_transformer_basic()
    def test_custom_format_transformer_basic()

    # ❌ Input Validation (입력 검증)
    def test_agent_response_missing_required_field()
    def test_mock_data_empty_dict()
    def test_invalid_format_type()

    # 🔀 Edge Cases (엣지 케이스)
    def test_empty_keywords_list()
    def test_null_explanation()
    def test_unicode_characters_in_keywords()
    def test_very_long_explanation()

    # ⚙️ Type Validation (타입 검증)
    def test_keywords_must_be_list()
    def test_explanation_must_be_string()
    def test_source_format_must_be_string()

class TestAnswerSchemaValueObject:
    # ✅ Creation & Conversion (생성 & 변환)
    def test_create_from_agent_response()
    def test_create_from_mock_data()
    def test_to_db_dict()
    def test_to_response_dict()

    # 🔒 Immutability (불변성)
    def test_frozen_object()
    def test_cannot_modify_keywords()

    # 🔄 Equality & Hashing (동등성 & 해시)
    def test_value_objects_with_same_data_equal()
    def test_value_objects_can_be_hashed()

    # 🧪 Integration (통합)
    def test_transformer_to_value_object_pipeline()
    def test_question_gen_service_with_value_object()

class TestTransformerFactory:
    # 🎯 Factory Pattern
    def test_get_agent_response_transformer()
    def test_get_mock_data_transformer()
    def test_unknown_format_type_raises_error()
```

### 사용 예

```python
def test_agent_response_transformer_basic():
    """Agent 응답 포맷 정상 변환"""
    raw_data = {
        "correct_keywords": ["배터리", "리튬"],
        "explanation": "리튬이온 배터리는..."
    }

    transformer = AgentResponseTransformer()
    result = transformer.transform(raw_data)

    assert result.keywords == ["배터리", "리튬"]
    assert result.explanation == "리튬이온 배터리는..."
    assert result.source_format == "agent_response"

def test_value_object_immutability():
    """AnswerSchema Value Object는 불변"""
    answer_schema = AnswerSchema.from_agent_response({
        "correct_keywords": ["a", "b"],
        "explanation": "설명"
    })

    # frozen=True이므로 수정 불가
    with pytest.raises(FrozenInstanceError):
        answer_schema.keywords = ["c", "d"]

def test_integration_question_gen_service():
    """QuestionGenerationService에서 Value Object 사용"""
    # Mock Agent 응답
    agent_response = {
        "questions": [
            {
                "answer_schema": {
                    "correct_keywords": ["답"],
                    "explanation": "설명"
                }
            }
        ]
    }

    service = QuestionGenerationService()
    questions = service.process_agent_response(agent_response)

    # AnswerSchema Value Object로 변환됨
    assert isinstance(questions[0].answer_schema, AnswerSchema)
    assert questions[0].answer_schema.keywords == ["답"]
```

### 기대 출력

**테스트 실행 결과**:
```bash
$ pytest tests/backend/test_answer_schema_transformers.py -v

test_answer_schema_transformers.py::TestAnswerSchemaTransformer::test_agent_response_transformer_basic PASSED
test_answer_schema_transformers.py::TestAnswerSchemaTransformer::test_mock_data_transformer_basic PASSED
test_answer_schema_transformers.py::TestAnswerSchemaTransformer::test_agent_response_missing_required_field PASSED
test_answer_schema_transformers.py::TestAnswerSchemaValueObject::test_create_from_agent_response PASSED
test_answer_schema_transformers.py::TestAnswerSchemaValueObject::test_to_db_dict PASSED
test_answer_schema_transformers.py::TestAnswerSchemaValueObject::test_frozen_object PASSED
test_answer_schema_transformers.py::TestAnswerSchemaValueObject::test_value_objects_with_same_data_equal PASSED
test_answer_schema_transformers.py::TestTransformerFactory::test_get_agent_response_transformer PASSED
test_answer_schema_transformers.py::TestTransformerFactory::test_unknown_format_type_raises_error PASSED

========================== 9 passed in 0.32s ==========================
```

**테스트 커버리지**:
```
answer_schema.py   ............ 100%
transformer.py     ............ 100%
factory.py         ............ 100%

Total Coverage: 100%
```

### 에러 케이스

- 테스트가 기존 코드와 불일치 → 테스트 우선 개발 (TDD)
- Edge case 누락 → Code review에서 추가 테스트 요청
- 테스트 실행 시간 과다 → Mocking으로 최적화

### Acceptance Criteria

- [ ] `tests/backend/test_answer_schema_transformers.py` 작성
- [ ] Happy path 테스트 (각 포맷 3+ 사례)
- [ ] Input validation 테스트 (6+ 사례)
- [ ] Edge case 테스트 (10+ 사례)
- [ ] Type validation 테스트 (5+ 사례)
- [ ] Immutability 테스트 (3+ 사례)
- [ ] Factory pattern 테스트 (3+ 사례)
- [ ] 통합 테스트 (question_gen_service + Transformer)
- [ ] 전체 테스트 커버리지 ≥ 95%
- [ ] 모든 테스트 3초 내 완료
- [ ] mypy strict 통과

**Priority**: H
**Dependencies**:
- REQ-REFACTOR-SOLID-1, REQ-REFACTOR-SOLID-2 (완성 후 테스트)
- pytest, pytest-cov

**Status**: ⏳ Backlog
**Estimated Effort**: ~3-4 hours (테스트 작성 + 검증)

---

## 통합 이행 계획

### Phase 1: 설계 & 검토 (1 hour)
- REQ-REFACTOR-SOLID-1,2,3,4 설계 검토
- Architecture Decision Record (ADR) 작성 (선택사항)
- 팀 동의 확보

### Phase 2: 구현 (8-10 hours)
1. REQ-REFACTOR-SOLID-1: AnswerSchemaTransformer (4-5 hours)
2. REQ-REFACTOR-SOLID-2: AnswerSchema Value Object (3-4 hours)
3. REQ-REFACTOR-SOLID-3: 문서화 (2-3 hours)
4. REQ-REFACTOR-SOLID-4: 테스트 (3-4 hours)

### Phase 3: 통합 (2-3 hours)
- question_gen_service 리팩토링 (새 Value Object 사용)
- explain_service 리팩토링
- 기존 테스트 업데이트
- `tox -e py311` 전체 테스트 통과 확인

### Phase 4: 리뷰 & 완성 (1-2 hours)
- Code review
- 문서 최종 검토
- Commit & PR

**총 예상 시간**: ~12-16 hours (4일 개발)

---

## 성공 지표

| 지표 | 현재 | 목표 |
|------|------|------|
| 새로운 포맷 추가 시 수정 필요한 파일 | 3-5개 | 1개 (Transformer만) |
| Answer schema null 저장 버그 | 반복 발생 | 0 |
| 타입 안정성 (mypy strict) | 일부 | 100% |
| 테스트 커버리지 | ~70% | ≥95% |
| 코드 리뷰 피드백 (null checks) | 많음 | 없음 |

---

## 참고 자료

- SOLID 원칙: Open/Closed, Single Responsibility, Dependency Inversion
- Transformer 패턴: 데이터 변환 로직 분리
- Value Object 패턴: 불변 도메인 모델
- Pydantic 라이브러리: Python 데이터 검증

---

## 다음 단계

1. 이 요구사항 문서를 `docs/feature_requirement_mvp1.md`에 추가
2. `docs/feature_requirement_mvp1.md`에서 REQ-REFACTOR-SOLID-1~4 섹션 생성
3. `docs/DEV-PROGRESS.md`에서 진행률 추적
4. 팀 동의 후 Phase 1부터 시작
