# Agent 강건성 개선 계획 (enhance_robust_agent_A)

> **Version**: 1.1 (Updated with G, CX feedback)
> **Last Updated**: 2025-12-05

## 0. 동료 피드백 반영 요약

### 반영된 핵심 인사이트

| 출처 | 핵심 제안 | 반영 위치 |
|------|-----------|-----------|
| **G 문서** | `with_structured_output` 활용으로 수동 파싱 제거 | Phase 0 (신규) |
| **G 문서** | Two-Step "Gather-Then-Generate" 단순화 | Phase 0 (신규) |
| **G 문서** | 프롬프트 대폭 단순화 | Phase 3.2 강화 |
| **CX 문서** | `StructuredTool` with `args_schema` | Phase 2 (신규 Task) |
| **CX 문서** | `ActionSanitizer` 전처리 단계 | Phase 2 (신규 Task) |
| **CX 문서** | `parse_json_robust()` 전역 활용 | Phase 2 강화 |
| **CX 문서** | `src/agent/tests` 비어있음 | Phase 4 강화 |
| **CX 문서** | 구조화된 로깅 필요 | Phase 4 (신규 Task) |

---

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
개선된 아키텍처 (Multi-Model 지원) - v1.1:
┌─────────────────────────────────────────────────────────────┐
│  AgentRunner (새로운 Facade)                                │
│  ├── ModelCapabilityProfile: 모델 능력 프로파일             │
│  │   ├── supports_tool_calls: bool                         │
│  │   ├── supports_json_mode: bool                          │
│  │   └── needs_react_text: bool                            │
│  ├── AgentFactory: 모델에 맞는 Agent 생성                    │
│  │   ├── StructuredOutputAgent (Gemini, GPT-4) ← NEW       │
│  │   ├── ToolCallingAgent (Gemini, GPT-4)                  │
│  │   └── TextReActAgent (DeepSeek, 기타)                   │
│  ├── ActionSanitizer: XML/YAML → JSON 전처리 ← NEW         │
│  ├── OutputNormalizer: 다양한 출력 형식 정규화               │
│  └── StructuredLogging: 디버깅용 구조화 로그 ← NEW          │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Phase 0: 근본적 해결책 - Structured Output (G 문서 반영) ⭐ NEW

> **핵심 아이디어**: 수동 Final Answer 파싱을 제거하고, LangChain의 `with_structured_output`을 활용하여 모델에 관계없이 일관된 출력 보장

#### Task 0.1: `with_structured_output` 도입
- 목적: 수동 JSON 파싱 제거, 모델별 차이 추상화
- 파일: `src/agent/llm_agent.py` (수정)

```python
# 현재: 수동 Final Answer 파싱
def _parse_agent_output_generate(self, result, round_id):
    # 복잡한 JSON 추출 로직...
    json_str = AgentOutputConverter.parse_final_answer_json(content)
    # ...

# 개선: with_structured_output 사용
async def generate_questions(self, request) -> GenerateQuestionsResponse:
    # 1단계: 정보 수집 (기존 도구 호출)
    context = await self._gather_context(request)

    # 2단계: Structured Output으로 생성
    structured_llm = self.llm.with_structured_output(GenerateQuestionsResponse)
    response = await structured_llm.ainvoke(
        f"Generate {request.question_count} questions based on: {context}"
    )

    # 파싱 불필요 - 이미 Pydantic 객체
    return response
```

**장점:**
- LangChain이 모델별 차이를 내부적으로 처리 (JSON mode, function calling 등)
- `_parse_agent_output_generate`, `parse_json_robust` 등 복잡한 파싱 로직 제거 가능
- 타입 안전성 보장

#### Task 0.2: Two-Step "Gather-Then-Generate" 아키텍처
- 목적: 복잡한 ReAct 루프 단순화, LLM 호출 횟수 감소
- 파일: `src/agent/llm_agent.py` (수정)

```python
class SimplifiedItemGenAgent:
    """
    Two-Step 아키텍처:
    1. Gather: 도구로 컨텍스트 수집 (user_profile, keywords 등)
    2. Generate: with_structured_output으로 최종 결과 생성
    """

    async def generate_questions(self, request):
        # Step 1: Gather - 정보 수집 (도구 직접 호출)
        profile = get_user_profile(request.user_id)
        keywords = get_difficulty_keywords(profile["self_level"], request.domain)

        context = {
            "profile": profile,
            "keywords": keywords,
            "domain": request.domain,
            "count": request.question_count,
        }

        # Step 2: Generate - 구조화된 출력으로 생성
        structured_llm = self.llm.with_structured_output(GenerateQuestionsResponse)
        response = await structured_llm.ainvoke(
            self._build_generation_prompt(context)
        )

        # Step 3: 검증 및 저장 (Python 코드로 처리, LLM 루프 밖)
        validated_items = []
        for item in response.items:
            validation = validate_question_quality(item.stem, item.type, ...)
            if validation["is_valid"]:
                save_result = save_generated_question(...)
                validated_items.append(item)

        return GenerateQuestionsResponse(items=validated_items, ...)
```

**장점:**
- LLM 호출 횟수 감소 (10+ → 2-3)
- 검증/저장 로직이 Python 코드로 이동하여 예측 가능
- ReAct 형식 준수 필요 없음

#### Task 0.3: Pydantic 응답 모델 강화
- 목적: 도구 응답도 구조화
- 파일: `src/agent/tools/*.py` (수정)

```python
# 현재: dict 반환
@tool
def score_and_explain(...) -> dict[str, Any]:
    return {"is_correct": True, "score": 85, ...}

# 개선: Pydantic 모델 반환 + with_structured_output 내부 사용
class ScoreResult(BaseModel):
    is_correct: bool
    score: int = Field(ge=0, le=100)
    explanation: str
    keyword_matches: list[str] = []
    graded_at: str

def _call_llm_score_short_answer(...) -> ScoreResult:
    """LLM 호출 시 with_structured_output 사용"""
    structured_llm = llm.with_structured_output(ScoreResult)
    return structured_llm.invoke(prompt)
```

### 3.3 Phase 1: 즉시 적용 가능한 개선 (Low Risk)

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

### 3.4 Phase 2: Output Parser 강화 + StructuredTool (CX 문서 반영) ⭐ ENHANCED

#### Task 2.0: StructuredTool with args_schema (CX 문서) ⭐ NEW
- 목적: 도구 입력 자동 검증 및 coercion
- 파일: `src/agent/tools/*.py` (수정)

```python
# 현재: @tool 데코레이터만 사용 (스키마 없음)
@tool
def save_generated_question(
    item_type: str,
    stem: str,
    choices: list[str] | None = None,
    ...
) -> dict[str, Any]:
    ...

# 개선: StructuredTool with Pydantic args_schema
class SaveQuestionArgs(BaseModel):
    """Tool 5 입력 스키마 - LangGraph가 자동 검증"""
    item_type: Literal["multiple_choice", "true_false", "short_answer"]
    stem: str = Field(min_length=1, max_length=2000)
    choices: list[str] | None = None
    correct_key: str | None = None
    correct_keywords: list[str] | None = None
    difficulty: int = Field(ge=1, le=10, default=5)
    categories: list[str] = Field(default_factory=lambda: ["general"])
    round_id: str
    session_id: str = "unknown"
    validation_score: float | None = None

    @model_validator(mode="after")
    def validate_answer_fields(self):
        if self.item_type == "multiple_choice":
            if not self.correct_key or not self.choices:
                raise ValueError("MC requires correct_key and choices")
        elif self.item_type == "short_answer":
            if not self.correct_keywords:
                raise ValueError("SA requires correct_keywords")
        return self

# StructuredTool 생성
save_generated_question = StructuredTool.from_function(
    func=_save_generated_question_impl,
    name="save_generated_question",
    description="Save a validated question to the question bank",
    args_schema=SaveQuestionArgs,
)
```

**장점:**
- LangGraph가 자동으로 입력 검증
- 잘못된 타입 자동 coercion (string → int 등)
- 누락된 필수 필드 즉시 감지

#### Task 2.1: ActionSanitizer 전처리 단계 (CX 문서) ⭐ NEW
- 목적: LangGraph 실행 전 XML/YAML → JSON 변환
- 파일: `src/agent/action_sanitizer.py` (신규)

```python
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage
import re
import json

class ActionSanitizer:
    """
    LangGraph state machine에 삽입되는 전처리 단계.
    DeepSeek의 XML tool call을 JSON으로 변환.
    """

    XML_PATTERNS = [
        # <tool_call><name>...</name><arguments>...</arguments></tool_call>
        (r"<tool_call>\s*<name>(.+?)</name>\s*<arguments>(.+?)</arguments>\s*</tool_call>",
         lambda m: {"name": m.group(1).strip(), "args": m.group(2).strip()}),

        # <function name="..."><parameter>...</parameter></function>
        (r'<function\s+name="(.+?)"[^>]*>(.+?)</function>',
         lambda m: {"name": m.group(1), "args": m.group(2)}),
    ]

    @classmethod
    def sanitize(cls, state: dict) -> dict:
        """LangGraph state에서 마지막 AIMessage를 검사하고 정규화"""
        messages = state.get("messages", [])
        if not messages:
            return state

        last_message = messages[-1]
        if not isinstance(last_message, AIMessage):
            return state

        content = last_message.content
        sanitized = False

        for pattern, extractor in cls.XML_PATTERNS:
            matches = list(re.finditer(pattern, content, re.DOTALL))
            if matches:
                # XML을 JSON Action Input으로 변환
                for match in matches:
                    tool_info = extractor(match)
                    json_replacement = f"Action: {tool_info['name']}\nAction Input: {tool_info['args']}"
                    content = content.replace(match.group(0), json_replacement)
                sanitized = True

        if sanitized:
            logger.info(f"ActionSanitizer: Converted XML to JSON format")
            # 새 메시지로 교체
            messages[-1] = AIMessage(content=content)
            return {**state, "messages": messages}

        return state

# LangGraph에 삽입
def create_sanitized_react_agent(llm, tools, prompt):
    """ActionSanitizer가 포함된 ReAct Agent"""
    base_agent = create_react_agent(llm, tools, prompt)

    # 에이전트 노드 앞에 sanitizer 삽입
    return base_agent.pipe(RunnableLambda(ActionSanitizer.sanitize))
```

#### Task 2.2: parse_json_robust() 전역 활용 (CX 문서) ⭐ ENHANCED
- 목적: 기존 robust 파서가 사용되지 않는 곳에 적용
- 파일: `src/agent/tools/score_and_explain_tool.py` (수정)

```python
# 현재: 단순 json.loads 사용 (src/agent/tools/score_and_explain_tool.py:231)
try:
    result = json.loads(response_text)  # ❌ 실패 가능
except json.JSONDecodeError as e:
    logger.warning(f"Could not parse...")
    return DEFAULT_LLM_SCORE, "Unable to parse"

# 개선: parse_json_robust 또는 AgentOutputConverter 사용
from src.agent.llm_agent import parse_json_robust
# 또는
from src.agent.output_converter import AgentOutputConverter

try:
    result = parse_json_robust(response_text)  # ✅ 5가지 cleanup 전략
except json.JSONDecodeError:
    # 여전히 실패하면 기본값
    return DEFAULT_LLM_SCORE, "Unable to parse after robust attempts"
```

**적용 대상 파일:**
- `src/agent/tools/score_and_explain_tool.py:231` (_call_llm_score_short_answer)
- `src/agent/tools/score_and_explain_tool.py:391` (_generate_explanation)
- `src/agent/llm_agent.py:1253` (_parse_agent_output_score)

#### Task 2.3: MultiFormatOutputParser 구현
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

### 3.6 Phase 4: 통합 테스트 및 검증 (CX 문서 반영) ⭐ ENHANCED

> **CX 문서 지적**: `src/agent/tests` 디렉토리가 비어있음 - 테스트 필수

#### Task 4.0: 테스트 인프라 구축 (CX 문서) ⭐ NEW
- 목적: `src/agent/tests/` 디렉토리에 테스트 기반 구축
- 파일: `tests/agent/` (신규 디렉토리)

```
tests/agent/
├── __init__.py
├── conftest.py                      # 공통 fixtures
├── fixtures/
│   ├── mock_llm_responses.py        # 다양한 LLM 응답 mocks
│   ├── xml_tool_calls.py            # DeepSeek XML 형식 샘플
│   └── json_tool_calls.py           # Gemini JSON 형식 샘플
├── test_model_capability.py         # ModelCapabilityProfile 테스트
├── test_action_sanitizer.py         # XML → JSON 변환 테스트
├── test_structured_tools.py         # StructuredTool 검증 테스트
├── test_text_react_agent.py         # TextReActAgent 테스트
├── test_output_parser.py            # MultiFormatOutputParser 테스트
└── test_multi_model_compatibility.py # 통합 테스트
```

```python
# tests/agent/conftest.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

@pytest.fixture
def mock_gemini_response():
    """Gemini 스타일 JSON tool call 응답"""
    return AIMessage(
        content="",
        tool_calls=[{
            "name": "get_user_profile",
            "args": {"user_id": "test-123"},
            "id": "call_abc123"
        }]
    )

@pytest.fixture
def mock_deepseek_xml_response():
    """DeepSeek 스타일 XML 응답 - 실제 사내 로그에서 추출"""
    return AIMessage(
        content='''Thought: I need to get user profile
<tool_call>
<name>get_user_profile</name>
<arguments>{"user_id": "test-123"}</arguments>
</tool_call>'''
    )

@pytest.fixture
def mock_deepseek_malformed_response():
    """DeepSeek 스타일 잘못된 형식"""
    return AIMessage(
        content='''Thought: Getting profile
Action: get_user_profile
Action Input: user_id="test-123"  # JSON 아닌 key=value
'''
    )
```

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

#### Task 4.3: 구조화된 로깅 (CX 문서) ⭐ NEW
- 목적: 사내/사외 환경 간 디버깅 용이성 향상
- 파일: `src/agent/structured_logging.py` (신규)

```python
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any

@dataclass
class AgentExecutionLog:
    """구조화된 Agent 실행 로그"""
    timestamp: str
    model_name: str
    capability_profile: dict
    iteration: int
    step_type: str  # "tool_call" | "observation" | "final_answer"

    # 원본 vs 정규화된 데이터
    raw_content: str
    sanitized_content: str | None
    sanitization_applied: bool

    # 도구 호출 정보
    tool_name: str | None
    tool_args: dict | None
    tool_result: Any | None

    # 에러 정보
    error: str | None = None

class StructuredAgentLogger:
    """사내/사외 환경 모두에서 일관된 JSON 로그 출력"""

    def __init__(self, model_name: str, capability_profile: dict):
        self.model_name = model_name
        self.capability_profile = capability_profile
        self.iteration = 0
        self.logs: list[AgentExecutionLog] = []

    def log_tool_call(
        self,
        raw_content: str,
        sanitized_content: str | None,
        tool_name: str,
        tool_args: dict
    ):
        """도구 호출 로그"""
        log = AgentExecutionLog(
            timestamp=datetime.now().isoformat(),
            model_name=self.model_name,
            capability_profile=self.capability_profile,
            iteration=self.iteration,
            step_type="tool_call",
            raw_content=raw_content[:500],  # 너무 길면 잘라냄
            sanitized_content=sanitized_content[:500] if sanitized_content else None,
            sanitization_applied=sanitized_content is not None,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=None,
        )
        self._emit(log)

    def log_observation(self, tool_name: str, result: Any):
        """도구 실행 결과 로그"""
        log = AgentExecutionLog(
            timestamp=datetime.now().isoformat(),
            model_name=self.model_name,
            capability_profile=self.capability_profile,
            iteration=self.iteration,
            step_type="observation",
            raw_content="",
            sanitized_content=None,
            sanitization_applied=False,
            tool_name=tool_name,
            tool_args=None,
            tool_result=result,
        )
        self._emit(log)
        self.iteration += 1

    def _emit(self, log: AgentExecutionLog):
        """JSON 형식으로 로그 출력 - 파일 또는 stdout"""
        self.logs.append(log)
        # 구조화된 JSON 로그 출력
        logging.info(f"AGENT_LOG: {json.dumps(asdict(log), ensure_ascii=False)}")

    def export_session(self) -> str:
        """전체 세션 로그를 JSON 파일로 내보내기 (디버깅용)"""
        return json.dumps([asdict(log) for log in self.logs], indent=2, ensure_ascii=False)
```

**사용 예:**
```python
# ItemGenAgent에서 사용
class ItemGenAgent:
    def __init__(self, ...):
        self.logger = StructuredAgentLogger(
            model_name=self.llm.model,
            capability_profile=asdict(self.capability)
        )

    async def _execute_tool(self, raw_content: str, tool_call: ToolCall):
        # 로그 기록
        self.logger.log_tool_call(
            raw_content=raw_content,
            sanitized_content=sanitized if was_sanitized else None,
            tool_name=tool_call.name,
            tool_args=tool_call.args
        )

        result = self.tools[tool_call.name].invoke(tool_call.args)

        self.logger.log_observation(tool_call.name, result)
```

**장점:**
- 사내 DeepSeek 실행 로그를 JSON 파일로 내보내기 가능
- 사외에서 동일 형식으로 로드하여 비교 분석
- grep/jq로 쉽게 필터링 가능

---

## 4. 구현 우선순위 및 일정

### 4.1 우선순위 매트릭스 (Updated with G, CX feedback)

| Phase | Task | 영향도 | 위험도 | 우선순위 | 출처 |
|-------|------|--------|--------|----------|------|
| **0** | with_structured_output 도입 | **Critical** | Medium | **P0** | G 문서 |
| **0** | Two-Step Gather-Generate | **Critical** | Medium | **P0** | G 문서 |
| **0** | Pydantic 응답 모델 강화 | High | Low | P0 | G 문서 |
| 1 | ModelCapabilityProfile | High | Low | P0 | A+CX |
| 1 | TextReActAgent | High | Medium | P1 | A |
| 1 | AgentFactory | High | Low | P1 | A |
| **2** | StructuredTool args_schema | **High** | Low | **P0** | CX 문서 |
| **2** | ActionSanitizer | **High** | Medium | **P0** | CX 문서 |
| **2** | parse_json_robust 전역 활용 | High | Low | P1 | CX 문서 |
| 2 | MultiFormatOutputParser | High | Medium | P1 | A |
| 3 | DeepSeekProvider | Medium | Low | P2 | A |
| 3 | 프롬프트 단순화 | Medium | Low | P2 | G 문서 |
| **4** | 테스트 인프라 구축 | **High** | Low | **P0** | CX 문서 |
| 4 | Multi-Model 테스트 | High | Low | P1 | A |
| **4** | 구조화된 로깅 | **High** | Low | **P1** | CX 문서 |

### 4.2 전략적 접근 방식

```
┌─────────────────────────────────────────────────────────────┐
│  Option A: "근본적 해결" (G 문서 권장)                        │
│  ───────────────────────────────────────                    │
│  Phase 0 집중 → with_structured_output으로 파싱 문제 제거    │
│  장점: 깔끔한 해결, 유지보수 용이                             │
│  단점: 큰 리팩토링 필요, 기존 ReAct 로직 대폭 수정            │
└─────────────────────────────────────────────────────────────┘
                           vs
┌─────────────────────────────────────────────────────────────┐
│  Option B: "점진적 개선" (A 문서 + CX 문서 조합)              │
│  ───────────────────────────────────────                    │
│  Phase 1-2 집중 → 기존 구조 유지하면서 호환성 레이어 추가     │
│  장점: 낮은 위험, 단계적 검증 가능                            │
│  단점: 복잡도 증가, 임시방편 느낌                             │
└─────────────────────────────────────────────────────────────┘
```

**권장: Option A + 필수 B 요소 조합**
- Phase 0 (G 문서)의 `with_structured_output`을 먼저 시도
- 실패 시 Phase 2 (CX 문서)의 `ActionSanitizer`로 fallback
- 테스트/로깅은 어느 옵션이든 필수

### 4.3 구현 순서 (Updated)

```
Week 1: Phase 0 + 테스트 인프라 (핵심)
├── Day 1: 테스트 인프라 구축 (tests/agent/)
├── Day 2: ModelCapabilityProfile 구현 + 테스트
├── Day 3-4: with_structured_output 도입 (llm_agent.py)
└── Day 5: Two-Step 아키텍처 프로토타입

Week 2: Phase 2 (호환성 레이어)
├── Day 1: StructuredTool args_schema 마이그레이션
├── Day 2-3: ActionSanitizer 구현 + 테스트
├── Day 4: parse_json_robust 전역 적용
└── Day 5: 구조화된 로깅 구현

Week 3: Phase 1 + 검증
├── Day 1-2: TextReActAgent (fallback용)
├── Day 3: AgentFactory 통합
├── Day 4: Multi-Model 테스트 스위트
└── Day 5: 사내 환경 검증 + 문서화
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

### 7.1 핵심 개선점 요약 (Updated with G, CX feedback)

| 카테고리 | 개선점 | 출처 |
|----------|--------|------|
| **근본적 해결** | `with_structured_output`으로 수동 파싱 제거 | G 문서 |
| **아키텍처** | Two-Step "Gather-Then-Generate" 단순화 | G 문서 |
| **호환성** | `ActionSanitizer`로 XML → JSON 전처리 | CX 문서 |
| **타입 안전성** | `StructuredTool` with `args_schema` | CX 문서 |
| **파싱 강화** | `parse_json_robust` 전역 활용 | CX 문서 |
| **테스트** | `tests/agent/` 테스트 인프라 구축 | CX 문서 |
| **디버깅** | 구조화된 JSON 로깅 | CX 문서 |
| **Fallback** | `TextReActAgent` (Tool Calling 미지원 시) | A 문서 |
| **프로파일** | `ModelCapabilityProfile` 모델별 능력 감지 | A+CX |

### 7.2 기대 효과

```
Before (현재):
┌─────────────────────────────────────────────┐
│ Gemini:    ✅ 정상 (native tool calling)    │
│ DeepSeek:  ❌ 실패 (XML 출력, 파싱 에러)     │
│ GPT-4:     ⚠️ 미테스트                       │
│ Claude:    ⚠️ 미테스트                       │
│ 디버깅:    😰 수동 로그 복사 필요             │
└─────────────────────────────────────────────┘

After (개선 후):
┌─────────────────────────────────────────────┐
│ Gemini:    ✅ 정상 (with_structured_output) │
│ DeepSeek:  ✅ 정상 (Sanitizer + TextReAct)  │
│ GPT-4:     ✅ 정상 (with_structured_output) │
│ Claude:    ✅ 정상 (with_structured_output) │
│ 기타:      ⚠️ TextReActAgent fallback       │
│ 디버깅:    😊 JSON 로그 자동 내보내기        │
└─────────────────────────────────────────────┘
```

### 7.3 다음 단계

1. **팀 논의**: Option A (근본적 해결) vs Option B (점진적 개선) 선택
2. **Phase 0 PoC**: `with_structured_output` 먼저 사내 DeepSeek에서 테스트
   - 성공 시: Phase 0 중심으로 진행
   - 실패 시: Phase 1-2 중심으로 진행 (ActionSanitizer 등)
3. **테스트 인프라**: 어느 옵션이든 `tests/agent/` 먼저 구축
4. **구조화된 로깅**: 사내/사외 디버깅 용이성을 위해 조기 적용

### 7.4 피드백 반영 완료

- [x] G 문서: `with_structured_output` 활용 → Phase 0 추가
- [x] G 문서: Two-Step 아키텍처 → Task 0.2 추가
- [x] G 문서: 프롬프트 단순화 → Phase 3.2 언급
- [x] CX 문서: `StructuredTool` args_schema → Task 2.0 추가
- [x] CX 문서: `ActionSanitizer` → Task 2.1 추가
- [x] CX 문서: `parse_json_robust` 전역 활용 → Task 2.2 추가
- [x] CX 문서: 테스트 부재 → Task 4.0 추가
- [x] CX 문서: 구조화된 로깅 → Task 4.3 추가

---

*문서 작성: 2025-12-05*
*마지막 업데이트: 2025-12-05 (v1.1 - G, CX 피드백 반영)*
