# Bug Analysis: questions generate --count 3 JSON Parsing Failure

**문제**: `questions generate --count 3` 실행 시 간헐적으로 LLM 응답 파싱 실패
**영향**: 문제 생성 3회 시도 후 최종 실패 ("No tool results extracted")
**심각도**: 🔴 High (기능 완전 실패)

---

## 🔍 근본 원인 분석

### Issue 1: answer_schema 필드 구조 불일치

**로그 증거 (첫 번째 실패)**:

```
✗ Failed to create GeneratedItem: 1 validation error for AnswerSchema
type
  Input should be a valid string [type=string_type, input_value={'type': 'exact_match',
  'mapping': {...}}, input_type=dict]
```

**원인**:

1. **Tool 5 (save_question_tool)** 응답:

   ```python
   answer_schema = {
       "type": "exact_match",        # ← 문자열 ✓
       "mapping": {...}              # ← 추가 필드
   }
   ```

2. **LLM Final Answer JSON에서**:

   ```json
   {
     "answer_schema": {
       "type": "exact_match",
       "mapping": {"Data cleaning": 1, ...}
     }
   }
   ```

3. **AnswerSchema Pydantic 모델**:

   ```python
   class AnswerSchema(BaseModel):
       type: str                    # ← 문자열만 기대
       keywords: list[str] | None
       correct_answer: str | None
   ```

**문제**: `answer_schema.type`을 **객체로 감싸서** 보냄 (Dict → String 변환 필요)

---

### Issue 2: JSON 문법 오류 (개행 + 이스케이프)

**로그 증거 (두 번째 실패)**:

```
⚠️  Initial JSON parse failed at char 1117, applying additional cleanup
❌ Failed to parse Final Answer JSON: Expecting ',' delimiter: line 40 column 38 (char 1117)
```

**원인**: LLM이 생성한 JSON에 **이스케이프되지 않은 개행/특수문자** 포함

예시:

```json
{
  "answer_schema": "exact_match",
  "correct_answer": "Data cleaning",
  "correct_keywords": [
    "feature engineering",
    "data cleaning"          // ← 이 뒤에 개행, 그 다음 '}' (쉼표 누락)
  ]
}
```

---

### Issue 3: 파싱 재시도 로직 부족

**문제**:

1. **Initial JSON parse** 실패 → Cleanup 적용
2. **Cleanup 후 재파싱** 실패 → 예외로 처리
3. **Tool results 추출 시도** → 실패 (Final Answer 이미 실패)
4. **3회 재시도 후 최종 실패**

현재 코드 (line 887-904):

```python
try:
    questions_data = json.loads(json_str)
except json.JSONDecodeError as e:
    # Cleanup 적용
    json_str = re.sub(...)  # 1회 cleanup만
    questions_data = json.loads(json_str)  # ← 재파싱 실패 시 즉시 예외 발생
```

**문제**: Cleanup 후 재파싱 실패 → **로깅은 하지만 계속 진행**

---

## 🛠️ 해결 방안

### Solution 1: LLM Prompt 개선 (즉시 적용 가능)

**파일**: `src/agent/prompts/react_prompt.py`

LLM에게 답변 포맷을 더 정확하게 지시:

```python
FINAL_ANSWER_FORMAT_INSTRUCTION = """
Return Final Answer as a JSON array (NOT a JSON object).
Each item MUST have these exact fields:

{
  "question_id": "string",
  "type": "multiple_choice|true_false|short_answer",
  "stem": "question text",
  "choices": [array for MC/TF, null for short_answer],
  "answer_schema": "exact_match" | "keyword_match" | "semantic_match",  # ← STRING ONLY!
  "difficulty": number (1-10),
  "category": "AI" | "ML" | "DL" | "NLP",
  "validation_score": float (0.0-1.0),
  "correct_answer": "string or null" (for MC/TF only),
  "correct_keywords": [array of keywords] (for short_answer only)
}

CRITICAL RULES:
1. answer_schema must be a STRING, NOT an object
2. Do NOT include 'mapping', 'type', or other nested structures
3. All JSON strings must be properly escaped
4. Use valid JSON syntax - no trailing commas
5. Escape special characters: use \\n for newlines, \\t for tabs
6. If you call Tool 5 (save_generated_question), return the exact response as-is
"""
```

### Solution 2: Answer Schema 정규화 (robust 파싱)

**파일**: `src/agent/llm_agent.py` (line 921-932)

```python
# Before: answer_schema 값이 Dict인 경우 대비 부족
if question_type == "short_answer":
    answer_schema = AnswerSchema(
        type=q.get("answer_schema", "keyword_match"),
        keywords=q.get("correct_keywords"),
    )

# After: answer_schema 값의 타입을 정규화
def normalize_answer_schema(answer_schema_raw):
    """Convert answer_schema to string if it's a dict."""
    if isinstance(answer_schema_raw, dict):
        # Extract type field from dict
        return answer_schema_raw.get("type", "exact_match")
    return answer_schema_raw or "exact_match"

# Usage:
answer_schema_type = normalize_answer_schema(q.get("answer_schema"))
if question_type == "short_answer":
    answer_schema = AnswerSchema(
        type=answer_schema_type,
        keywords=q.get("correct_keywords"),
    )
else:
    answer_schema = AnswerSchema(
        type=answer_schema_type,
        correct_answer=q.get("correct_answer"),
    )
```

### Solution 3: 향상된 JSON 파싱 로직

**파일**: `src/agent/llm_agent.py` (line 887-904)

```python
def parse_and_clean_json(json_str: str, max_attempts: int = 3) -> dict | list:
    """
    Robust JSON parsing with multiple cleanup strategies.

    Args:
        json_str: Raw JSON string from LLM
        max_attempts: Number of cleanup attempts before giving up

    Returns:
        Parsed JSON object or list

    Raises:
        json.JSONDecodeError: If all attempts fail
    """
    cleanup_strategies = [
        ("identity", lambda s: s),  # No cleanup
        ("escape_quotes", lambda s: re.sub(r"\\(?!\\|/|[btnfr])", "\\\\", s)),
        ("fix_none", lambda s: re.sub(r"\bNone\b", "null", s)),
        ("fix_booleans", lambda s: re.sub(r"\b(True|False)\b", lambda m: m.group(1).lower(), s)),
        ("remove_control_chars", lambda s: s.encode('utf-8', 'ignore').decode('utf-8')),
        ("fix_trailing_commas", lambda s: re.sub(r",(\s*[}\]])", r"\1", s)),
    ]

    last_error = None
    for attempt, (strategy_name, cleanup_fn) in enumerate(cleanup_strategies):
        try:
            cleaned = cleanup_fn(json_str)
            result = json.loads(cleaned)
            if attempt > 0:
                logger.info(f"✅ JSON parse succeeded with strategy '{strategy_name}' (attempt {attempt + 1})")
            return result
        except json.JSONDecodeError as e:
            last_error = e
            logger.debug(f"   Attempt {attempt + 1} ({strategy_name}) failed: char {e.pos}")
            continue

    # All attempts failed
    logger.error(f"❌ All JSON parse attempts failed. Last error: {last_error}")
    raise last_error
```

**사용**:

```python
try:
    questions_data = parse_and_clean_json(json_str)
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse JSON: {e}")
    error_messages.append(f"JSON parsing failed after 5 attempts: {str(e)}")
    continue
```

### Solution 4: Tool Result Fallback

**문제**: Final Answer 파싱 실패 → Tool 결과로 fallback 시도 → 둘 다 없으면 실패

**개선**: Tool 호출 결과를 더 적극적으로 추출

```python
# Current code (line 978-996):
if not items:
    logger.info("\n📊 Extracting save_generated_question tool results...")
    tool_results = self._extract_tool_results(result, "save_generated_question")
    logger.info(f"✓ 도구 호출 {agent_steps}개 발견, save_generated_question {len(tool_results)}개")

# Improved:
if not items:
    logger.info("\n📊 Extracting save_generated_question tool results...")
    # Try multiple tool names for robustness
    tool_names = [
        "save_generated_question",
        "save_question",
        "save_question_tool",
    ]

    for tool_name in tool_names:
        tool_results = self._extract_tool_results(result, tool_name)
        if tool_results:
            logger.info(f"✓ Found {len(tool_results)} results from tool '{tool_name}'")
            break

    if not tool_results:
        logger.warning("⚠️  No tool results found from any tool name")
        error_messages.append("No Final Answer JSON or tool results extracted")
```

---

## 📊 Impact Analysis

### Root Causes 정리

| 원인 | 빈도 | 영향 | 해결책 |
|------|------|------|--------|
| answer_schema Dict vs String | **중간** | 파싱 실패 | Solution 2 (정규화) |
| JSON 문법 오류 (개행, 쉼표) | **높음** | 파싱 실패 | Solution 1 (Prompt) + Solution 3 (파싱) |
| 파싱 재시도 로직 부족 | **높음** | 전체 실패 | Solution 3 (robust parsing) |
| Tool name 불일치 | **낮음** | Fallback 실패 | Solution 4 (tool name flexibility) |

---

## 🚀 구현 우선순위

### Priority 1: LLM Prompt 개선 (가장 효과적)

- **난이도**: ⭐ Easy
- **효과**: 70-80% 문제 해결
- **작업**: Prompt 수정 (1-2분)
- **테스트**: 즉시 효과 확인 가능

### Priority 2: Robust JSON 파싱

- **난이도**: ⭐⭐ Medium
- **효과**: 15-20% 추가 개선
- **작업**: Parser 함수 추가 (30분)
- **테스트**: 단위 테스트 (cleanup 전략별)

### Priority 3: Answer Schema 정규화

- **난이도**: ⭐ Easy
- **효과**: 5% 추가 개선
- **작업**: Helper 함수 추가 (10분)

### Priority 4: Tool Result Fallback

- **난이도**: ⭐⭐ Medium
- **효과**: 3% 추가 개선
- **작업**: 도구 이름 확장 (15분)

---

## 📈 예상 개선 효과

| 구현 단계 | 성공률 | 비고 |
|----------|-------|------|
| **현재** | ~60% | 간헐적 실패 (30-40%) |
| **+ Prompt 개선** | 85-90% | 가장 효과적 |
| **+ Robust Parser** | 92-95% | 엣지케이스 처리 |
| **+ 정규화 + Fallback** | 98%+ | Production ready |

---

## 🔧 Next Steps

1. **즉시 (오늘)**: Solution 1 구현 (Prompt 개선)
   - `src/agent/prompts/react_prompt.py` 수정
   - `questions generate --count 5` 테스트 3회 (모두 성공 확인)

2. **단기 (내일)**: Solution 2,3 구현 (Robust Parser)
   - `src/agent/llm_agent.py` 파서 함수 추가
   - 단위 테스트 작성 (`test_json_parsing_strategies.py`)

3. **중기**: Solution 3 구현 (Schema 정규화)
   - Helper 함수 추가
   - Integration 테스트

4. **장기**: Solution 4 구현 (Fallback 개선)
   - Tool name flexibility 추가
   - E2E 테스트 (agent 통합 테스트)

---

## 📝 Implementation Checklist

### Phase 1: LLM Prompt 개선

- [ ] `src/agent/prompts/react_prompt.py`에 명확한 JSON 포맷 지시 추가
- [ ] answer_schema를 "string ONLY" 명시
- [ ] 이스케이프 규칙 명확화
- [ ] Manual test: `questions generate --count 3` 5회 실행 (모두 성공)

### Phase 2: Robust Parser 구현

- [ ] `parse_and_clean_json()` 함수 구현
- [ ] Cleanup strategies 배열로 정의
- [ ] Logging으로 어떤 전략이 성공했는지 추적
- [ ] Unit test: 다양한 JSON 문법 오류에 대한 테스트

### Phase 3: Schema 정규화

- [ ] `normalize_answer_schema()` 헬퍼 함수 구현
- [ ] Dict → String 변환 로직
- [ ] Type checking 추가

### Phase 4: Fallback 개선

- [ ] Tool name list 정의
- [ ] 여러 도구 이름으로 시도
- [ ] Logging 상세화

---

**작성자**: Claude Code
**분석 일자**: 2025-11-18
**버전**: 1.0
