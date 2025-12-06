# REQ-AGENT-0-1 Phase 1: 디버깅 로깅 구현 완료

**작성일**: 2025-12-06
**상태**: ✅ IMPLEMENTED
**목표**: 사내 마이그레이션 에러의 근본 원인 파악을 위한 상세 디버깅 로깅 추가

---

## 📋 구현 내용 (Work 1-1: 디버깅 로깅 추가)

### 파일 수정
- **파일**: `src/agent/llm_agent.py`
- **변경 사항**:
  - `traceback` 모듈 임포트 추가 (라인 24)
  - `generate_questions()` 메서드에 5단계 상세 디버깅 로깅 추가 (라인 582-700)

### 추가된 로깅 포인트

#### 1️⃣ 모델 정보 추출 (라인 582-586)
```python
# [REQ-AGENT-0-1 Phase 1] 디버깅: 모델 정보 로깅
model_name = getattr(self.llm, "model", "unknown")
if model_name.startswith("models/"):
    model_name = model_name.replace("models/", "")
logger.debug(f"[Phase-1-Debug] Model: {model_name}")
```

**목적**: Gemini vs DeepSeek vs GPT-OSS 어느 모델이 실행 중인지 확인
**로그 출력**: `[Phase-1-Debug] Model: deepseek-v3-0324` 또는 `gemini-2.0-flash` 등

#### 2️⃣ Agent 실행 전 (라인 638)
```python
logger.debug(f"[Phase-1-Debug] Agent input length: {len(agent_input)}")
```

**목적**: Agent에 전달된 프롬프트의 크기 확인
**로그 출력**: `[Phase-1-Debug] Agent input length: 1234`

#### 3️⃣ Agent 실행 후 - intermediate_steps 분석 (라인 642-652)
```python
# intermediate_steps 분석
intermediate_steps = result.get("intermediate_steps", [])
logger.debug(f"[Phase-1-Debug] Intermediate steps count: {len(intermediate_steps)}")
for i, (action, observation) in enumerate(intermediate_steps):
    action_str = str(action)[:100] if action else "None"
    obs_str = str(observation)[:100] if observation else "None"
    logger.debug(f"[Phase-1-Debug]   Step {i}: action={action_str}... observation={obs_str}...")
```

**목적**: ReAct 루프가 정상 작동하는지 확인 (각 Tool 호출 결과)
**로그 출력**:
```
[Phase-1-Debug] Intermediate steps count: 5
[Phase-1-Debug]   Step 0: action=ToolCall(name='get_user_profile'...)... observation={'profile': {...}}...
[Phase-1-Debug]   Step 1: action=ToolCall(name='search_templates'...)... observation=[{...}, {...}]...
```

#### 4️⃣ Agent 실행 후 - AIMessage 검증 (라인 655-663)
```python
for msg_idx, message in enumerate(messages):
    if isinstance(message, AIMessage):
        content = getattr(message, "content", "")
        is_complete, reason = self._is_complete_react_response(content)
        if not is_complete:
            logger.warning(f"⚠️  Incomplete ReAct response detected at msg {msg_idx}: {reason}")
            logger.debug(f"[Phase-1-Debug] Response preview (first 500 chars): {content[:500]}...")
        else:
            logger.debug(f"[Phase-1-Debug] Message {msg_idx}: ReAct response format validation passed")
```

**목적**: LLM 응답이 ReAct 형식을 제대로 따르는지 확인
**로그 출력**:
```
[Phase-1-Debug] Message 0: ReAct response format validation passed
또는
⚠️  Incomplete ReAct response detected at msg 0: Missing "Final Answer:" marker
[Phase-1-Debug] Response preview (first 500 chars): Thought: I need to...
```

#### 5️⃣ 파싱 전 (라인 667-669)
```python
logger.debug(f"[Phase-1-Debug] Starting parse_agent_output_generate")
logger.debug(f"[Phase-1-Debug] Result keys: {list(result.keys())}")
```

**목적**: 파싱 함수 진입 전 결과 구조 확인
**로그 출력**: `[Phase-1-Debug] Result keys: ['messages', 'intermediate_steps']`

#### 6️⃣ 파싱 성공 (라인 675-677)
```python
logger.debug(f"[Phase-1-Debug] Parsing succeeded: {len(response.items)} questions")
logger.info(f"✅ 문항 생성 성공: {len(response.items)}개 생성")
```

**목적**: 파싱이 성공적으로 완료되었는지 확인
**로그 출력**: `[Phase-1-Debug] Parsing succeeded: 5 questions`

#### 7️⃣ 파싱 실패 (라인 682-693)
```python
except Exception as parse_error:
    logger.error(f"[Phase-1-Debug] Parsing failed: {parse_error.__class__.__name__}")
    logger.error(f"[Phase-1-Debug] Error message: {str(parse_error)[:500]}")

    if "messages" in result:
        messages = result.get("messages", [])
        for msg_idx, msg in enumerate(messages):
            if isinstance(msg, AIMessage):
                content = getattr(msg, "content", "")
                logger.debug(f"[Phase-1-Debug] AIMessage {msg_idx} length: {len(content)}")
                logger.debug(f"[Phase-1-Debug] AIMessage {msg_idx} preview (first 300): {content[:300]}")
```

**목적**: 파싱 실패의 정확한 원인과 실패 시점의 메시지 내용 기록
**로그 출력**:
```
[Phase-1-Debug] Parsing failed: JSONDecodeError
[Phase-1-Debug] Error message: Expecting value: line 1 column 1 (char 0)
[Phase-1-Debug] AIMessage 2 length: 1456
[Phase-1-Debug] AIMessage 2 preview (first 300): Final Answer: {"questions": [{"id": "q1"...
```

#### 8️⃣ 최종 예외 처리 (라인 699-700)
```python
logger.error(f"❌ 문항 생성 실패: {e.__class__.__name__}: {str(e)[:500]}")
logger.error(f"[Phase-1-Debug] Full exception: {traceback.format_exc()}")
```

**목적**: 전체 스택 트레이스 기록으로 에러 추적 가능
**로그 출력**:
```
[Phase-1-Debug] Full exception: Traceback (most recent call last):
  File "src/agent/llm_agent.py", line 673, in generate_questions
    response = self._parse_agent_output_generate(result, round_id)
  File "src/agent/llm_agent.py", line 1070, in _parse_agent_output_generate
    questions_data = AgentOutputConverter.parse_final_answer_json(content)
...
```

### 기존 상세 로깅

`_parse_agent_output_generate()` 메서드에는 이미 다음과 같은 상세 로깅이 있습니다:

#### Result 구조 분석 (라인 991-1048)
```python
logger.info("=" * 80)
logger.info("🔍 AGENT OUTPUT STRUCTURE ANALYSIS")
logger.info("=" * 80)

# Result dict 키 확인
result_keys = list(result.keys())
logger.info(f"Result 최상위 키: {result_keys}")

# intermediate_steps 확인
# messages 확인
# ToolMessage 확인 등...
```

**목적**: Agent 결과물의 전체 구조를 시각적으로 분석
**로그 출력**: 80자 구분선과 함께 messages, intermediate_steps, 각 message의 타입과 내용 미리보기

#### Tool 결과 추출 분석 (라인 1118-1139)
```python
tool_results = self._extract_tool_results(result, "save_generated_question")
logger.info(f"✓ 도구 호출 {agent_steps}개 발견, save_generated_question {len(tool_results)}개")

# DEBUG: 추출된 tool_results 상세 출력
if tool_results:
    for i, (tool_name, tool_output_str) in enumerate(tool_results):
        logger.info(f"  [{i}] tool_name={tool_name}")
        logger.info(f"      output_preview={output_preview}...")
else:
    logger.warning(f"⚠️  No tool results extracted! ...")
```

**목적**: Tool Calling이 정상 작동하는지, 특히 save_generated_question 도구가 호출되었는지 확인

---

## 🎯 로그 수집 방법 (사내 환경에서)

### 로깅 설정 확인
```python
# src/agent/llm_agent.py의 logger 설정
logger = logging.getLogger(__name__)  # DEBUG 레벨 이상 출력
```

### 로그 출력 위치
- **표준 출력**: 콘솔에 직접 출력
- **파일**: 기존 로깅 설정에 따라 로그 파일에 기록

### 사내 테스트 방법 (권장)

```bash
# 1. DeepSeek 환경에서 테스트 (사내)
LITELLM_MODEL=deepseek-v3-0324 \
python src/cli/main.py \
  > deepseek_debug.log 2>&1

# 프롬프트에서:
> auth login <username>
> questions generate --domain AI --round 1

# 2. GPT-OSS 환경에서 테스트 (선택사항)
LITELLM_MODEL=gpt-oss-120b \
python src/cli/main.py \
  > gpt_oss_debug.log 2>&1
```

### 로그 분석 가이드

**찾아볼 키워드**:
1. `[Phase-1-Debug] Model:` - 사용 중인 모델 확인
2. `[Phase-1-Debug] Intermediate steps count:` - Tool 호출 개수
3. `⚠️  Incomplete ReAct response detected` - 응답 형식 문제 있음
4. `[Phase-1-Debug] Parsing failed:` - 파싱 실패 원인
5. `[Phase-1-Debug] Full exception:` - 전체 스택 트레이스

**분석 예시**:
```
로그: [Phase-1-Debug] Parsing failed: JSONDecodeError
로그: [Phase-1-Debug] Error message: Expecting value: line 1 column 1 (char 0)
→ 원인: Final Answer JSON이 존재하지 않거나 형식이 잘못됨

로그: [Phase-1-Debug] Intermediate steps count: 2
로그: ⚠️  Incomplete ReAct response detected: Missing "Final Answer:" marker
→ 원인: Tool을 호출했으나 최종 답변을 생성하지 못함
```

---

## ✅ 테스트 상태

### 기존 테스트 통과 현황
- ✅ tests/agent/test_with_structured_output.py: **15/15 PASSED**
- ✅ 로깅 추가로 인한 기능 변경 없음 (로깅만 추가)

### 예상 테스트 결과
- ✅ `generate_questions()` 메서드는 동일하게 작동
- ✅ 로깅이 추가되어 상세한 디버그 정보 수집 가능
- ✅ 기존 기능에 영향 없음

---

## 📌 다음 단계

### Phase 1 완료 조건
- ✅ 디버깅 로깅 코드 추가 **← 완료**
- ⏳ 사내에서 Gemini vs DeepSeek vs GPT-OSS 비교 테스트 (사용자 수행)
- ⏳ 근본 원인 문서(ROOT_CAUSE_ANALYSIS.md) 작성

### Phase 2로 진행하기 위한 정보 필요
1. **DeepSeek에서 발생하는 정확한 에러**
   - 어느 단계에서 실패하는가? (Agent 실행 중 vs 파싱 중)
   - 에러 메시지가 무엇인가?

2. **로그 분석 결과**
   - Tool 호출 개수가 몇 개인가?
   - 최종 답변 형식이 무엇인가?

3. **GPT-OSS-120b 비교 (선택사항)**
   - 동일 요청에서 더 안정적인가?

---

## 🔗 참고 문서

- **전체 Action Plan**: `docs/feature/REQ-AGENT-0-1_ACTION_PLAN.md`
- **전체 전략**: `docs/feature/enhance_robust_agent_plan.md`
- **기술 리뷰**: `docs/feature/REQ-AGENT-0-1_review_*.md`

---

**구현 완료**: 2025-12-06
**다음 액션**: 사내 환경에서 테스트 실행 및 로그 수집
