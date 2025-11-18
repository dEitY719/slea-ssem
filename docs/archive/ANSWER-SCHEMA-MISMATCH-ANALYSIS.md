# Answer Schema Mismatch Analysis & Fix

**문제**: `questions generate` vs `questions generate adaptive` 에서 생성되는 **answer_schema 구조가 다름**
**영향**: Scoring 실패 (0점 채점), 데이터 일관성 문제
**심각도**: 🔴 Critical (채점 불가능)

---

## 🔍 데이터 비교

### ✅ questions generate (정상)

```python
answer_schema = {
    "type": "exact_match",           # ← 올바른 구조
    "keywords": null,
    "correct_answer": "Algorithms"
}
```

### ❌ questions generate adaptive (문제)

```python
answer_schema = {
    "correct_key": "B",              # ← 잘못된 필드명
    "explanation": "LLM은 수십억..."  # ← 불필요한 설명
}
```

---

## 📊 문제점 분석

| 항목 | questions generate | questions generate adaptive | 문제 |
|------|-------------------|------------------------------|------|
| **type 필드** | ✓ "exact_match" | ✗ 없음 | Pydantic validation 실패 |
| **correct_answer** | ✓ "Algorithms" | ✗ "correct_key": "B" | 필드명 다름 |
| **keywords** | ✓ null | ✗ 없음 | 단답형 처리 불가 |
| **explanation** | ✗ 없음 | ✓ 설명 포함 | 불필요한 필드 |
| **choices encoding** | ✓ UTF-8 | ✗ Unicode escape | 보기 표시 오류 |

---

## 🔎 근본 원인

### 원인 1: Tool 5 응답 형식 차이

**questions generate 흐름**:

```
Agent → Tool 1 (get_user_profile)
      → Tool 2 (search templates)
      → Tool 3 (get_difficulty_keywords)
      → Tool 4 (validate_question_quality)
      → Tool 5 (save_generated_question)  ← 이 응답이 최종 answer_schema
           Response: {"type": "exact_match", "keywords": null, "correct_answer": "..."}
```

**questions generate adaptive 흐름**:

```
Agent → Tool 1 (get_user_profile)
      → Tool 3 (get_difficulty_keywords)  ← Tool 2 스킵
      → Tool 4 (validate_question_quality)
      → Tool 5 (save_generated_question)  ← 같은 응답 형식이어야 함
           But LLM Generated: {"correct_key": "B", "explanation": "..."}
                             (Tool 5 호출 안됨, LLM이 직접 생성)
```

**핵심**: Adaptive mode에서 Tool 5가 호출되지 않음 → LLM이 직접 JSON 생성 → 형식 불일치

### 원인 2: Unicode 인코딩 문제

**Adaptive mode choices 필드**:

```json
"choices": [
  "A: \uc791\uc740 \ud06c\uae30...",  ← Unicode escape 포함
  "B: \uc218\uc2ed\uc5b5 \uac1c...",
  ...
]
```

**정상 mode choices 필드**:

```json
"choices": [
  "Data",
  "Algorithms",
  "Human Intelligence",
  "All of the above"
]
```

**문제**: Unicode escape는 문자열 출력 시 인식되지 않음

---

## 🛠️ 근본 원인: LLM이 Tool 5를 호출하지 않음

로그를 보면 Adaptive mode에서는:

- Tool 1, 3, 4는 호출됨
- **Tool 5 (save_generated_question) 호출 안됨**
- LLM이 Final Answer에서 **직접 JSON 생성**

원인:

1. LLM이 Tool 5 호출 스킵
2. 직접 생성한 JSON이 Tool 5 응답 형식과 다름
3. Normalize 로직이 이 형식을 처리하지 못함

---

## ✅ 해결 방안

### Solution 1: Tool 5 호출 강제 (권장)

**파일**: `src/agent/pipeline/mode1_pipeline.py` (또는 mode2)

문제: Adaptive mode가 Tool 5를 건너뛰는 이유 분석 필요

- Adaptive mode 로직 확인
- Tool 5 호출 강제

### Solution 2: Answer Schema 정규화 강화

**파일**: `src/agent/llm_agent.py`

기존 `normalize_answer_schema()` 함수를 확장:

```python
def normalize_answer_schema_comprehensive(raw_schema: dict | str | None, question_type: str) -> dict:
    """
    Comprehensive answer_schema normalization.

    Handles multiple formats:
    1. Tool 5 format: {"type": "exact_match", "keywords": null, "correct_answer": "..."}
    2. LLM format: {"correct_key": "B", "explanation": "..."}
    3. String format: "exact_match"
    4. None: default based on question_type
    """
    if raw_schema is None:
        # Default based on question type
        return {
            "type": "keyword_match" if question_type == "short_answer" else "exact_match",
            "keywords": None,
            "correct_answer": None
        }

    if isinstance(raw_schema, str):
        return {
            "type": raw_schema,
            "keywords": None,
            "correct_answer": None
        }

    if isinstance(raw_schema, dict):
        # Case 1: Tool 5 format (already correct)
        if "type" in raw_schema:
            return {
                "type": raw_schema.get("type", "exact_match"),
                "keywords": raw_schema.get("keywords"),
                "correct_answer": raw_schema.get("correct_answer")
            }

        # Case 2: LLM format (correct_key instead of correct_answer)
        if "correct_key" in raw_schema:
            return {
                "type": "exact_match",
                "keywords": None,
                "correct_answer": raw_schema.get("correct_key")  # ← Convert correct_key to correct_answer
            }

        # Case 3: Unknown format - try best effort extraction
        return {
            "type": raw_schema.get("type", raw_schema.get("answer_type", "exact_match")),
            "keywords": raw_schema.get("keywords"),
            "correct_answer": raw_schema.get("correct_answer", raw_schema.get("correct_key"))
        }

    return {
        "type": "exact_match",
        "keywords": None,
        "correct_answer": None
    }
```

### Solution 3: Unicode 처리

**파일**: `src/backend/services/question_gen_service.py`

```python
def fix_unicode_encoding(choices: list[str]) -> list[str]:
    """Decode unicode escape sequences in choices."""
    if not choices:
        return choices

    fixed_choices = []
    for choice in choices:
        if isinstance(choice, str):
            try:
                # Try to decode unicode escapes
                decoded = choice.encode().decode('utf-8')
                fixed_choices.append(decoded)
            except:
                fixed_choices.append(choice)
        else:
            fixed_choices.append(str(choice))

    return fixed_choices
```

---

## 📝 구현 계획

### Phase 1: 근본 원인 파악 (지금)

- [x] Adaptive mode에서 Tool 5 호출 여부 확인
- [ ] Adaptive mode 로직 코드 위치 파악
- [ ] Tool 5 호출하지 않는 이유 분석

### Phase 2: Tool 5 호출 강제 (우선순위 높음)

- [ ] Adaptive mode 로직 수정
- [ ] Tool 5 호출 강제 또는 응답 형식 맞춤

### Phase 3: 정규화 강화 (우선순위 높음)

- [ ] `normalize_answer_schema_comprehensive()` 함수 구현
- [ ] LLM format → Tool 5 format 변환 로직
- [ ] answer_schema 검증 추가

### Phase 4: Unicode 처리 (우선순위 중간)

- [ ] choices 필드 Unicode 디코딩
- [ ] 테스트: choices 출력 정상 확인

---

## 🔧 즉시 적용 가능한 Hotfix

**파일**: `src/agent/llm_agent.py` (line 1014 주변)

기존 코드:

```python
normalized_schema_type = normalize_answer_schema(q.get("answer_schema"))
```

개선된 코드:

```python
# Handle both Tool 5 format and LLM format
raw_schema = q.get("answer_schema")
if isinstance(raw_schema, dict):
    # Convert LLM format (correct_key) to Tool 5 format (correct_answer)
    if "correct_key" in raw_schema and "type" not in raw_schema:
        normalized_schema_type = "exact_match"
        correct_answer = raw_schema.get("correct_key")
    else:
        normalized_schema_type = normalize_answer_schema(raw_schema)
        correct_answer = raw_schema.get("correct_answer")
else:
    normalized_schema_type = normalize_answer_schema(raw_schema)
    correct_answer = None
```

---

## 📊 기대 효과

| 단계 | 수정 내용 | 효과 |
|------|---------|------|
| 현재 | answer_schema 형식 불일치 | 0점 채점 (불가능) |
| + Phase 2 (Tool 5 호출) | Adaptive도 Tool 5 사용 | 통일된 응답 형식 |
| + Phase 3 (정규화) | 형식 변환 로직 | 어떤 형식도 처리 |
| + Phase 4 (Unicode) | 보기 정상 표시 | 완전한 기능 |

---

## 🎯 최종 검증 체크리스트

- [ ] `questions generate` → answer_schema 정상
- [ ] `questions generate adaptive` → answer_schema 정상
- [ ] `questions score` → 점수 계산 정상 (0점 아님)
- [ ] choices 보기 정상 표시
- [ ] Unicode 문자 정상 렌더링

---

**분석 완료**: 2025-11-18
**다음 단계**: Adaptive mode 코드 위치 파악 및 Tool 5 호출 로직 검토
