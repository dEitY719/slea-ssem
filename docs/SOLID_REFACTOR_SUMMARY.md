# SOLID 리팩토링 요구사항 - 요약 및 실행 가이드

**작성일**: 2025-11-24
**상태**: 준비 완료 (feature_requirement_mvp1.md에 통합됨)
**다음 단계**: 팀 검토 후 Phase 1 시작

---

## 개요

현재 **answer_schema** 포맷 처리의 기술부채를 SOLID 원칙 기반의 구조적 개선으로 해결합니다.

### 문제점 (AS-IS)
```python
# 현재: Ad-hoc 처리
answer_schema = question_data.get("answer_schema", {})
if "correct_keywords" in answer_schema:
    keywords = answer_schema["correct_keywords"]
elif "correct_key" in answer_schema:
    keywords = answer_schema["correct_key"]
else:
    keywords = None  # BUG: null이 DB에 저장될 수 있음
```

**문제**:
- 새로운 포맷 추가 시 여러 파일 수정 필요 (Open/Closed 원칙 위반)
- 필드 검증 없음 (타입 안전성 부재)
- 반복되는 null 저장 버그

### 솔루션 (TO-BE)
```python
# 개선: Transformer + Value Object 패턴
factory = TransformerFactory()
transformer = factory.get_transformer(format_type="agent_response")
answer_schema = transformer.transform(raw_data)
# Result: 항상 유효한 AnswerSchema 객체, null 불가능

# 새로운 포맷 추가: 기존 코드 수정 불필요
class CustomTransformer(AnswerSchemaTransformer):
    def transform(self, raw_data: dict) -> AnswerSchema:
        # 새로운 포맷 처리
        pass
```

**개선점**:
- Open/Closed 원칙: 새로운 포맷 추가 시 확장만 가능 (수정 불가)
- Single Responsibility: 포맷별 Transformer 클래스 분리
- Dependency Inversion: Factory 패턴으로 의존성 역전
- 타입 안전성: Value Object로 필드 검증
- 테스트 용이성: 포맷별 독립적 테스트

---

## 4개 요구사항 (REQ-REFACTOR-SOLID-1~4)

### 1️⃣ REQ-REFACTOR-SOLID-1: Transformer 클래스
**목표**: 포맷별 변환 로직을 독립적 클래스로 분리

```python
# 구현 위치: src/backend/models/answer_schema.py

# 추상 기본 클래스
class AnswerSchemaTransformer(ABC):
    @abstractmethod
    def transform(self, raw_data: dict) -> AnswerSchema:
        pass

# Agent 응답 변환: correct_keywords → keywords
class AgentResponseTransformer(AnswerSchemaTransformer):
    def transform(self, raw_data: dict) -> AnswerSchema:
        keywords = raw_data["correct_keywords"]  # 자동 변환
        explanation = raw_data["explanation"]
        return AnswerSchema(
            keywords=keywords,
            explanation=explanation,
            source_format="agent_response"
        )

# Mock 데이터 변환: correct_key → keywords
class MockDataTransformer(AnswerSchemaTransformer):
    def transform(self, raw_data: dict) -> AnswerSchema:
        keywords = [raw_data["correct_key"]]  # List로 변환
        return AnswerSchema(
            keywords=keywords,
            explanation=raw_data["explanation"],
            source_format="mock_data"
        )

# Factory: 포맷별 Transformer 선택
class TransformerFactory:
    def get_transformer(self, format_type: str) -> AnswerSchemaTransformer:
        transformers = {
            "agent_response": AgentResponseTransformer(),
            "mock_data": MockDataTransformer(),
        }
        if format_type not in transformers:
            raise TransformerError(f"Unknown format: {format_type}")
        return transformers[format_type]
```

**우선순위**: HIGH
**예상 소요 시간**: 4-5 hours

---

### 2️⃣ REQ-REFACTOR-SOLID-2: Value Object 정의
**목표**: 타입-안전한 AnswerSchema 도메인 모델 정의

```python
# src/backend/models/answer_schema.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)  # Immutable
class AnswerSchema:
    """Answer schema value object"""

    question_type: str  # mc, short_answer, ox
    keywords: Optional[list[str]]  # 변환된 키워드
    explanation: str  # 필수
    source_format: str  # agent_response, mock_data
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Factory Methods
    @classmethod
    def from_agent_response(cls, data: dict) -> "AnswerSchema":
        """Agent 응답 -> AnswerSchema"""
        cls._validate(data, source="agent_response")
        keywords = data.get("correct_keywords", [])
        return cls(
            question_type=data.get("question_type", "short_answer"),
            keywords=keywords,
            explanation=data["explanation"],
            source_format="agent_response"
        )

    @classmethod
    def from_mock_data(cls, data: dict) -> "AnswerSchema":
        """Mock 데이터 -> AnswerSchema"""
        cls._validate(data, source="mock_data")
        keywords = [data["correct_key"]]  # List로 변환
        return cls(
            question_type=data.get("question_type", "short_answer"),
            keywords=keywords,
            explanation=data["explanation"],
            source_format="mock_data"
        )

    # Conversion Methods
    def to_db_dict(self) -> dict:
        """데이터베이스 저장용"""
        return {
            "keywords": self.keywords,
            "explanation": self.explanation,
            "source_format": self.source_format,
            "created_at": self.created_at.isoformat()
        }

    def to_response_dict(self) -> dict:
        """API 응답용 (source_format 제외)"""
        return {
            "keywords": self.keywords,
            "explanation": self.explanation
        }

    # Validation
    @staticmethod
    def _validate(data: dict, source: str) -> None:
        """포맷별 검증"""
        required_fields = {
            "agent_response": ["correct_keywords", "explanation"],
            "mock_data": ["correct_key", "explanation"]
        }

        for field in required_fields[source]:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        # Type validation
        if not isinstance(data.get("explanation"), str):
            raise TypeValidationError("explanation must be str")

    # Value Object Pattern
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AnswerSchema):
            return NotImplemented
        return (
            self.keywords == other.keywords and
            self.explanation == other.explanation and
            self.source_format == other.source_format
        )

    def __hash__(self) -> int:
        keywords_tuple = tuple(self.keywords) if self.keywords else None
        return hash((self.question_type, keywords_tuple, self.explanation, self.source_format))
```

**우선순위**: HIGH
**예상 소요 시간**: 3-4 hours

---

### 3️⃣ REQ-REFACTOR-SOLID-3: 포맷 문서화
**목표**: Answer Schema 포맷을 명확히 문서화

**생성 문서**: `docs/ANSWER_SCHEMA_FORMATS.md` (2000+ 단어)

**포함 내용**:
- Agent 응답 포맷 정의 및 3+ 예시
- Mock 데이터 포맷 정의 및 3+ 예시
- Database 저장 포맷 스키마
- 변환 플로우 다이어그램

**예시 구조**:
```markdown
# Answer Schema Formats

## Agent Response Format
### 형식 정의
```json
{
  "question_id": "q_001",
  "answer_schema": {
    "correct_keywords": ["키워드1", "키워드2"],
    "explanation": "설명 텍스트"
  }
}
```

### 예시 1: 짧은 답 (Short Answer)
...

### 예시 2: 객관식 (MC)
...

## Mock Data Format
...

## Database Storage Format
...

## Transformation Flow Diagram
...

## 새로운 포맷 추가 체크리스트
- [ ] Transformer 클래스 작성
- [ ] 테스트 케이스 추가
- [ ] 문서 업데이트
- [ ] Factory에 등록
```

**우선순위**: MEDIUM
**예상 소요 시간**: 2-3 hours

---

### 4️⃣ REQ-REFACTOR-SOLID-4: 테스트 강화
**목표**: Transformer & Value Object의 신뢰성 검증

**테스트 파일**: `tests/backend/test_answer_schema_transformers.py`

**테스트 구조**:
```python
class TestAnswerSchemaTransformer:
    # ✅ Happy path (정상 케이스)
    def test_agent_response_transformer_basic(self)
    def test_mock_data_transformer_basic(self)

    # ❌ Input validation (입력 검증)
    def test_agent_response_missing_required_field(self)
    def test_mock_data_empty_dict(self)
    def test_invalid_format_type(self)

    # 🔀 Edge cases (엣지 케이스)
    def test_empty_keywords_list(self)
    def test_unicode_characters_in_keywords(self)
    def test_very_long_explanation(self)

    # ⚙️ Type validation (타입 검증)
    def test_keywords_must_be_list(self)
    def test_explanation_must_be_string(self)

class TestAnswerSchemaValueObject:
    # ✅ Creation & conversion
    def test_create_from_agent_response(self)
    def test_to_db_dict(self)
    def test_to_response_dict(self)

    # 🔒 Immutability
    def test_frozen_object(self)
    def test_cannot_modify_keywords(self)

    # 🔄 Equality & hashing
    def test_value_objects_with_same_data_equal(self)
    def test_value_objects_can_be_hashed(self)

class TestTransformerFactory:
    def test_get_agent_response_transformer(self)
    def test_unknown_format_type_raises_error(self)

class TestIntegration:
    def test_question_gen_service_with_value_object(self)
```

**예상 결과**:
```
$ pytest tests/backend/test_answer_schema_transformers.py -v
========================== 25 passed in 1.50s ==========================
Coverage: 98% (answer_schema.py)
```

**우선순위**: HIGH
**예상 소요 시간**: 3-4 hours

---

## 통합 이행 일정

### Phase 1: 설계 & 검토 (1 hour)
- 팀 리뷰 (this document + SOLID_REFACTOR_REQUIREMENTS.md)
- 의견 수렴 및 최종 승인

### Phase 2: 구현 (8-10 hours)
```
Day 1 (4-5 hours):
  ├─ REQ-REFACTOR-SOLID-1: Transformer 클래스 (4-5 hours)
  └─ 단위 테스트 작성

Day 2 (3-4 hours):
  ├─ REQ-REFACTOR-SOLID-2: Value Object (3-4 hours)
  └─ 통합 테스트

Day 2 (2-3 hours):
  ├─ REQ-REFACTOR-SOLID-3: 문서화 (2-3 hours)
  └─ 기존 코드 마이그레이션 예시 작성

Day 3 (3-4 hours):
  ├─ REQ-REFACTOR-SOLID-4: 테스트 강화 (3-4 hours)
  └─ 엣지 케이스 검증
```

### Phase 3: 통합 & 검증 (2-3 hours)
```
- question_gen_service 리팩토링
  (기존 dict 처리 → Value Object 사용)

- explain_service 리팩토링
  (기존 dict 처리 → Value Object 사용)

- 전체 테스트 실행
  $ tox -e py311          # 모든 테스트 통과 확인
  $ tox -e mypy           # Type hints 검증

- 기존 테스트 업데이트
  (test_question_gen_service, test_explain_service)
```

### Phase 4: 리뷰 & 완성 (1-2 hours)
```
- Code review (GitHub PR)
- 문서 최종 검토
- Git commit & merge

Commit message:
  refactor: Implement SOLID Answer Schema transformation

  - Add AnswerSchemaTransformer pattern (REQ-REFACTOR-SOLID-1)
  - Define AnswerSchema Value Object (REQ-REFACTOR-SOLID-2)
  - Document answer_schema formats (REQ-REFACTOR-SOLID-3)
  - Add comprehensive tests (REQ-REFACTOR-SOLID-4)

  Fixes repeated null storage bugs
  Improves type safety and extensibility

  Generated with Claude Code
  Co-Authored-By: Claude <noreply@anthropic.com>
```

**총 예상 시간**: 12-16 hours (3-4일 개발)

---

## 성공 지표

| 지표 | 현재 | 목표 | 목표 달성 시 효과 |
|------|------|------|---------|
| 새로운 포맷 추가 시 수정 파일 수 | 3-5개 | 1개 (Transformer만) | 개발 시간 70% 감소 |
| Answer schema null 저장 버그 | 반복 발생 | 0 | 버그 수정 시간 제거 |
| 타입 안전성 (mypy strict) | 일부 | 100% | Type hint 오류 사전 방지 |
| 테스트 커버리지 | ~70% | ≥95% | 회귀 버그 감소 |
| 코드 리뷰 피드백 (null check) | 매 PR마다 | 없음 | PR 검토 시간 단축 |
| Onboarding 시간 | ~2시간 | ~30분 | 신규 팀원 입문 가속 |

---

## 사용 시작

### 구현 시작 전 체크리스트
- [ ] 이 문서 읽기 완료
- [ ] `docs/SOLID_REFACTOR_REQUIREMENTS.md` 검토
- [ ] `docs/feature_requirement_mvp1.md` 의 REQ-REFACTOR-SOLID-1~4 확인
- [ ] 팀 리뷰 및 승인 완료

### 개발 단계별 명령어
```bash
# 1. feature 브랜치 생성
git checkout -b refactor/answer-schema-solid

# 2. REQ-REFACTOR-SOLID-1 구현
# src/backend/models/answer_schema.py 작성

# 3. 테스트 작성 (TDD)
# tests/backend/test_answer_schema_transformers.py 작성

# 4. 형식/린트 검증
./tools/dev.sh format  # ruff, black, mypy, pylint

# 5. 테스트 실행
./tools/dev.sh test
# or
pytest tests/backend/test_answer_schema_transformers.py -v

# 6. 기존 서비스 리팩토링
# src/backend/services/question_gen_service.py 수정
# src/backend/services/explain_service.py 수정

# 7. 통합 테스트
tox -e py311

# 8. Commit
./tools/commit.sh
# or
git add .
git commit -m "refactor: Implement SOLID Answer Schema transformation"

# 9. PR 생성
gh pr create --title "refactor: SOLID Answer Schema transformation"
```

---

## 참고 자료

### SOLID 원칙 (이 리팩토링에서 적용)
- **Single Responsibility**: 포맷별 Transformer 클래스 분리
- **Open/Closed**: 새로운 포맷 추가 시 확장만 가능 (기존 코드 수정 불필요)
- **Liskov Substitution**: 모든 Transformer가 AnswerSchemaTransformer 인터페이스 구현
- **Interface Segregation**: Transformer 기본 인터페이스 간결 (transform만 필요)
- **Dependency Inversion**: Factory 패턴으로 의존성 역전

### 디자인 패턴
- **Transformer Pattern**: 포맷별 변환 로직 분리
- **Value Object**: 불변 도메인 모델 (null 불가능)
- **Factory Pattern**: 포맷별 Transformer 선택

### 프로젝트 문서
- `docs/SOLID_REFACTOR_REQUIREMENTS.md`: 상세 요구사항
- `docs/feature_requirement_mvp1.md`: REQ-REFACTOR-SOLID-1~4 (통합됨)

---

## FAQ

### Q1: 왜 지금 이 리팩토링을 해야 하나?
**A**: 반복되는 null 저장 버그, 새로운 포맷 추가 시마다 기존 코드 수정, 타입 검증 부재 등 기술부채 축적. 지금 해결하면 향후 유지보수 비용 70% 감소.

### Q2: 기존 코드와의 호환성은?
**A**: Phase 3에서 question_gen_service, explain_service를 새 Value Object로 리팩토링하므로, 점진적 마이그레이션 가능. 기존 API는 변경 없음.

### Q3: 테스트 기간은?
**A**: 25개 테스트 케이스, 예상 실행 시간 1.5초 이내. 모든 테스트는 통합 테스트 전에 통과해야 함.

### Q4: 문서화는 몇 시간?
**A**: 약 2-3시간. 포맷별 예시 3+, 다이어그램, 마이그레이션 가이드 포함.

### Q5: 향후 새로운 포맷 추가 시 얼마나 걸리나?
**A**: Transformer 클래스 + 테스트만 추가하면 됨. 예상 시간: 30분 (기존: 2-3시간)

---

**다음 단계**: 팀 리뷰 후 Phase 1 시작
**연락처**: 개발팀 또는 Architecture 리드
**상태**: 준비 완료 (2025-11-24)
