# Agent 강건성 개선 계획 (enhance_robust_agent_A)

## 1. 문제 요약

### 1.1 현상
| 환경 | 모델 | 상태 |
|------|------|------|
| 사외PC (공개망) | gemini-2.0-flash | 정상 동작 |
| 사내PC (폐쇄망) | deepseek-v3-0324 | 오동작 |

### 1.2 증상
- **Tool 호출 형식 문제**: DeepSeek이 JSON 대신 XML 형태로 도구 호출
- **Output 형식 불일치**: 모델이 약속된 ReAct 형식을 준수하지 않음
- **Structured Output 미지원**: DeepSeek-v3가 `response_format: json_schema` 미지원

### 1.3 근본 원인 분석

```
현재 아키텍처 (Gemini 최적화):
┌─────────────────────────────────────────────────────────────┐
│  create_react_agent (LangGraph v2)                          │
│  ├── Tool Calling: 모델의 native tool_calls 기능 사용        │
│  ├── Response Format: JSON structured output                │
│  └── Prompt: ReAct 텍스트 형식 (Thought/Action/Observation)  │
└─────────────────────────────────────────────────────────────┘
             ↓ Gemini: 정상 ↓ DeepSeek: 실패
```

**핵심 문제점:**
1. LangGraph `create_react_agent`는 모델의 native **Tool Calling API**를 사용
2. DeepSeek-v3는 OpenAI-compatible tool calling을 제한적으로 지원
3. 프롬프트는 텍스트 기반 ReAct 형식이지만, 실제 실행은 Tool Calling에 의존
4. 모델 간 Tool Calling 지원 수준 차이로 인한 불일치

---

## 2. 코드 분석 결과

### 2.1 현재 아키텍처 (`src/agent/`)

```
src/agent/
├── llm_agent.py          # 핵심: ItemGenAgent (create_react_agent 사용)
├── config.py             # LLM Provider 팩토리 (Strategy Pattern)
├── prompts/
│   ├── react_prompt.py   # 프롬프트 엔트리포인트
│   ├── prompt_content.py # ReAct 형식 규칙 (텍스트)
│   └── prompt_builder.py # Builder Pattern
├── tools/                # 6개 Tool 구현 (@tool 데코레이터)
├── output_converter.py   # Final Answer JSON 파싱
└── fastmcp_server.py     # Tool 목록 등록
```

### 2.2 문제가 되는 코드 영역

#### A. `llm_agent.py:370-376` - Agent 생성
```python
# 문제: create_react_agent는 모델의 Tool Calling을 자동으로 사용
self.executor = create_react_agent(
    model=self.llm,
    tools=self.tools,
    prompt=self.prompt,
    debug=AGENT_CONFIG.get("verbose", False),
    version="v2",  # LangGraph v2
)
```

**문제점**: DeepSeek이 Tool Calling을 제대로 지원하지 않으면 전체 파이프라인이 실패

#### B. `config.py:79-119` - LiteLLM Provider
```python
class LiteLLMProvider(LLMProvider):
    def create(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.3,
            max_tokens=8192,
            timeout=30,
        )
```

**문제점**: DeepSeek-v3의 특성 (tool calling 제한, json_schema 미지원)을 고려하지 않음

#### C. `prompt_content.py` - ReAct 프롬프트
```
현재 프롬프트 설계:
- 텍스트 기반 ReAct 형식 명시 (Thought/Action/Action Input/Observation)
- 그러나 실제 실행은 LangGraph의 Tool Calling 메커니즘에 의존
- 모델이 텍스트 형식을 무시하고 XML이나 다른 형식으로 응답할 수 있음
```

### 2.3 참조 문서 발견

| 문서 | 경로 | 내용 |
|------|------|------|
| Postmortem 1 | `docs/postmortem-prompt-escaping-solid-refactoring.md` | JSON 이스케이핑 문제 해결 |
| Postmortem 2 | (누락) | LiteLLM "No tool results" 에러 분석 필요 |
| SOLID Refactoring | `docs/PROMPT_SOLID_REFACTORING.md` | 프롬프트 아키텍처 개선 |

---

## 3. 개선 전략

### 3.1 전략 개요

```
개선된 아키텍처 (Multi-Model 지원):
┌─────────────────────────────────────────────────────────────┐
│  AgentRunner (새로운 Facade)                                │
│  ├── ModelCapabilityDetector: 모델 능력 자동 감지           │
│  ├── AgentFactory: 모델에 맞는 Agent 생성                    │
│  │   ├── ToolCallingAgent (Gemini, GPT-4)                  │
│  │   └── TextReActAgent (DeepSeek, 기타)                   │
│  ├── OutputNormalizer: 다양한 출력 형식 정규화               │
│  └── RetryStrategy: 형식 실패 시 재시도                      │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Phase 1: 즉시 적용 가능한 개선 (Low Risk)

#### Task 1.1: ModelCapabilityDetector 구현
- 목적: 모델별 지원 기능 자동 감지
- 파일: `src/agent/model_capability.py` (신규)

```python
# 구현 개념
class ModelCapability:
    supports_tool_calling: bool = True
    supports_json_schema: bool = True
    supports_function_calling: bool = True
    preferred_react_format: str = "tool_calling"  # or "text"

MODEL_CAPABILITIES = {
    "gemini-2.0-flash": ModelCapability(
        supports_tool_calling=True,
        supports_json_schema=True,
        preferred_react_format="tool_calling"
    ),
    "deepseek-v3": ModelCapability(
        supports_tool_calling=False,  # 제한적
        supports_json_schema=False,
        preferred_react_format="text"
    ),
}

def detect_capability(model_name: str) -> ModelCapability:
    """모델 이름에서 capability 감지"""
    for pattern, capability in MODEL_CAPABILITIES.items():
        if pattern in model_name.lower():
            return capability
    return ModelCapability()  # 기본값 (Tool Calling 시도)
```

#### Task 1.2: TextReActAgent 구현 (Text-based ReAct)
- 목적: Tool Calling 없이 순수 텍스트 기반 ReAct 실행
- 파일: `src/agent/text_react_agent.py` (신규)

```python
# 구현 개념
class TextReActAgent:
    """
    Tool Calling 없이 텍스트 기반 ReAct를 실행하는 Agent.

    동작 방식:
    1. 프롬프트에 도구 설명 포함 (함수 시그니처 형태)
    2. LLM이 "Action: tool_name" 텍스트로 응답
    3. "Action Input: {...}" JSON 파싱
    4. 도구 수동 실행
    5. "Observation: ..." 주입
    6. 반복 (Final Answer까지)
    """

    def __init__(self, llm, tools, prompt):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.prompt = prompt

    async def ainvoke(self, messages: list) -> dict:
        """텍스트 기반 ReAct 실행"""
        conversation = messages.copy()

        for iteration in range(MAX_ITERATIONS):
            # 1. LLM 호출
            response = await self.llm.ainvoke(conversation)
            content = response.content

            # 2. Final Answer 체크
            if "Final Answer:" in content:
                return {"messages": conversation + [response]}

            # 3. Action/Action Input 파싱
            action, action_input = self._parse_action(content)

            # 4. 도구 실행
            tool = self.tools.get(action)
            if tool:
                result = tool.invoke(action_input)
                observation = f"Observation: {json.dumps(result)}"
            else:
                observation = f"Observation: Tool '{action}' not found"

            # 5. Observation 추가
            conversation.append(response)
            conversation.append(HumanMessage(content=observation))

        return {"messages": conversation}

    def _parse_action(self, content: str) -> tuple[str, dict]:
        """텍스트에서 Action/Action Input 파싱"""
        # "Action: tool_name" 파싱
        action_match = re.search(r"Action:\s*(\w+)", content)
        action = action_match.group(1) if action_match else ""

        # "Action Input: {...}" 파싱 (JSON 또는 XML 모두 처리)
        input_match = re.search(r"Action Input:\s*(.+?)(?=\n|$)", content, re.DOTALL)
        if input_match:
            raw_input = input_match.group(1).strip()
            action_input = self._parse_tool_input(raw_input)
        else:
            action_input = {}

        return action, action_input

    def _parse_tool_input(self, raw: str) -> dict:
        """JSON 또는 XML 형식의 도구 입력 파싱"""
        # JSON 시도
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # XML 시도 (DeepSeek이 가끔 XML로 응답)
        try:
            return self._parse_xml_input(raw)
        except Exception:
            pass

        # Key=Value 형식 시도
        return self._parse_kv_input(raw)
```

#### Task 1.3: AgentFactory 구현
- 목적: 모델 능력에 따라 적절한 Agent 선택
- 파일: `src/agent/agent_factory.py` (신규)

```python
class AgentFactory:
    @staticmethod
    def create_agent(llm, tools, prompt) -> ToolCallingAgent | TextReActAgent:
        """모델 능력에 따라 적절한 Agent 생성"""
        model_name = getattr(llm, "model", "") or getattr(llm, "model_name", "")
        capability = detect_capability(model_name)

        if capability.preferred_react_format == "tool_calling":
            # 기존 LangGraph create_react_agent 사용
            return create_react_agent(model=llm, tools=tools, prompt=prompt)
        else:
            # 텍스트 기반 ReAct Agent 사용
            return TextReActAgent(llm=llm, tools=tools, prompt=prompt)
```

### 3.3 Phase 2: Output Parser 강화 (Medium Risk)

#### Task 2.1: MultiFormatOutputParser 구현
- 목적: JSON, XML, Key-Value 등 다양한 출력 형식 처리
- 파일: `src/agent/output_parser.py` (신규)

```python
class MultiFormatOutputParser:
    """다양한 LLM 출력 형식을 정규화된 형태로 변환"""

    @staticmethod
    def parse_tool_call(content: str) -> list[ToolCall]:
        """
        지원하는 형식:
        1. JSON: {"tool": "name", "args": {...}}
        2. XML: <tool name="..."><arg>...</arg></tool>
        3. Text: Action: name\nAction Input: {...}
        4. Function Call: tool_name(arg1, arg2)
        """
        parsers = [
            JSONToolCallParser,
            XMLToolCallParser,
            TextReActParser,
            FunctionCallParser,
        ]

        for parser in parsers:
            try:
                result = parser.parse(content)
                if result:
                    return result
            except Exception:
                continue

        return []

class XMLToolCallParser:
    """DeepSeek이 출력하는 XML 형식 파싱"""

    @staticmethod
    def parse(content: str) -> list[ToolCall] | None:
        # <tool_call> 또는 <function_call> 태그 찾기
        patterns = [
            r"<tool_call>\s*<name>(.+?)</name>\s*<arguments>(.+?)</arguments>\s*</tool_call>",
            r"<function_call>\s*<name>(.+?)</name>\s*<parameters>(.+?)</parameters>\s*</function_call>",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                return [
                    ToolCall(name=name.strip(), args=XMLToolCallParser._parse_args(args))
                    for name, args in matches
                ]
        return None
```

#### Task 2.2: FinalAnswerExtractor 강화
- 목적: 다양한 Final Answer 형식 처리
- 파일: `src/agent/output_converter.py` (수정)

```python
# 추가할 메서드
@staticmethod
def extract_final_answer(content: str) -> dict | list | None:
    """
    다양한 Final Answer 형식 지원:
    1. Final Answer: [JSON]
    2. Final Answer:\n```json\n[JSON]\n```
    3. <final_answer>[JSON]</final_answer>
    4. **Final Answer**: [JSON]
    """
    patterns = [
        r"Final Answer:\s*```json\s*(.+?)\s*```",
        r"Final Answer:\s*(.+?)(?:\n\nThought:|$)",
        r"<final_answer>\s*(.+?)\s*</final_answer>",
        r"\*\*Final Answer\*\*:\s*(.+?)(?:\n\n|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue

    return None
```

### 3.4 Phase 3: Provider 전략 개선 (Medium Risk)

#### Task 3.1: DeepSeekProvider 전용 구현
- 목적: DeepSeek 모델의 특성에 맞는 설정
- 파일: `src/agent/config.py` (수정)

```python
class DeepSeekProvider(LLMProvider):
    """
    DeepSeek 전용 Provider.

    주요 설정:
    - Tool Calling 비활성화 (불안정)
    - JSON mode 사용 (json_schema 대신)
    - 낮은 temperature (형식 일관성)
    """

    def create(self) -> ChatOpenAI:
        base_url = getenv("DEEPSEEK_BASE_URL") or getenv("LITELLM_BASE_URL")
        api_key = getenv("DEEPSEEK_API_KEY") or getenv("LITELLM_API_KEY", "sk-dummy")

        return ChatOpenAI(
            model="deepseek-chat",  # deepseek-v3
            api_key=api_key,
            base_url=base_url,
            temperature=0.1,  # 더 낮은 temperature로 형식 일관성 향상
            max_tokens=8192,
            timeout=60,  # 더 긴 타임아웃
            # Tool Calling은 TextReActAgent에서 수동 처리
        )

class LLMFactory:
    @staticmethod
    def get_provider() -> LLMProvider:
        model = getenv("LLM_MODEL", "").lower()

        if "deepseek" in model:
            return DeepSeekProvider()
        elif getenv("USE_LITE_LLM", "False").lower() == "true":
            return LiteLLMProvider()
        else:
            return GoogleGenerativeAIProvider()
```

#### Task 3.2: 프롬프트 강화 (DeepSeek 최적화)
- 목적: DeepSeek이 더 잘 따르는 프롬프트 형식
- 파일: `src/agent/prompts/prompt_content.py` (수정)

```python
# DeepSeek 전용 강화 지시문 추가
DEEPSEEK_FORMAT_ENFORCEMENT = """
=== CRITICAL OUTPUT FORMAT REQUIREMENTS ===

You MUST follow this EXACT format. No exceptions.

DO NOT use XML tags like <tool_call> or <function>.
DO NOT use markdown code blocks for tool calls.
ALWAYS use this plain text format:

```
Thought: [your reasoning here]
Action: [exact tool name from the list above]
Action Input: {"param1": "value1", "param2": "value2"}
```

WRONG (DO NOT DO THIS):
❌ <tool_call><name>get_user_profile</name>...</tool_call>
❌ ```json
   {"tool": "get_user_profile", ...}
   ```
❌ get_user_profile(user_id="...")

CORRECT (DO THIS):
✓ Thought: I need to get user profile information
✓ Action: get_user_profile
✓ Action Input: {"user_id": "e79a0ee1-2a36-4383-91c5-9a8a01f27b62"}
"""
```

### 3.5 Phase 4: 통합 테스트 및 검증 (High Priority)

#### Task 4.1: Multi-Model 테스트 스위트
- 목적: 다양한 모델에서 동작 검증
- 파일: `tests/agent/test_multi_model_compatibility.py` (신규)

```python
import pytest
from src.agent.agent_factory import AgentFactory
from src.agent.model_capability import detect_capability

@pytest.mark.parametrize("model_name,expected_format", [
    ("gemini-2.0-flash", "tool_calling"),
    ("deepseek-v3", "text"),
    ("deepseek-chat", "text"),
    ("gpt-4", "tool_calling"),
    ("claude-3", "tool_calling"),
])
def test_capability_detection(model_name, expected_format):
    capability = detect_capability(model_name)
    assert capability.preferred_react_format == expected_format

@pytest.mark.asyncio
async def test_text_react_agent_basic():
    """TextReActAgent가 텍스트 기반으로 도구를 호출하는지 확인"""
    # Mock LLM that returns text-based ReAct
    mock_llm = MockLLM(responses=[
        "Thought: I need to get user profile\nAction: get_user_profile\nAction Input: {\"user_id\": \"test-123\"}",
        "Thought: Got the profile, now I can answer\nFinal Answer: {\"status\": \"success\"}"
    ])

    agent = TextReActAgent(llm=mock_llm, tools=MOCK_TOOLS, prompt=TEST_PROMPT)
    result = await agent.ainvoke([HumanMessage(content="Get user profile")])

    assert "Final Answer" in result["messages"][-1].content
```

#### Task 4.2: Output Parser 테스트
- 목적: 다양한 출력 형식 파싱 검증
- 파일: `tests/agent/test_output_parser.py` (신규)

```python
class TestMultiFormatOutputParser:
    def test_parse_json_tool_call(self):
        content = 'Action Input: {"user_id": "123"}'
        result = MultiFormatOutputParser.parse_tool_call(content)
        assert result[0].args == {"user_id": "123"}

    def test_parse_xml_tool_call(self):
        content = '<tool_call><name>get_user_profile</name><arguments>{"user_id": "123"}</arguments></tool_call>'
        result = MultiFormatOutputParser.parse_tool_call(content)
        assert result[0].name == "get_user_profile"

    def test_parse_text_react(self):
        content = "Thought: ...\nAction: save_question\nAction Input: {\"stem\": \"What is AI?\"}"
        result = MultiFormatOutputParser.parse_tool_call(content)
        assert result[0].name == "save_question"
```

---

## 4. 구현 우선순위 및 일정

### 4.1 우선순위 매트릭스

| Phase | Task | 영향도 | 위험도 | 우선순위 |
|-------|------|--------|--------|----------|
| 1 | ModelCapabilityDetector | High | Low | P0 |
| 1 | TextReActAgent | High | Medium | P0 |
| 1 | AgentFactory | High | Low | P0 |
| 2 | MultiFormatOutputParser | High | Medium | P1 |
| 2 | FinalAnswerExtractor 강화 | Medium | Low | P1 |
| 3 | DeepSeekProvider | Medium | Low | P2 |
| 3 | 프롬프트 강화 | Medium | Low | P2 |
| 4 | Multi-Model 테스트 | High | Low | P1 |

### 4.2 구현 순서

```
Week 1: Phase 1 (핵심 인프라)
├── Day 1-2: ModelCapabilityDetector + 테스트
├── Day 3-4: TextReActAgent 기본 구현
└── Day 5: AgentFactory 통합

Week 2: Phase 2 (Output 처리)
├── Day 1-2: MultiFormatOutputParser (XML 지원)
├── Day 3: FinalAnswerExtractor 강화
└── Day 4-5: 통합 테스트

Week 3: Phase 3-4 (최적화 및 검증)
├── Day 1-2: DeepSeekProvider + 프롬프트 최적화
├── Day 3-4: Multi-Model 테스트 스위트
└── Day 5: 문서화 및 릴리스
```

---

## 5. 위험 요소 및 완화 방안

### 5.1 기술적 위험

| 위험 | 영향 | 확률 | 완화 방안 |
|------|------|------|-----------|
| TextReActAgent 루프 무한반복 | High | Medium | max_iterations + timeout 설정 |
| XML 파싱 실패 | Medium | Medium | 여러 파서 fallback chain |
| DeepSeek API 불안정 | High | Medium | 재시도 로직 + 폴백 |
| 프롬프트 변경으로 Gemini 영향 | High | Low | 모델별 프롬프트 분리 |

### 5.2 완화 코드 예시

```python
# 무한 루프 방지
class TextReActAgent:
    MAX_ITERATIONS = 10
    ITERATION_TIMEOUT = 120  # seconds

    async def ainvoke(self, messages):
        start_time = time.time()

        for i in range(self.MAX_ITERATIONS):
            if time.time() - start_time > self.ITERATION_TIMEOUT:
                logger.warning("Iteration timeout reached")
                break

            # ... 실행 로직 ...

        return self._create_error_response("Max iterations reached")
```

---

## 6. 참고 자료

### 6.1 LangChain/LangGraph 공식 문서
- [ReAct Agent Structured Output](https://langchain-ai.github.io/langgraph/how-tos/react-agent-structured-output/)
- [ReAct Agent from Scratch](https://langchain-ai.github.io/langgraph/how-tos/react-agent-from-scratch/)
- [LangChain + LangGraph 1.0](https://blog.langchain.com/langchain-langgraph-1dot0/)

### 6.2 DeepSeek 호환성 이슈
- [DeepSeek V3 Structured Output Issue #29282](https://github.com/langchain-ai/langchain/issues/29282)
- [LiteLLM DeepSeek JSON Issue #7580](https://github.com/BerriAI/litellm/issues/7580)
- [LiteLLM DeepSeek Docs](https://docs.litellm.ai/docs/providers/deepseek)

### 6.3 프로젝트 내부 문서
- `docs/postmortem-prompt-escaping-solid-refactoring.md`
- `docs/PROMPT_SOLID_REFACTORING.md`
- `docs/TOOL_DEFINITIONS_SUMMARY.md`

---

## 7. 결론

### 7.1 핵심 개선점 요약

1. **모델 능력 자동 감지**: Tool Calling 지원 여부에 따라 적절한 Agent 선택
2. **텍스트 기반 ReAct 대안**: Tool Calling 미지원 모델용 fallback
3. **다형 출력 파서**: JSON, XML, Text 등 다양한 형식 처리
4. **모델별 최적화**: Provider Strategy 패턴 강화

### 7.2 기대 효과

```
Before (현재):
- Gemini: ✅ 정상
- DeepSeek: ❌ 실패

After (개선 후):
- Gemini: ✅ 정상 (Tool Calling)
- DeepSeek: ✅ 정상 (Text ReAct)
- GPT-4: ✅ 정상 (Tool Calling)
- Claude: ✅ 정상 (Tool Calling)
- 기타: ⚠️ Text ReAct fallback
```

### 7.3 다음 단계

Phase 1 구현 완료 후:
1. 사내 환경에서 DeepSeek 테스트
2. 로그 수집 및 분석
3. 필요시 Phase 2-4 진행

---

*문서 작성: 2025-12-05*
*마지막 업데이트: 2025-12-05*
