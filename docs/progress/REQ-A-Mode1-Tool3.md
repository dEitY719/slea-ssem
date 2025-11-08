# REQ-A-Mode1-Tool3: Phase 1 - Specification

**작성일**: 2025-11-09
**단계**: Phase 1 (📝 Specification)
**상태**: Specification 작성 완료, 검토 대기

---

## 📋 Phase 1: SPECIFICATION

### 1.1 요구사항 분석

#### 기능 개요

**REQ-A-Mode1-Tool3: Get Difficulty Keywords**

Tool 3는 질문 생성 파이프라인의 세 번째 단계에서 사용되는 도구입니다.

특정 난이도(1-10)와 카테고리에 대한 주요 키워드, 개념, 예시 문항을 조회하여 LLM 프롬프트 작성 시 컨텍스트를 제공합니다. 캐시된 데이터를 우선 사용하여 성능을 최적화합니다.

**역할**:

- Mode 1 파이프라인에서 Tool 2(검색 템플릿) 실패 또는 완료 후 실행
- 난이도별 키워드 및 개념을 제공하여 LLM 프롬프트 향상
- 데이터베이스 쿼리 실패 시 캐시된 기본값 사용 (graceful degradation)

#### 우선순위 & 스코프

| 항목 | 값 |
|------|-----|
| **REQ ID** | REQ-A-Mode1-Tool3 |
| **우선순위** | Must (M) |
| **영역** | Mode 1 - 문항 생성 파이프라인 |
| **스코프** | 키워드/개념/예시 조회 (캐싱 포함) |
| **MVP** | 1.0 |
| **BacklogSize** | 5개 sub-tasks |

---

### 1.2 입력 명세

#### 입력 데이터 구조

```python
{
    "difficulty": 7,  # 난이도 (1-10)
    "category": "technical"  # 상위 카테고리 (technical, business, general)
}
```

#### 입력 필드 정의

| 필드 | 타입 | 필수 | 설명 | 유효성 검증 |
|------|------|------|------|-----------|
| `difficulty` | `int` | ✓ | 난이도 레벨 | 1-10 범위 |
| `category` | `str` | ✓ | 상위 카테고리 | "technical"\|"business"\|"general" |

#### 입력 검증 규칙

1. **difficulty**:
   - 타입: int
   - 범위: 1-10 포함
   - float 입력: int로 변환 후 검증
   - 범위 밖: ValueError 발생

2. **category**:
   - 타입: str
   - 허용값: "technical", "business", "general"
   - 대소문자 구분: 소문자 통일 후 검증
   - 미지원 카테고리: ValueError 발생

---

### 1.3 출력 명세

#### 출력 데이터 구조

```python
{
    "difficulty": 7,
    "category": "technical",
    "keywords": [
        "Large Language Model",
        "Transformer Architecture",
        "Attention Mechanism",
        "Fine-tuning",
        "Prompt Engineering",
        "Token Embedding",
        "Semantic Understanding"
    ],
    "concepts": [
        {
            "name": "Retrieval Augmented Generation",
            "acronym": "RAG",
            "definition": "LLM과 외부 지식 데이터베이스를 연결하여 정확도를 높이는 기술",
            "key_points": [
                "Retrieval: 관련 문서 검색",
                "Augmented: 문서로 프롬프트 확장",
                "Generation: LLM이 최종 답변 생성"
            ]
        },
        {
            "name": "Chain-of-Thought Prompting",
            "acronym": "CoT",
            "definition": "LLM에게 중간 단계의 추론 과정을 요청하는 기법",
            "key_points": [
                "Step-by-step 사고 과정 활성화",
                "복잡한 문제 해결력 향상",
                "설명 가능한 AI(XAI) 지원"
            ]
        }
        # ... 최대 10개
    ],
    "example_questions": [
        {
            "stem": "Transformer 모델에서 Attention Mechanism의 역할은?",
            "type": "short_answer",
            "difficulty_score": 7.5,
            "answer_summary": "입력 시퀀스의 각 단어가 다른 단어들에 얼마나 영향을 미치는지 학습"
        },
        # ... 최대 5개
    ]
}
```

#### 출력 필드 정의

| 필드 | 타입 | 설명 |
|------|------|------|
| `difficulty` | `int` | 요청한 난이도 (echo) |
| `category` | `str` | 요청한 카테고리 (echo) |
| `keywords` | `list[str]` | 난이도별 주요 키워드 (5-20개) |
| `concepts` | `list[dict]` | 핵심 개념 설명 (최대 10개) |
| `example_questions` | `list[dict]` | 예시 문항 (최대 5개) |

#### Concepts 항목 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `name` | `str` | 개념명 (30-100글자) |
| `acronym` | `str` | 약자 (2-10글자) |
| `definition` | `str` | 정의 (50-300글자) |
| `key_points` | `list[str]` | 핵심 포인트 (3-5개, 각 20-100글자) |

#### Example Questions 항목 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `stem` | `str` | 문항 내용 (50-300글자) |
| `type` | `str` | 문항 유형 ("short_answer", "multiple_choice", "true_false") |
| `difficulty_score` | `float` | 난이도 (0.0-10.0) |
| `answer_summary` | `str` | 정답 요약 (30-200글자) |

---

### 1.4 동작 명세

#### 4.1 조회 로직

```
Input: difficulty, category
│
├─ 1단계: 입력 검증
│  ├─ difficulty 검증 (1-10 범위)
│  └─ category 검증 (허용값 확인)
│
├─ 2단계: 캐시 확인
│  ├─ in-memory 캐시 확인: {difficulty}_{category}
│  ├─ 캐시 HIT: 캐시 데이터 반환
│  └─ 캐시 MISS: DB 조회로 진행
│
├─ 3단계: 데이터베이스 조회
│  ├─ difficulty_keywords 테이블 쿼리
│  ├─ 필터: difficulty = input.difficulty AND category = input.category
│  ├─ 결과 없음: 캐시된 기본값(DEFAULT_KEYWORDS) 사용
│  └─ DB 에러: 캐시된 기본값 사용 (graceful degradation)
│
├─ 4단계: 응답 구성
│  ├─ 캐시에 저장 (TTL: 1시간)
│  ├─ JSON 형식으로 변환
│  └─ 정규화 (null → 기본값)
│
└─ Output: dict with keywords, concepts, example_questions
```

#### 4.2 캐싱 전략

```python
# In-memory 캐시 구조
KEYWORDS_CACHE = {
    "1_technical": {"keywords": [...], "concepts": [...], ...},  # TTL: 1시간
    "7_technical": {...},
    "10_business": {...},
    ...
}

# 캐시 키: f"{difficulty}_{category}"
# 캐시 값: 완전한 응답 dict
# TTL: 3600초 (1시간)
# 만료 후: 자동 재조회 또는 기본값 사용
```

#### 4.3 기본값 (DEFAULT_KEYWORDS)

```python
DEFAULT_KEYWORDS = {
    "difficulty": 5,
    "category": "general",
    "keywords": [
        "Communication",
        "Problem Solving",
        "Teamwork",
        "Critical Thinking",
        "Adaptability"
    ],
    "concepts": [
        {
            "name": "Effective Communication",
            "acronym": "EC",
            "definition": "명확하고 효율적인 정보 전달",
            "key_points": [
                "Clear message formulation",
                "Active listening",
                "Feedback exchange"
            ]
        },
        # ... 2-3개 기본 개념
    ],
    "example_questions": [
        {
            "stem": "팀 프로젝트에서 의견 불일치가 발생했을 때 가장 먼저 해야 할 일은?",
            "type": "short_answer",
            "difficulty_score": 5.0,
            "answer_summary": "모든 의견을 경청하고 공통점 찾기"
        }
    ]
}
```

---

### 1.5 에러 처리

#### 5.1 입력 검증 에러

| 에러 시나리오 | 입력 | 예외 | 처리 방식 | 파이프라인 진행 |
|-------------|------|------|---------|-----------|
| 1. difficulty 범위 초과 | `difficulty=11` | ValueError | 로그 + 예외 발생 | 중단 |
| 2. difficulty 타입 오류 | `difficulty="7"` | TypeError | 로그 + 예외 발생 | 중단 |
| 3. category 미지원 | `category="unknown"` | ValueError | 로그 + 예외 발생 | 중단 |

#### 5.2 데이터베이스 에러 (Graceful Degradation)

| 에러 시나리오 | 예외 | 처리 방식 | 반환값 |
|-------------|------|---------|--------|
| 1. DB 연결 실패 | OperationalError | 로그 기록 + 캐시 확인 | 기본값 또는 캐시 |
| 2. 쿼리 타임아웃 | TimeoutError | 로그 기록 + 캐시 확인 | 기본값 또는 캐시 |
| 3. 임시 DB 오류 | Exception | 로그 기록 + 캐시 확인 | 기본값 또는 캐시 |
| 4. 검색 결과 없음 | 정상 (에러 아님) | 캐시 없음 | 기본값(DEFAULT_KEYWORDS) |

#### 5.3 에러 처리 원칙

- **입력 에러**: 예외 발생 (파이프라인에서 재시도 또는 폐기)
- **DB 에러**: 캐시 확인 → 캐시 없으면 기본값 반환 (시스템 중단 없음)
- **캐시 만료**: 자동 재조회 또는 기본값 사용
- **로깅**: 모든 에러는 DEBUG/WARNING/ERROR 레벨로 기록

---

### 1.6 캐싱 상세

#### 캐시 전략

| 측면 | 구현 |
|------|------|
| **캐시 타입** | In-memory dict (LRU 캐시) |
| **캐시 키** | `f"{difficulty}_{category}"` |
| **캐시 TTL** | 3600초 (1시간) |
| **최대 항목** | 100개 (LRU 제거) |
| **만료 처리** | 자동 재조회 또는 기본값 |
| **스레드 안전성** | threading.Lock 사용 |

#### 캐시 초기화

```python
# 애플리케이션 시작 시
_keywords_cache = {}

# 모든 10개 난이도 + 3개 카테고리 조합 사전 로드 (선택사항)
# for difficulty in range(1, 11):
#     for category in ["technical", "business", "general"]:
#         _load_keywords_to_cache(difficulty, category)
```

---

### 1.7 성능 요구사항

| 요구사항 | 목표값 | 설명 |
|---------|--------|------|
| **응답 시간 (캐시 HIT)** | < 10ms | 메모리 조회만 |
| **응답 시간 (캐시 MISS)** | < 500ms | DB 쿼리 + 캐시 저장 |
| **캐시 HIT 율** | >= 80% | 정상 운영 시 목표 |
| **동시 요청** | 10+ / sec | 멀티스레드 안전성 |

---

### 1.8 보안 요구사항

| 요구사항 | 구현 |
|---------|------|
| **입력 검증** | 모든 입력값 타입/범위 검증 |
| **SQL 주입 방지** | SQLAlchemy ORM 사용 |
| **캐시 독립성** | 사용자 정보 미포함 (어느 사용자든 같은 결과) |
| **로깅** | 민감 정보 제외 |

---

### 1.9 Acceptance Criteria

#### AC1: 유효한 입력으로 완전한 응답 반환

**Given**: 유효한 difficulty (1-10), category ("technical"/"business"/"general") 제공
**When**: get_difficulty_keywords() 호출
**Then**:

- 결과는 dict 타입
- 필수 필드 포함: difficulty, category, keywords, concepts, example_questions
- keywords: 5개 이상 20개 이하
- concepts: 최대 10개, 각 항목은 name, acronym, definition, key_points 포함
- example_questions: 최대 5개

#### AC2: DB 에러 시 기본값 반환

**Given**: difficulty_keywords 테이블이 없거나 DB 연결 실패
**When**: get_difficulty_keywords() 호출
**Then**:

- 예외 발생 안 함
- DEFAULT_KEYWORDS 또는 캐시된 데이터 반환
- 파이프라인은 계속 진행

#### AC3: 입력 검증 실패

**Given**: 잘못된 입력값 (범위 초과, 타입 오류, 미지원 카테고리)
**When**: get_difficulty_keywords(invalid_input) 호출
**Then**:

- ValueError 또는 TypeError 발생
- 에러 메시지에 검증 실패 이유 포함
- 로그에 WARNING 레벨로 기록

#### AC4: 캐시 동작 검증

**Given**: 동일한 (difficulty, category) 연속 호출
**When**: get_difficulty_keywords() 첫 호출 후 재호출
**Then**:

- 첫 호출: DB 쿼리 (> 50ms)
- 두 번째 호출: 캐시 반환 (< 10ms)
- 응답 데이터는 동일

#### AC5: 출력 필드 정규화

**Given**: DB에서 조회한 데이터에 NULL 필드 포함
**When**: get_difficulty_keywords() 호출
**Then**:

- NULL 필드는 기본값으로 대체
- 모든 필드가 존재하는 완전한 응답 반환

---

### 1.10 백엔드 통합

#### API 엔드포인트

**현재 상태**: Tool 3은 FastAPI 엔드포인트 없음 (아직 구현 대기)

**예상 엔드포인트** (REQ-B-* 백엔드에서 구현될 예정):

```
POST /api/v1/tools/difficulty-keywords
Content-Type: application/json

{
    "difficulty": 7,
    "category": "technical"
}

Response: 200
{
    "difficulty": 7,
    "category": "technical",
    "keywords": [...],
    "concepts": [...],
    "example_questions": [...]
}
```

#### 데이터베이스 스키마 (가정)

```sql
-- difficulty_keywords 테이블 (예상 스키마)
CREATE TABLE difficulty_keywords (
    id UUID PRIMARY KEY,
    difficulty INT,  -- 1-10
    category VARCHAR(50),  -- "technical", "business", "general"
    keywords JSONB,  -- ["keyword1", "keyword2", ...]
    concepts JSONB,  -- [{"name": "...", "acronym": "...", ...}, ...]
    example_questions JSONB,  -- [{"stem": "...", "type": "...", ...}, ...]
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(difficulty, category)
);

CREATE INDEX idx_difficulty_keywords_lookup
    ON difficulty_keywords(difficulty, category);
```

#### 모델 정의 (가정)

```python
# src/backend/models/difficulty_keyword.py (예상)
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

class DifficultyKeyword(Base):
    __tablename__ = "difficulty_keywords"

    id: Column = Column(UUID, primary_key=True, default=uuid4)
    difficulty: Column = Column(Integer)
    category: Column = Column(String)
    keywords: Column = Column(JSONB)
    concepts: Column = Column(JSONB)
    example_questions: Column = Column(JSONB)
    is_active: Column = Column(Boolean, default=True)
    created_at: Column = Column(DateTime, default=datetime.utcnow)
    updated_at: Column = Column(DateTime, default=datetime.utcnow)
```

---

### 1.11 의존성

#### 직접 의존

- **Tool 2 (Search Question Templates)**: Tool 2 미스 또는 실패 후 호출
- **SQLAlchemy**: difficulty_keywords 테이블 쿼리
- **difficulty_keywords 테이블**: 키워드/개념 데이터소스
- **Python threading**: 캐시 스레드 안전성

#### 간접 의존

- **Tool 4 (Validate Question Quality)**: Tool 3 결과 기반 LLM 프롬프트 구성
- **LLM 프롬프트**: Tool 3 키워드/개념 기반 프롬프트 향상

---

### 1.12 제한사항 & 향후 고려사항

#### 현재 제한사항

1. **정적 데이터**: 런타임 중 수정 불가 (재배포 필요)
2. **영어 중심**: 키워드, 개념명은 주로 영어 (정의는 한글)
3. **난이도별 분리**: 난이도 범위 쿼리 없음 (정확 일치만)
4. **수동 관리**: 키워드/개념은 수동으로 입력

#### 향후 개선사항

- 동적 키워드 학습 (사용자 반응 기반)
- 다국어 지원 (영어, 중국어, 일본어)
- 난이도 범위 쿼리 (예: 5-7 난이도의 모든 키워드)
- 커뮤니티 기반 키워드 추가

---

## 📊 Phase 1 요약

### 1.13 규격 정리

| 항목 | 내용 |
|------|------|
| **모듈 경로** | `src/agent/tools/difficulty_keywords_tool.py` |
| **함수명** | `get_difficulty_keywords(difficulty: int, category: str) -> dict[str, Any]` |
| **입력 개수** | 2개 매개변수 (difficulty, category) |
| **출력 타입** | `dict` with keywords[], concepts[], example_questions[] |
| **예외 타입** | ValueError, TypeError (입력 검증 실패 시) |
| **캐싱** | In-memory LRU (TTL: 1시간) |
| **캐시 전략** | graceful degradation (DB 실패 → 캐시 → 기본값) |
| **로깅** | DEBUG/WARNING/ERROR 레벨 |
| **DB 의존** | difficulty_keywords 테이블 |

### 1.14 다음 단계

- [ ] Phase 1 스펙 검토 및 승인
- [ ] Phase 2: 테스트 설계 (12-14개 테스트 케이스)
- [ ] Phase 3: 구현 및 테스트 실행
- [ ] Phase 4: 커밋 및 진행 상황 추적

---

**Status**: ✅ Phase 1 완료
**Next**: Phase 2 (테스트 설계)
