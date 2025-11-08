# REQ-A-Mode1-Tool2: Phase 1 - Specification

**작성일**: 2025-11-09
**단계**: Phase 1 (📝 Specification)
**상태**: Specification 작성 완료, 검토 대기

---

## 📋 Phase 1: SPECIFICATION

### 1.1 요구사항 분석

#### 기능 개요

**REQ-A-Mode1-Tool2: Search Question Templates**

Tool 2는 질문 생성 파이프라인의 두 번째 단계에서 사용되는 도구입니다.

사용자의 관심분야, 난이도, 카테고리에 맞는 기존 문항 템플릿을 데이터베이스에서 검색하여 반환합니다. 이 템플릿들은 LLM 프롬프트의 few-shot 예시로 활용되어 생성 문항의 품질을 향상시킵니다.

**역할**:

- Mode 1 파이프라인에서 Tool 1(사용자 프로필 조회) 이후 실행
- Tool 3(난이도 키워드 조회)로 진행하기 전에 문항 템플릿 제공
- 검색 결과 없을 경우 gracefully skip

#### 우선순위 & 스코프

| 항목 | 값 |
|------|-----|
| **REQ ID** | REQ-A-Mode1-Tool2 |
| **우선순위** | Must (M) |
| **영역** | Mode 1 - 문항 생성 파이프라인 |
| **스코프** | 템플릿 검색 로직만 (생성은 Tool 4-5 담당) |
| **MVP** | 1.0 |
| **BacklogSize** | 5개 sub-tasks |

---

### 1.2 입력 명세

#### 입력 데이터 구조

```python
{
    "interests": ["LLM", "RAG", "Agent Architecture"],  # 사용자 관심분야 (Tool 1 출력)
    "difficulty": 7,  # 난이도 (1-10, Tool 1 context + 현재 라운드 정보)
    "category": "technical"  # 상위 카테고리 (technical, business, general)
}
```

#### 입력 필드 정의

| 필드 | 타입 | 필수 | 설명 | 유효성 검증 |
|------|------|------|------|-----------|
| `interests` | `list[str]` | ✓ | 사용자 관심분야 목록 | 1-10개 문자열, 각 1-50글자 |
| `difficulty` | `int` | ✓ | 난이도 레벨 | 1-10 범위 |
| `category` | `str` | ✓ | 상위 카테고리 | "technical"\|"business"\|"general" |

#### 입력 검증 규칙

1. **interests**:
   - 타입: list[str]
   - 길이: 1-10개 요소
   - 각 요소: 1-50글자, 공백 제거 후 검증
   - 빈 리스트: ValueError 발생

2. **difficulty**:
   - 타입: int
   - 범위: 1-10 포함
   - float 입력: int로 변환 후 검증
   - 범위 밖: ValueError 발생

3. **category**:
   - 타입: str
   - 허용값: "technical", "business", "general"
   - 대소문자 구분: 소문자 통일 후 검증
   - 미지원 카테고리: ValueError 발생

---

### 1.3 출력 명세

#### 출력 데이터 구조

```python
[
    {
        "id": "tmpl_550e8400_e29b_41d4_a716_446655440001",
        "stem": "다음 중 LLM의 특징으로 가장 적절한 것은?",
        "type": "multiple_choice",  # "multiple_choice" | "true_false" | "short_answer"
        "choices": [
            "A) 미리 정의된 규칙만 사용하는 프로그래밍 언어",
            "B) 대규모 텍스트 데이터로 학습된 신경망 모델",
            "C) 데이터베이스 관리 시스템",
            "D) 웹 서버의 일종"
        ],
        "correct_answer": "B",  # 정답 키
        "correct_rate": 0.78,  # 0.0-1.0, 이 템플릿으로 생성한 문항의 정답률
        "usage_count": 45,  # 지금까지 사용된 횟수
        "avg_difficulty_score": 7.2  # 템플릿의 실제 평균 난이도
    },
    # ... 최대 10개
]
```

#### 출력 필드 정의

| 필드 | 타입 | 설명 | 비고 |
|------|------|------|------|
| `id` | `str` | 템플릿 UUID | 데이터베이스의 question_templates.id |
| `stem` | `str` | 문항 내용 | 100-500글자 |
| `type` | `str` | 문항 유형 | 3가지 타입 중 하나 |
| `choices` | `list[str]` | 선택지 (MC/TF만) | 2-5개, 각 20-200글자 |
| `correct_answer` | `str` | 정답 | "A"-"E" or "True"-"False" or 키워드 |
| `correct_rate` | `float` | 정답률 | 0.0-1.0 범위 |
| `usage_count` | `int` | 사용 횟수 | >= 0 |
| `avg_difficulty_score` | `float` | 평균 난이도 | 0.0-10.0 범위 |

#### 출력 검증

- 빈 리스트는 성공 응답 (검색 결과 없음 = Tool 3으로 진행)
- 최대 10개 템플릿 반환 (초과 시 상위 10개로 제한)
- 모든 필드가 존재해야 함 (NULL 불가)

---

### 1.4 동작 명세

#### 4.1 검색 로직

```
Input: interests[], difficulty, category
│
├─ 1단계: 입력 검증
│  ├─ interests 검증 (길이, 타입, 문자열 유효성)
│  ├─ difficulty 검증 (1-10 범위)
│  └─ category 검증 (허용값 확인)
│
├─ 2단계: 데이터베이스 쿼리
│  ├─ question_templates 테이블 쿼리
│  ├─ 필터 조건:
│  │  ├─ category = input.category (정확 매칭)
│  │  ├─ domain IN interests[] (interests 중 하나라도 포함)
│  │  ├─ ABS(avg_difficulty_score - input.difficulty) <= 1.5 (난이도 범위)
│  │  ├─ usage_count > 0 (최소 1회 이상 사용)
│  │  └─ is_active = true (활성 템플릿만)
│  ├─ 정렬: correct_rate DESC, usage_count DESC
│  └─ LIMIT 10 (최대 10개)
│
├─ 3단계: 검색 결과 처리
│  ├─ 결과 있음: 필드 매핑 후 반환
│  ├─ 결과 없음: 빈 리스트 반환 (에러 아님)
│  └─ DB 에러: 에러 처리 (아래 참고)
│
└─ Output: list[dict] (0-10개)
```

#### 4.2 컨텍스트 통합

Tool 2는 Tool 1의 출력을 입력으로 받습니다:

```python
# Tool 1 (Get User Profile) 출력
tool1_output = {
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "self_level": "intermediate",
    "years_experience": 5,
    "job_role": "Backend Engineer",
    "duty": "API development",
    "interests": ["LLM", "RAG", "Agent Architecture"],  # ← Tool 2 입력으로 사용
    "previous_score": 75
}

# Tool 2 입력 (Tool 1 출력 + 파이프라인 context)
tool2_input = {
    "interests": tool1_output["interests"],  # 재사용
    "difficulty": 7,  # 현재 라운드의 난이도 (별도 context)
    "category": "technical"  # 카테고리 (별도 context)
}
```

---

### 1.5 에러 처리

#### 5.1 입력 검증 에러

| 에러 시나리오 | 입력 | 예외 | 처리 방식 | 파이프라인 진행 |
|-------------|------|------|---------|-----------|
| 1. interests 빈 리스트 | `interests=[]` | ValueError | 로그 + 예외 발생 | 중단 |
| 2. interests 타입 오류 | `interests="LLM"` | TypeError | 로그 + 예외 발생 | 중단 |
| 3. difficulty 범위 초과 | `difficulty=11` | ValueError | 로그 + 예외 발생 | 중단 |
| 4. difficulty 타입 오류 | `difficulty="7"` | TypeError | 로그 + 예외 발생 | 중단 |
| 5. category 미지원 | `category="unknown"` | ValueError | 로그 + 예외 발생 | 중단 |

#### 5.2 데이터베이스 에러

| 에러 시나리오 | 예외 | 처리 방식 | 반환값 |
|-------------|------|---------|--------|
| 1. DB 연결 실패 | OperationalError | 로그 기록 | `[]` (빈 리스트) |
| 2. 쿼리 타임아웃 | TimeoutError | 로그 기록 | `[]` (빈 리스트) |
| 3. 임시 DB 오류 | Exception | 로그 기록 | `[]` (빈 리스트) |

#### 5.3 에러 처리 원칙

- **입력 에러**: 예외 발생 (파이프라인에서 재시도 또는 폐기)
- **검색 결과 없음**: 에러 아님, 빈 리스트 반환 (Tool 3으로 진행)
- **DB 에러**: 빈 리스트 반환 (graceful degradation, 파이프라인은 계속 진행)
- **로깅**: 모든 에러는 DEBUG/WARNING/ERROR 레벨로 기록

---

### 1.6 성능 요구사항

| 요구사항 | 목표값 | 설명 |
|---------|--------|------|
| **응답 시간** | < 500ms | DB 쿼리 + 필드 매핑 포함 |
| **최대 결과 수** | 10개 | 쿼리 성능 & 메모리 제약 |
| **동시 요청** | 10+ / sec | 멀티스레드 안전성 |
| **캐싱** | 선택사항 | Tool 2는 캐싱 미포함 (Tool 3에서 구현) |

---

### 1.7 보안 요구사항

| 요구사항 | 구현 |
|---------|------|
| **입력 검증** | 모든 입력값 타입/길이/범위 검증 |
| **SQL 주입 방지** | SQLAlchemy ORM 사용 (raw SQL 없음) |
| **데이터 유출 방지** | 요청한 사용자만 결과 접근 (인증은 API 레이어) |
| **로깅** | 민감 정보 제외 (키워드, 정답 미기록) |

---

### 1.8 Acceptance Criteria

#### AC1: 유효한 입력으로 검색 결과 반환

**Given**: 유효한 interests[], difficulty, category 제공
**When**: search_question_templates() 호출
**Then**:

- 결과는 리스트 타입
- 각 결과 객체는 필수 필드 모두 포함 (id, stem, type, choices, correct_answer, correct_rate, usage_count, avg_difficulty_score)
- 최대 10개 항목
- correct_rate로 내림차순 정렬

#### AC2: 검색 결과 없을 경우 빈 리스트 반환

**Given**: 데이터베이스에 일치하는 템플릿 없음
**When**: search_question_templates() 호출
**Then**:

- 예외 발생 안 함
- 빈 리스트 `[]` 반환
- 파이프라인은 계속 진행 (Tool 3으로)

#### AC3: 입력 검증 실패

**Given**: 잘못된 입력값 (오타, 범위 초과, 타입 오류 등)
**When**: search_question_templates(invalid_input) 호출
**Then**:

- ValueError 또는 TypeError 발생
- 에러 메시지에 검증 실패 이유 포함
- 로그에 WARNING 레벨로 기록

#### AC4: 난이도 범위 필터링

**Given**: difficulty=7 요청
**When**: search_question_templates() 호출
**Then**:

- 반환되는 템플릿의 avg_difficulty_score는 5.5~8.5 범위
- (input.difficulty ± 1.5)

#### AC5: 데이터베이스 에러 처리

**Given**: DB 연결 실패 또는 타임아웃
**When**: search_question_templates() 호출 중 DB 에러 발생
**Then**:

- 예외 발생 안 함
- 빈 리스트 반환
- 에러 메시지 로깅 (WARNING 또는 ERROR 레벨)

---

### 1.9 백엔드 통합

#### API 엔드포인트

**현재 상태**: Tool 2는 FastAPI 엔드포인트 없음 (아직 구현 대기)

**예상 엔드포인트** (REQ-B-* 백엔드에서 구현될 예정):

```
POST /api/v1/tools/search-templates
Content-Type: application/json

{
    "interests": ["LLM", "RAG"],
    "difficulty": 7,
    "category": "technical"
}

Response: 200
{
    "results": [
        {
            "id": "tmpl_550e8400_e29b_41d4_a716_446655440001",
            "stem": "...",
            ...
        }
    ]
}
```

#### 데이터베이스 스키마 (가정)

```sql
-- question_templates 테이블 (예상 스키마)
CREATE TABLE question_templates (
    id UUID PRIMARY KEY,
    category VARCHAR(50),  -- "technical", "business", "general"
    domain VARCHAR(100),   -- "LLM", "RAG", "Agent Architecture", ...
    stem TEXT,
    type VARCHAR(50),  -- "multiple_choice", "true_false", "short_answer"
    choices JSONB,  -- ["A) ...", "B) ...", ...]
    correct_answer VARCHAR(255),
    correct_rate FLOAT,
    usage_count INT,
    avg_difficulty_score FLOAT,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_templates_category_domain
    ON question_templates(category, domain);
CREATE INDEX idx_templates_difficulty
    ON question_templates(avg_difficulty_score);
```

#### 모델 정의 (가정)

```python
# src/backend/models/question_template.py (예상)
from sqlalchemy import Column, String, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

class QuestionTemplate(Base):
    __tablename__ = "question_templates"

    id: Column = Column(UUID, primary_key=True)
    category: Column = Column(String)
    domain: Column = Column(String)
    stem: Column = Column(Text)
    type: Column = Column(String)
    choices: Column = Column(JSONB)
    correct_answer: Column = Column(String)
    correct_rate: Column = Column(Float)
    usage_count: Column = Column(Integer)
    avg_difficulty_score: Column = Column(Float)
    is_active: Column = Column(Boolean, default=True)
    created_at: Column = Column(DateTime, default=datetime.utcnow)
    updated_at: Column = Column(DateTime, default=datetime.utcnow)
```

---

### 1.10 의존성

#### 직접 의존

- **Tool 1 (Get User Profile)**: interests[] 의존
- **FastAPI**: GET /api/v1/profile/{user_id} (Tool 1이 제공)
- **SQLAlchemy**: question_templates 테이블 쿼리
- **question_templates 테이블**: 템플릿 데이터소스

#### 간접 의존

- **Tool 3 (Get Difficulty Keywords)**: Tool 2 실패 시 폴백
- **Tool 4 (Validate Question Quality)**: Tool 2 결과를 few-shot 예시로 사용
- **LLM 프롬프트**: Tool 2 결과 기반 프롬프트 구성

---

### 1.11 제한사항 & 향후 고려사항

#### 현재 제한사항

1. **캐싱 없음**: 매 요청마다 DB 쿼리 (Tool 3에서 캐싱 담당)
2. **점수 기반 정렬만**: 사용자별 선호도 학습 없음
3. **하드코딩된 난이도 범위**: difficulty ± 1.5 (조정 불가)
4. **영어 이외 미지원**: stem/choices는 한글 지원하지만 도메인명은 영어로 제한

#### 향후 개선사항

- 사용자 선호도 학습 (클릭 기반)
- 템플릿 다양성 강화 (정렬 알고리즘 개선)
- 다국어 도메인명 지원
- 동적 난이도 범위 조정

---

## 📊 Phase 1 요약

### 1.12 규격 정리

| 항목 | 내용 |
|------|------|
| **모듈 경로** | `src/agent/tools/search_templates_tool.py` |
| **함수명** | `search_question_templates(interests: list[str], difficulty: int, category: str) -> list[dict[str, Any]]` |
| **입력 개수** | 3개 매개변수 (interests, difficulty, category) |
| **출력 타입** | `list[dict]` (0-10개 객체) |
| **예외 타입** | ValueError, TypeError (입력 검증 실패 시) |
| **로깅** | DEBUG/WARNING/ERROR 레벨 |
| **DB 의존** | question_templates 테이블 |
| **캐싱** | 없음 (매 호출마다 쿼리) |

### 1.13 다음 단계

- [ ] Phase 1 스펙 검토 및 승인
- [ ] Phase 2: 테스트 설계 (10-12개 테스트 케이스)
- [ ] Phase 3: 구현 및 테스트 실행
- [ ] Phase 4: 커밋 및 진행 상황 추적

---

**Status**: ✅ Phase 1 완료
**Next**: Phase 2 (테스트 설계)
