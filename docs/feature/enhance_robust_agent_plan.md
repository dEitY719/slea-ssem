# Agent 안정화 전략 재검토 (Enhanced Plan)

**작성일**: 2025-12-06
**대상**: REQ-AGENT-0-1 재설계
**배경**: 사내 마이그레이션 후 에러 발생 + Over-engineering 우려

---

## 📊 현황 분석

### ✅ 확인된 사실들

| 항목 | 상태 | 근거 |
|------|------|------|
| **Gemini (개발)** | ✅ 작동 | ReAct + Tool Calling 검증 완료 |
| **Tool Calling 지원** | ✅ 양쪽 | DeepSeek-v3-0324, GPT-OSS-120b 모두 지원 |
| **LangChain with_structured_output** | ❓ 재검토 필요 | DeepSeek 미지원 확실하지 않음 |
| **사내 마이그레이션** | ❌ 에러 발생 | 실제 문제 원인 파악 필요 |

### 🔴 내가 놓친 부분

```
❌ 이전 분석:
   with_structured_output 미지원
   → 복잡한 Gather-Then-Generate 아키텍처 제안
   → Over-engineering 위험

✅ 재검토:
   Tool Calling이 양쪽 모두 가능
   → 현재 ReAct + Tool 구조 유지 가능
   → 실제 문제는 무엇인가? (model-specific 호환성?)
```

---

## 🎯 사용자 요구사항 재해석

### 명확한 의도
```
최종 목표: 사내 환경 서비스 (DeepSeek-v3-0324 또는 GPT-OSS-120b)
현재 상황: Gemini에서 ReAct + Tool 검증 완료 ✅
문제: 사내 마이그레이션 후 에러 발생 ❌
해결책: 최소 변경으로 LLM 모델 의존성 제거

옵션:
  1. DeepSeek-v3-0324 지원 추가 (에러 해결)
  2. GPT-OSS-120b를 기준으로 재설계 (더 나을 경우)
```

### 핵심: With_structured_output이 정말 필요한가?

**사용자의 의문점**:
- Tool Calling이 양쪽 모두 가능한데?
- 왜 복잡한 with_structured_output 도입이 필요한가?
- 현재 ReAct + Tool 구조로는 충분하지 않은가?

**내 재검토**:
✅ 타당한 질문이다. with_structured_output은:
- **이점**: JSON 응답 보장, 파싱 안정성 ↑
- **비용**: 아키텍처 변경, Tool Calling 제약, Over-engineering

→ **현재 상황에서는 필수가 아닐 수 있다**

---

## 💡 재제안: 최소 변경 접근법

### 현재 구조 유지 + 모델 호환성 개선

```python
# 기본 원칙: ReAct + Tool Calling 유지
# 변경 범위: 모델별 prompt/config 최적화

current_architecture = {
    "Gemini (개발)": "ReAct + Tool → Manual Parsing ✅",
    "DeepSeek-v3-0324": "ReAct + Tool → Manual Parsing ❌",
    "GPT-OSS-120b": "ReAct + Tool → Manual Parsing ?"
}

improved_architecture = {
    "Gemini (개발)": "ReAct + Tool → Optimized Manual Parsing",
    "DeepSeek-v3-0324": "ReAct + Tool → Model-Specific Parsing",
    "GPT-OSS-120b": "ReAct + Tool → Model-Specific Parsing (if chosen)"
}
```

### 실제 문제는 무엇인가?

**사내 마이그레이션 에러의 가능한 원인들**:

1. **Tool Calling 형식 차이**
   - Gemini vs DeepSeek의 tool call JSON 형식
   - 문제: `ToolMessage` 처리 방식 불일치

2. **Prompt 호환성**
   - Gemini에 최적화된 ReAct prompt
   - DeepSeek가 이해 못 하는 지시사항 포함
   - 예: "Final Answer:" 형식 인식 차이

3. **Tool 실행 순서/로직**
   - Tool 1-5의 호출 순서 (선택사항 vs 필수)
   - 에러 시 retry 로직
   - Tool 결과 parsing 실패

4. **LangChain + LiteLLM 호환성**
   - Message 형식 변환
   - Tool schema 인식 차이

---

## 📋 추천: 3단계 해결책

### ✅ **1단계: 근본 원인 파악 (즉시)**

```python
# 사내 환경에서 디버깅 로깅 추가
# generate_questions 실행 중 다음 기록:

1. ReAct agent 실행 결과
   - intermediate_steps 확인
   - messages 형식 확인
   - Tool call JSON 형식 확인

2. Manual parsing 단계
   - parse_json_robust 실패 지점
   - AgentOutputConverter 에러
   - 어느 단계에서 망가지는가?

3. DeepSeek vs GPT-OSS-120b 비교
   - 동일 요청에 대한 응답 차이
   - Tool call 형식 차이
   - JSON 추출 난도 비교
```

**예상 결과**:
```
DeepSeek 에러 원인:
❌ Tool JSON 형식: {...} vs [...]
❌ Final Answer 인식 실패
❌ Tool 호출 반복 안 됨
```

### ✅ **2단계: 최소 변경으로 호환성 개선**

**Option A: 모델별 프롬프트 최적화**
```python
# src/agent/prompts/react_prompt.py에 모델별 버전 추가

def get_react_prompt(model_name: str):
    if "gemini" in model_name:
        return GEMINI_OPTIMIZED_PROMPT
    elif "deepseek" in model_name:
        return DEEPSEEK_OPTIMIZED_PROMPT
    elif "gpt-oss" in model_name:
        return GPT_OSS_OPTIMIZED_PROMPT
    else:
        return DEFAULT_PROMPT
```

**Option B: Tool Call 형식 정규화**
```python
# src/agent/llm_agent.py의 _extract_tool_results 개선

def _extract_tool_results(self, result, tool_name):
    # Gemini, DeepSeek, GPT-OSS의 서로 다른 Tool call 형식 수용
    # → 통일된 형식으로 변환

    tool_calls = extract_tool_calls(result)  # 모델별 차이 흡수
    return normalized_results  # 일관된 형식
```

**Option C: Manual Parsing 강화**
```python
# src/agent/llm_agent.py의 parse_json_robust 향상

def parse_json_robust(json_str, model_name=None, max_attempts=10):
    # 모델별 특성에 맞는 cleanup 전략 추가

    if "deepseek" in model_name:
        strategies = [
            remove_deepseek_artifacts,
            normalize_final_answer,
            extract_json_array_objects,
            # ... 더 많은 시도
        ]
    return parse_with_strategies(json_str, strategies)
```

### ✅ **3단계: GPT-OSS-120b 평가 (병렬 진행)**

```python
# 사내에서 GPT-OSS-120b 테스트

test_cases = [
    "Tool Calling 안정성",
    "Final Answer 인식",
    "Tool 반복 호출",
    "에러 처리 및 복구",
    "응답 시간",
    "비용 효율성"
]

if gpt_oss_120b_better:
    → GPT-OSS-120b를 기준으로 재설계
else:
    → DeepSeek-v3-0324 호환성 집중
```

---

## 🚨 With_Structured_Output 재평가

### 비용 vs 이득

| 측면 | With_Structured_Output | 현재 ReAct + Tool |
|------|----------------------|-------------------|
| **아키텍처** | 대규모 변경 필요 | 최소 변경 |
| **Tool Calling** | 제약 있음 | 완전 지원 |
| **JSON 안정성** | ✅ 높음 | ⚠️ 파싱 의존 |
| **개발 비용** | ⚠️ 높음 (새 아키텍처) | ✅ 낮음 (prompt/config) |
| **배포 위험** | ⚠️ 높음 (검증 필요) | ✅ 낮음 (기존 검증됨) |
| **Model Independence** | ✅ 이상적 | ⚠️ 실제는 가능 |

### 결론

**현재 상황에서는 with_structured_output이 과도할 가능성**:

```
이상:    모든 모델이 동일 코드로 작동
현실:    Tool Calling + Prompt 최적화로 충분

with_structured_output = 좋지만 필수는 아님
→ 추후 안정화 단계에서 고려
```

---

## 🎯 최종 권장사항

### Phase 1: 긴급 안정화 (1-2주)

**목표**: 사내 환경에서 DeepSeek-v3-0324 또는 GPT-OSS-120b 정상 작동

**작업**:
1. 실제 에러 원인 파악 (디버깅 로깅)
2. 모델별 프롬프트/config 최적화
3. Manual parsing 강화 (parse_json_robust 개선)
4. 기존 ReAct + Tool 구조 유지

**기대 효과**:
- ✅ 최소 코드 변경
- ✅ 배포 위험 낮음
- ✅ 빠른 문제 해결

### Phase 2: 구조 개선 (추후)

**목표**: 모델 독립성 강화 + 파싱 안정성 개선

**검토 항목**:
1. with_structured_output 실제 필요성 재평가
2. Gather-Then-Generate 아키텍처 (선택사항)
3. 통일된 Tool Call 형식화
4. 자동 모델 호환성 감지

**시기**: 안정화 후 (비용 대비 이득이 명확할 때)

---

## 📌 최종 결론

### 현재 REQ-AGENT-0-1 상태

```
❌ 문제점:
   - with_structured_output 도입 과도
   - 현재 ReAct + Tool 구조로 충분
   - 사내 실제 에러와 무관

✅ 권장:
   - REQ-AGENT-0-1 재정의: "Model-specific 호환성 개선"
   - 현재 구조 유지
   - 긴급: 사내 에러 원인 파악 & 해결
   - 추후: 안정성 개선 후 재검토
```

### 실행 계획

```
Week 1:
  └─ 사내 에러 디버깅 (DeepSeek-v3-0324)
  └─ GPT-OSS-120b 평가
  └─ 근본 원인 파악

Week 2:
  └─ 모델별 프롬프트 최적화
  └─ Manual parsing 강화
  └─ 안정성 테스트

추후 (안정화 후):
  └─ with_structured_output 재평가
  └─ 구조 개선 (필요시)
```

---

## ❓ 동료 피드백 반영

### G 검토자의 지적 재평가

```
❌ "with_structured_output을 꼭 구현해야 한다"

✅ "현재 ReAct + Tool로 충분하다"
   (Tool Calling 양쪽 지원하므로)

→ 대신, 모델별 호환성 개선이 실제 필요
```

### CX 검토자의 지적 재평가

```
❌ "Acceptance Criteria = with_structured_output 도입"

✅ "Acceptance Criteria = 모델 독립적 안정적 문항 생성"
   (with_structured_output은 수단, 목적 아님)

→ 현재 ReAct + 모델별 최적화로 달성 가능
```

---

## 🏁 결론

**REQ-AGENT-0-1 재정의**:

```
이전: "with_structured_output 도입" (Over-engineering)
↓
이후: "다중 LLM 모델 호환 안정화" (실용적)

목표:
  ✅ Gemini (개발): 이미 작동
  ✅ DeepSeek-v3-0324 또는 GPT-OSS-120b (사내): 정상 작동
  ✅ 최소 코드 변경으로 달성
```

이 방향이 **프로젝트 현실과 일치**하며, **빠른 문제 해결**에도 최적입니다.
