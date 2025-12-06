# REQ-AGENT-0-1 Action Plan: 전략 전환 후 실행 계획

**작성일**: 2025-12-06
**목표**: 사내 환경(DeepSeek-v3-0324 또는 GPT-OSS-120b) 정상 작동 확보
**전략**: `enhance_robust_agent_plan.md` 기반 3단계 접근법
**상태**: Phase 1 준비 중

---

## 📋 Overview: 왜 전략을 전환했는가?

### 이전 접근 (❌ Over-engineering)
```
REQ-AGENT-0-1: with_structured_output 전체 구현
→ 복잡한 Gather-Then-Generate 아키텍처 필요
→ LangChain 미지원 모델 호환성 불명확
→ 배포 위험 높음
```

### 새로운 접근 (✅ 실용적, 최소 변경)
```
Phase 1 (즉시): 사내 실제 에러 원인 파악
Phase 2 (단기): 모델별 최적화로 안정화 (ReAct + Tool 유지)
Phase 3 (장기): 안정화 후 with_structured_output 필요성 재검토
```

**핵심 가정**:
- Tool Calling은 Gemini, DeepSeek, GPT-OSS 모두 지원 ✅
- 현재 ReAct + Manual Parsing으로 기본은 작동 ✅
- 사내 에러는 **모델별 호환성 문제** (아키텍처 문제 아님) ❌
- 최소 변경으로 빠른 해결 가능

---

## 🎯 Phase 1: 근본 원인 파악 (긴급 디버깅)

### 목표
사내 마이그레이션 중 발생한 에러의 정확한 원인 파악

### 작업 1-1: 디버깅 로깅 추가 (개발 환경)
**위치**: `src/agent/llm_agent.py` → `generate_questions()` 메서드

**수정 사항**:
```python
# 기존: 단순 로깅만 실행
logger.info(f"REQ-AGENT-0-1: ... use_structured={use_structured}")

# 변경: 상세 디버깅 정보 기록
def generate_questions(...):
    # ...
    # 1단계: ReAct agent 실행 전 로깅
    logger.debug(f"[Phase-1-Debug] Model: {model_name}, Prompt hash: {hash(prompt)}")

    # 2단계: Agent 실행 후 로깅
    agent_result = self.agent_executor.invoke(...)
    logger.debug(f"[Phase-1-Debug] intermediate_steps count: {len(agent_result.get('intermediate_steps', []))}")
    for i, (action, observation) in enumerate(agent_result.get('intermediate_steps', [])):
        logger.debug(f"  Step {i}: {action.tool} → {observation[:200]}...")  # 처음 200자만

    # 3단계: Parsing 시작 전 로깅
    logger.debug(f"[Phase-1-Debug] Raw output length: {len(str(agent_result))}")

    # 4단계: Parsing 중 에러 catch
    try:
        parsed = self._parse_agent_output_generate(agent_result)
    except Exception as e:
        logger.error(f"[Phase-1-Debug] Parsing failed at step: {e.__class__.__name__}: {str(e)[:500]}")
        raise

    # 5단계: 최종 결과 로깅
    logger.debug(f"[Phase-1-Debug] Parsing success: {len(parsed)} questions")
```

**파일 변경**: `src/agent/llm_agent.py` (약 50줄 추가)
**비용**: 낮음 (로깅만 추가, 로직 변경 없음)

### 작업 1-2: 사내 환경에서 테스트 시나리오 실행
**어디서**: 사용자 사내 환경
**무엇을**: 동일 요청 (프로필 + 도메인)에 대해 Gemini vs DeepSeek 비교

**테스트 케이스**:
```bash
# 1. Gemini (참조 모델)
python src/cli/main.py
> auth login <user>
> questions generate --domain AI --round 1
→ ✅ 성공 확인

# 2. DeepSeek (문제 모델)
LITELLM_MODEL=deepseek-v3-0324 python src/cli/main.py
> auth login <user>
> questions generate --domain AI --round 1
→ ❌ 에러 발생 지점 확인

# 3. GPT-OSS-120b (비교 모델)
LITELLM_MODEL=gpt-oss-120b python src/cli/main.py
> auth login <user>
> questions generate --domain AI --round 1
→ ? 안정성 평가
```

**수집할 정보**:
- 로그 파일 (디버깅 로깅)
- 에러 메시지 (정확한 Exception)
- 응답 시간 (모델별 비교)
- 토큰 사용량 (cost 평가)

**파일 변경**: 없음 (테스트만 실행)
**비용**: 없음 (사용자 수행)

### 작업 1-3: 분석 및 근본 원인 문서화
**위치**: 분석 결과를 `docs/feature/REQ-AGENT-0-1_ROOT_CAUSE_ANALYSIS.md`에 작성

**산출물**:
```markdown
# Root Cause Analysis: DeepSeek Compatibility

## 발견 사항

### 에러 1: Tool JSON 형식 차이
- Gemini output: `{"tool_name": "...", "tool_input": {...}}`
- DeepSeek output: `[{"name": "...", "input": {...}}]`
- 영향: `parse_json_robust` 실패 → 도구 호출 안 됨

### 에러 2: Final Answer 형식 불일치
- 예상: "Final Answer:\n{...json...}"
- 실제: "最终答案:\n{...}" (중국어 사용)
- 영향: 최종 JSON 추출 실패

### 에러 3: Tool 반복 호출 제한
- Gemini: Tool 1-5번 정상 호출
- DeepSeek: 3번 이후 중단
- 영향: 불완전한 데이터 수집

## 권장사항

Priority 순서:
1. **P0**: 에러 1 해결 (Tool JSON 정규화)
2. **P0**: 에러 2 해결 (Final Answer 형식 유연성)
3. **P1**: 에러 3 해결 (Tool 호출 정책 수정)
```

**파일 변경**: 신규 문서 작성
**비용**: 중간 (분석 시간)

---

## 🔧 Phase 2: 모델별 최적화 (호환성 개선)

### 전략
원인 파악 결과에 따라 다음 3가지 방향 중 최적의 해결책 선택

### 옵션 A: 모델별 프롬프트 최적화

**목표**: 각 모델이 이해하기 좋은 형식으로 지시사항 제공

**작업 2A-1**: 모델별 ReAct 프롬프트 생성

```python
# src/agent/prompts/react_prompt.py 수정

# 기존: 동일한 프롬프트를 모든 모델에 사용
# 변경: 모델별 최적화 프롬프트

def get_react_prompt(model_name: str) -> str:
    """모델에 최적화된 ReAct 프롬프트 반환"""

    base_prompt = """
    You are an AI assistant helping generate test questions.

    Use the following tools to gather information:
    - tool_1: Get user profile
    - tool_2: Search templates
    - tool_3: Get difficulty keywords
    - tool_4: Validate quality
    - tool_5: Save question

    Format your response as:
    Thought: <your thinking>
    Action: <tool_name>
    Action Input: <json_input>
    Observation: <result>
    ... (repeat as needed)
    Final Answer: <json_output>
    """

    if "gemini" in model_name.lower():
        return base_prompt + GEMINI_SPECIFIC_INSTRUCTIONS
    elif "deepseek" in model_name.lower():
        return base_prompt + DEEPSEEK_SPECIFIC_INSTRUCTIONS
    elif "gpt-oss" in model_name.lower():
        return base_prompt + GPT_OSS_SPECIFIC_INSTRUCTIONS
    else:
        return base_prompt
```

**GEMINI_SPECIFIC_INSTRUCTIONS**:
```
- Always use JSON format for tool inputs
- Each Action must be followed immediately by Action Input
- Final Answer must contain the complete JSON object
```

**DEEPSEEK_SPECIFIC_INSTRUCTIONS**:
```
- Do NOT use XML tags in your response
- Use English for "Thought", "Action", "Final Answer" labels
- Format Action Input as valid JSON (not XML)
- For Final Answer, provide ONLY the JSON object, no markdown
```

**GPT_OSS_SPECIFIC_INSTRUCTIONS**:
```
- Use clear tool names exactly as specified
- Each tool invocation must show both action and observation
- Final Answer should be wrapped in clear markers: ### FINAL ANSWER ###
```

**파일 변경**: `src/agent/prompts/react_prompt.py` (약 100줄)
**비용**: 낮음 (프롬프트 텍스트만 추가)

### 옵션 B: Tool Call 형식 정규화

**목표**: 모든 모델의 Tool call을 통일된 형식으로 변환

**작업 2B-1**: Tool Call 추출 함수 개선

```python
# src/agent/llm_agent.py → 새로운 유틸리티 함수

def normalize_tool_calls(raw_output: str, model_name: str) -> List[Dict]:
    """
    모델별 Tool call 형식을 통일된 Dict 리스트로 변환

    Gemini: {"tool_name": "...", "tool_input": {...}}
    DeepSeek: [{"name": "...", "input": {...}}]
    GPT-OSS: "Tool: ...\nInput: {...}"

    → 공통 형식: [{"tool": "...", "input": {...}, "model": "..."}]
    """

    if "gemini" in model_name.lower():
        # Gemini의 native tool calling format
        tool_calls = extract_gemini_tool_calls(raw_output)
    elif "deepseek" in model_name.lower():
        # DeepSeek의 배열 형식
        tool_calls = extract_deepseek_tool_calls(raw_output)
    elif "gpt-oss" in model_name.lower():
        # GPT-OSS의 텍스트 형식
        tool_calls = extract_gpt_oss_tool_calls(raw_output)
    else:
        # 기본: 텍스트 파싱
        tool_calls = extract_default_tool_calls(raw_output)

    # 정규화: 모든 형식을 통일된 Dict로
    normalized = []
    for call in tool_calls:
        normalized.append({
            "tool": call.get("tool_name") or call.get("name") or call.get("tool"),
            "input": call.get("tool_input") or call.get("input") or call.get("params"),
            "source_model": model_name,
        })

    return normalized
```

**파일 변경**: `src/agent/llm_agent.py` (약 80줄)
**비용**: 중간 (추출 로직 복잡함)

### 옵션 C: Manual Parsing 강화

**목표**: `parse_json_robust` 함수를 모델별 특성에 맞게 확장

**작업 2C-1**: 모델별 parsing 전략 추가

```python
# src/agent/llm_agent.py → parse_json_robust 함수 확장

def parse_json_robust(json_str: str, model_name: str = None, max_attempts: int = 10) -> Dict:
    """
    모델별 특성을 고려한 JSON 파싱

    현재: 일반적인 cleanup 5가지 시도
    변경: 모델별 추가 cleanup 전략
    """

    # 기본 cleanup (모든 모델)
    strategies = [
        lambda s: remove_markdown_code_blocks(s),
        lambda s: fix_json_quotes(s),
        lambda s: remove_trailing_commas(s),
        lambda s: unescape_unicode(s),
        lambda s: extract_json_object(s),
    ]

    # 모델별 추가 전략
    if model_name and "deepseek" in model_name.lower():
        strategies.extend([
            lambda s: remove_deepseek_artifacts(s),  # "最终答案" → "Final Answer" 변환
            lambda s: normalize_tool_name_format(s),  # tool_name vs name 정규화
            lambda s: fix_deepseek_json_arrays(s),   # [] vs {} 형식 수정
            lambda s: extract_between_markers(s, "```json", "```"),
            lambda s: extract_between_markers(s, "<json>", "</json>"),
        ])
    elif model_name and "gpt-oss" in model_name.lower():
        strategies.extend([
            lambda s: extract_between_markers(s, "### FINAL ANSWER ###", "###"),
            lambda s: remove_code_comments(s),
            lambda s: normalize_gpt_oss_format(s),
        ])

    # 시도
    for attempt, strategy in enumerate(strategies):
        try:
            cleaned = strategy(json_str)
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            if attempt == len(strategies) - 1:
                # 마지막 시도 실패
                logger.error(f"parse_json_robust failed after {len(strategies)} strategies")
                raise
            continue

    raise ValueError("parse_json_robust exhausted all strategies")
```

**파일 변경**: `src/agent/llm_agent.py` (약 120줄)
**비용**: 중간 (많은 cleanup 함수 필요)

### 작업 2-Final: Phase 1 결과에 따른 선택 및 구현

**의사 결정**:
- 에러 1 (Tool JSON 형식) → **옵션 B** 우선 (정규화)
- 에러 2 (Final Answer 형식) → **옵션 A+C** 조합
- 에러 3 (Tool 호출 제한) → **프롬프트 개선** (옵션 A)

**파일 변경**: Phase 1 결과에 따라 A, B, C 중 선택
**비용**: 중간 (선택된 옵션에 따라 50-150줄)

---

## 📊 Phase 3: 전략 평가 및 최종 결정

### 목표
Phase 1-2 완료 후, with_structured_output 구현 필요성 최종 판단

### 작업 3-1: GPT-OSS-120b 평가

**테스트 케이스**:

| 항목 | Gemini | DeepSeek | GPT-OSS | 추천 |
|------|--------|----------|---------|------|
| Tool Calling 안정성 | ✅ | ? | ? | ? |
| 응답 시간 | Fast | Medium | ? | ? |
| Cost per 1K tokens | $$ | $ | $ | ? |
| 한글 이해 능력 | Good | Excellent | ? | ? |

**사내 테스트 수행**:
```bash
# Phase 2 안정화 후, 동일 테스트 케이스로 GPT-OSS-120b 평가
# 결과: 더 안정적이면 GPT-OSS를 기준으로 재설계
#       DeepSeek이 안정적이면 DeepSeek 기준 진행
```

### 작업 3-2: with_structured_output 필요성 재평가

**평가 기준**:

```
IF Phase 2 안정화로 DeepSeek 정상 작동:
  → with_structured_output 필수 아님 (현재 ReAct + 최적화로 충분)
  → REQ-AGENT-0-1 종료 (완료 or "최소 변경으로 모델 호환성 달성")

ELSE (여전히 파싱 오류):
  → with_structured_output 구현 검토 필요
  → REQ-AGENT-0-2 (Gather-Then-Generate) 시작
```

**파일 변경**: 없음 (의사 결정 문서만)
**비용**: 없음

---

## 🗂️ 상태 추적

### Current Status
- Phase 1: 🔄 준비 중
- Phase 2: ⏳ 대기 중 (Phase 1 완료 필요)
- Phase 3: ⏳ 대기 중 (Phase 2 완료 필요)

### Milestone Dates (예상, 조정 가능)
- Phase 1 디버깅 로깅: 2025-12-06~07 (1일)
- Phase 1 사내 테스트: 2025-12-08~10 (2-3일, 사용자)
- Phase 1 분석: 2025-12-10~11 (1일)
- Phase 2 구현: 2025-12-12~14 (2-3일, 선택된 옵션에 따라)
- Phase 3 평가: 2025-12-15~17 (2-3일, 병렬 진행)

---

## 📌 Success Criteria

### Phase 1 완료 조건
- ✅ 디버깅 로깅 코드 추가 및 배포
- ✅ 사내에서 Gemini vs DeepSeek vs GPT-OSS 비교 테스트 완료
- ✅ 근본 원인 문서(ROOT_CAUSE_ANALYSIS.md) 작성
- ✅ 우선순위별 에러 목록 작성

### Phase 2 완료 조건
- ✅ 선택된 옵션 구현 (A, B, C 중 하나 또는 조합)
- ✅ 사내 환경에서 DeepSeek 정상 작동 확인
- ✅ 기존 Gemini 호환성 유지 확인
- ✅ pytest tests/agent/ 모두 통과

### Phase 3 완료 조건
- ✅ GPT-OSS-120b 평가 완료
- ✅ with_structured_output 필요성 최종 판단
- ✅ REQ-AGENT-0-1 최종 상태 결정 (완료 or 진행)
- ✅ 추후 계획 문서화

---

## 🔗 관련 문서

- **전체 전략**: `docs/feature/enhance_robust_agent_plan.md`
- **진행 추적**: `docs/progress/REQ-AGENT-0-1.md`
- **요구사항**: `docs/AGENT-REQUIREMENTS.md` (Lines 68-89)
- **근본 원인 분석**: `docs/feature/REQ-AGENT-0-1_ROOT_CAUSE_ANALYSIS.md` (작성 예정)
- **기술 리뷰**:
  - `docs/feature/REQ-AGENT-0-1_review_G.md` (Gemini's technical review)
  - `docs/feature/REQ-AGENT-0-1_review_CX.md` (CX's review in Korean)

---

**마지막 업데이트**: 2025-12-06
**작성자**: Claude Code
**상태**: 📋 Planning (Phase 1 준비)
