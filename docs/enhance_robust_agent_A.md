# Agent 강건성 개선 계획 (enhance_robust_agent_A)

> **Version**: 1.1 (Updated with G, CX feedback)
> **Last Updated**: 2025-12-05

## 0. 동료 피드백 반영 요약 (v1.2 - 최종 검토 반영)

### 0.1 1차 피드백 통합 (v1.1)

| 출처 | 핵심 제안 | 반영 위치 |
|------|-----------|-----------|
| **G 문서** | `with_structured_output` 활용으로 수동 파싱 제거 | Phase 0 (신규) |
| **G 문서** | Two-Step "Gather-Then-Generate" 단순화 | Phase 0 (신규) |
| **CX 문서** | `StructuredTool` with `args_schema` | Phase 2 (신규 Task) |
| **CX 문서** | `ActionSanitizer` 전처리 단계 | Phase 2 (신규 Task) |
| **CX 문서** | `tests/agent/` 테스트 인프라 구축 | Phase 4 (신규 Task) |

### 0.2 최종 검토 반영 (v1.2)

**CX의 5가지 핵심 지적:**

| # | 문제 | 해결책 | 반영 위치 |
|---|------|--------|-----------|
| 1 | Phase 0의 위험 관리 부족 | ModelCapability 먼저 + 단계적 rollout | Section 3.2 강화 |
| 2 | Gather 단계의 에러 처리 미흡 | Gather도 ErrorHandler 적용 | Section 3.2.2 신규 |
| 3 | TextReActAgent와 AGENT_CONFIG 미연동 | AGENT_CONFIG 파라미터 통합 | Section 3.3.1 신규 |
| 4 | 테스트가 unit만 있음 | e2e 시나리오 추가 | Section 4.4 신규 |
| 5 | DeepSeekProvider vs LiteLLM 충돌 | 명시적 환경 변수 + precedence | Section 3.4 신규 |

**G의 3가지 강화 제안:**

| # | 제안 | 효과 | 우선순위 |
|---|------|------|----------|
| 1 | ModelCapability를 YAML 외부화 | 배포 없이 설정 변경 | P1 (추가) |
| 2 | ResilientAgentExecutor 자동 fallback | Self-healing agent | P0 (추가) |
| 3 | Key Performance Metrics 정의 | 성과 측정 및 비교 | P1 (추가) |

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
개선된 아키텍처 (DeepSeek 호환성 검증 - v1.2):
┌─────────────────────────────────────────────────────────────┐
│  AgentRunner (새로운 Facade)                                │
│  ├── ModelCapabilityProfile: 모델 능력 프로파일             │
│  │   ├── supports_tool_calls: bool                         │
│  │   ├── supports_json_mode: bool                          │
│  │   └── needs_react_text: bool                            │
│  ├── AgentFactory: 모델에 맞는 Agent 생성                    │
│  │   ├── StructuredOutputAgent (Gemini - 개발환경용)      │
│  │   ├── ToolCallingAgent (Gemini - 개발환경용)            │
│  │   └── TextReActAgent (DeepSeek - 프로덕션용) ← FOCUS   │
│  ├── ActionSanitizer: XML/YAML → JSON 전처리 ← NEW         │
│  ├── OutputNormalizer: 다양한 출력 형식 정규화               │
│  └── StructuredLogging: 디버깅용 구조화 로그 ← NEW          │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Phase 0: 근본적 해결책 - Structured Output (G 문서 반영, CX 위험 관리 추가) ⭐ NEW

> **핵심 아이디어**: 수동 Final Answer 파싱을 제거하고, LangChain의 `with_structured_output`을 활용하여 개발 환경(Gemini)에서 완벽하게 검증한 후 프로덕션(DeepSeek)에 배포
>
> **🎯 전략**: 개발(Gemini, 완벽한 검증) → 프로덕션(DeepSeek, 검증된 코드)
> - **Phase 0a**: Gemini에서만 `with_structured_output` 활성화 (완전한 로그 수집 + 메트릭 검증)
> - **Phase 0b-0c**: TextReActAgent + ActionSanitizer로 DeepSeek 호환성 확보
> - **Feature Flag**: `ENABLE_STRUCTURED_OUTPUT` 환경 변수로 Gemini 개발환경에서 제어

#### Task 0.0: 위험 관리 전략 (CX 검토 반영) ⭐ CRITICAL

```python
# src/agent/config.py - 새로운 설정
STRUCTURED_OUTPUT_CONFIG = {
    "enabled_by_default": getenv("ENABLE_STRUCTURED_OUTPUT", "false").lower() == "true",
    "supported_models": [
        "gemini-*",  # Gemini는 기본 지원
    ],
    "rollout_models": [
        # "deepseek-*",  # 나중에 활성화
    ]
}

def should_use_structured_output(model_name: str) -> bool:
    """모델별로 with_structured_output 사용 여부 결정"""
    if not STRUCTURED_OUTPUT_CONFIG["enabled_by_default"]:
        return False

    for pattern in STRUCTURED_OUTPUT_CONFIG["supported_models"]:
        if model_name.lower().startswith(pattern.replace("*", "")):
            return True

    return False
```

**안전한 배포 계획:**
1. **Phase 0a** (Week 1-2): Gemini에서만 `with_structured_output` 활성화
   - 환경: `ENABLE_STRUCTURED_OUTPUT=true` (Gemini만)
   - 검증: 완전한 로그 수집 및 메트릭 검증
2. **Phase 0b** (Week 3-4): DeepSeek 준비
   - Feature flag 추가 후 테스트
   - ActionSanitizer 동시 활성화
3. **Phase 0c** (Week 5+): 프로덕션 롤아웃

#### Task 0.1: `with_structured_output` 도입 (Gemini용)
- 목적: 수동 JSON 파싱 제거, 모델별 차이 추상화
- 파일: `src/agent/llm_agent.py` (수정)
- **주의**: `should_use_structured_output()`로 감싸서 안전하게 실행

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

#### Task 0.2: Two-Step "Gather-Then-Generate" 아키텍처 (CX 에러 처리 강화) ⭐ NEW
- 목적: 복잡한 ReAct 루프 단순화, LLM 호출 횟수 감소
- 파일: `src/agent/llm_agent.py` (수정)
- **⚠️ CX 지적 반영**: Gather 단계도 ErrorHandler/retry 정책 적용

```python
from src.backend.utils.error_handler import ErrorHandler

class SimplifiedItemGenAgent:
    """
    Two-Step 아키텍처 (CX 에러 처리 강화):
    1. Gather: 도구로 컨텍스트 수집 (user_profile, keywords 등)
       ⚠️ 기존 ErrorHandler/retry 정책 적용
    2. Generate: with_structured_output으로 최종 결과 생성
    """

    def __init__(self, ...):
        self.error_handler = ErrorHandler()  # 기존 재시도 정책

    async def generate_questions(self, request):
        # Step 1: Gather - 정보 수집 (도구 호출, ErrorHandler 적용)
        try:
            profile = await self.error_handler.retry_with_backoff(
                lambda: get_user_profile(request.user_id),
                max_retries=3,
                backoff_factor=2
            )
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            profile = self._get_default_profile()

        try:
            keywords = await self.error_handler.retry_with_backoff(
                lambda: get_difficulty_keywords(profile["self_level"], request.domain),
                max_retries=2,
                backoff_factor=2
            )
        except Exception as e:
            logger.error(f"Failed to get keywords: {e}")
            keywords = self._get_default_keywords()

        context = {
            "profile": profile,
            "keywords": keywords,
            "domain": request.domain,
            "count": request.question_count,
        }

        # Step 2: Generate - 구조화된 출력으로 생성
        if should_use_structured_output(self.llm.model):
            structured_llm = self.llm.with_structured_output(GenerateQuestionsResponse)
            response = await structured_llm.ainvoke(
                self._build_generation_prompt(context)
            )
        else:
            # Fallback: TextReActAgent 사용
            response = await self.text_react_agent.ainvoke(context)

        # Step 3: 검증 및 저장 (Python 코드로 처리, LLM 루프 밖)
        validated_items = []
        for item in response.items:
            validation = validate_question_quality(item.stem, item.type, ...)
            if validation["is_valid"]:
                save_result = save_generated_question(...)
                validated_items.append(item)

        return GenerateQuestionsResponse(items=validated_items, ...)
```

**중요 변경:**
- ✅ Gather 단계도 ErrorHandler/retry 정책 적용 (기존과 동일)
- ✅ Generate 단계에서 `should_use_structured_output()` 검사
- ✅ 실패 시 TextReActAgent로 fallback
- ✅ 모든 도구 호출이 기존 재시도 메커니즘 활용

**장점:**
- LLM 호출 횟수 감소 (10+ → 2-3)
- 기존 ErrorHandler/retry/queuing 모두 적용
- 구조화된 로깅으로 전 단계 추적 가능

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

### 3.3 Phase 1: Resilient Agent Executor + 기본 인프라 (G 제안 추가) ⭐ ENHANCED

#### Task 1.0: ResilientAgentExecutor (G 제안, CX 안전성) ⭐ P0 PRIORITY
- 목적: primary (structured) → fallback (text) 자동 전환
- 파일: `src/agent/resilient_executor.py` (신규)

```python
class ResilientAgentExecutor:
    """
    G의 제안: primary → fallback으로 자동 전환하는 self-healing agent

    1차 시도: StructuredOutputAgent (빠르고 효율적)
    실패 시: TextReActAgent + ActionSanitizer (느리지만 견고)
    """

    def __init__(self, llm, tools, prompt, capability_profile):
        self.llm = llm
        self.tools = tools
        self.prompt = prompt
        self.capability = capability_profile

        # Primary agent
        if capability_profile.supports_structured_output:
            self.primary_agent = StructuredOutputAgent(llm, tools, prompt)
        else:
            self.primary_agent = None

        # Fallback agent (항상 준비)
        self.fallback_agent = TextReActAgent(llm, tools, prompt)
        self.fallback_agent = self.fallback_agent.pipe(RunnableLambda(ActionSanitizer.sanitize))

        # Logger
        self.logger = StructuredAgentLogger(llm.model, asdict(capability_profile))

    async def ainvoke(self, request):
        """Primary 시도 → 실패 시 fallback"""

        # Primary 시도
        if self.primary_agent:
            try:
                logger.info(f"[Resilient] Attempting primary agent (structured output)")
                result = await self.primary_agent.ainvoke(request)
                self.logger.log_execution("primary_success")
                return result
            except (OutputParserException, ValidationError, json.JSONDecodeError) as e:
                logger.warning(f"[Resilient] Primary agent failed: {e}. Retrying with fallback.")
                self.logger.log_execution("primary_failed", error=str(e))

        # Fallback 시도
        try:
            logger.info(f"[Resilient] Attempting fallback agent (text react)")
            result = await self.fallback_agent.ainvoke(request)
            self.logger.log_execution("fallback_success")
            return result
        except Exception as e:
            logger.error(f"[Resilient] Both agents failed: {e}")
            self.logger.log_execution("fallback_failed", error=str(e))
            raise

def create_resilient_agent(llm, tools, prompt):
    """Factory: capability에 맞는 ResilientAgentExecutor 생성"""
    model_name = getattr(llm, "model", "") or getattr(llm, "model_name", "")
    capability = detect_capability(model_name)
    return ResilientAgentExecutor(llm, tools, prompt, capability)
```

#### Task 1.1: ModelCapabilityDetector 구현 (YAML 외부화, G 제안)
- 목적: 모델별 지원 기능 자동 감지
- 파일: `src/agent/model_capability.py` (신규) + `config/model_capabilities.yaml` (신규)

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

#### Task 1.2: TextReActAgent와 AGENT_CONFIG 통합 (CX 지적) ⭐ CRITICAL
- 목적: TextReActAgent가 기존 agent_steps, partial_result 등 계약 보장
- 파일: `src/agent/text_react_agent.py` (신규, AGENT_CONFIG 통합)

```python
class TextReActAgent:
    """
    CX 지적 반영: AGENT_CONFIG와 통합되어 기존 observability 보장
    """

    def __init__(self, llm, tools, prompt, agent_config=None):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.prompt = prompt

        # AGENT_CONFIG 적용 (CX 요구)
        self.agent_config = agent_config or AGENT_CONFIG
        self.max_iterations = self.agent_config.get("max_iterations", 10)
        self.iteration_timeout = self.agent_config.get("iteration_timeout_sec", 120)
        self.agent_steps = []  # 기존 observability 유지

        # Logger (ActionSanitizer와 함께 작동)
        self.logger = StructuredAgentLogger(llm.model, {})

    async def ainvoke(self, messages: list) -> dict:
        """
        기존 agent loop 계약과 동일:
        - agent_steps 수집
        - partial_result 반환
        - observability 유지
        """
        conversation = messages.copy()
        start_time = time.time()

        for iteration in range(self.max_iterations):
            # Timeout 체크
            if time.time() - start_time > self.iteration_timeout:
                logger.warning("TextReActAgent: Iteration timeout reached")
                break

            # LLM 호출
            response = await self.llm.ainvoke(conversation)
            content = response.content

            # agent_steps에 기록 (기존 observability)
            step = {
                "iteration": iteration,
                "thought": self._extract_thought(content),
                "action": self._extract_action(content),
                "observation": None,
            }

            # Final Answer 체크
            if "Final Answer:" in content:
                self.agent_steps.append(step)
                return {
                    "messages": conversation + [response],
                    "agent_steps": self.agent_steps,  # 기존 키
                    "partial_result": None,
                }

            # Action/Action Input 파싱 및 도구 실행
            action, action_input = self._parse_action(content)
            tool = self.tools.get(action)

            if tool:
                try:
                    result = tool.invoke(action_input)
                    observation = f"Observation: {json.dumps(result)}"
                    step["observation"] = result
                except Exception as e:
                    observation = f"Observation: Tool '{action}' failed: {e}"
                    step["observation"] = {"error": str(e)}
                    logger.warning(f"TextReActAgent tool error: {e}")
            else:
                observation = f"Observation: Tool '{action}' not found"
                step["observation"] = {"error": f"Tool {action} not found"}

            # observability 기록
            self.agent_steps.append(step)
            self.logger.log_tool_call(content, None, action, action_input)

            # 다음 루프 준비
            conversation.append(response)
            conversation.append(HumanMessage(content=observation))

        # 최대 반복 도달
        logger.warning(f"TextReActAgent: Max iterations reached ({self.max_iterations})")
        return {
            "messages": conversation,
            "agent_steps": self.agent_steps,
            "partial_result": {"error": "Max iterations reached"},
        }
```

#### Task 1.3: LiteLLM 설정 충돌 해결 (CX 지적) ⭐ CRITICAL
- 목적: DeepSeekProvider와 LiteLLM 간 명확한 precedence
- 파일: `src/agent/config.py` (수정)

```python
# CX 지적: 사내에서 DeepSeek이 LiteLLM 프록시로 제공되므로 명시적 제어 필요

LLM_PROVIDER_CONFIG = {
    # 명시적 우선순위
    "force_provider": getenv("FORCE_LLM_PROVIDER", None),  # "gemini" | "deepseek" | "litellm"
    "model_name": getenv("LLM_MODEL", "gemini-2.0-flash"),
}

def create_llm():
    """Provider 선택: 명시적 > 모델명 > 기본값"""

    force = LLM_PROVIDER_CONFIG["force_provider"]
    if force:
        logger.info(f"Using forced provider: {force}")
        return _create_provider_by_name(force)

    model_name = LLM_PROVIDER_CONFIG["model_name"].lower()

    # 모델 기반 자동 선택
    if "deepseek" in model_name:
        # 사내 환경에서 LiteLLM 확인
        if getenv("USE_LITE_LLM", "False").lower() == "true":
            logger.info("DeepSeek via LiteLLM detected")
            return LiteLLMProvider().create()
        else:
            logger.info("DeepSeek direct detected")
            return DeepSeekProvider().create()

    elif "gemini" in model_name:
        return GoogleGenerativeAIProvider().create()

    else:
        # 기본값
        return GoogleGenerativeAIProvider().create()
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

#### Task 4.2: E2E 테스트 시나리오 (CX 지적) ⭐ P0
- 목적: FastMCP + DB 상호작용 검증
- 파일: `tests/agent/test_e2e_scenarios.py` (신규)

```python
@pytest.mark.asyncio
async def test_e2e_deepseek_xml_to_save_question():
    """
    CX 지적: XML 형식 DeepSeek 응답이 전체 파이프라인을 통과하는 e2e 검증

    흐름: DeepSeek XML → Sanitizer → TextReActAgent → SaveQuestion tool
    """
    # Mock: DeepSeek의 실제 XML 응답 (사내 로그에서 추출)
    mock_deepseek_response = AIMessage(
        content='''Thought: Need to save a question about RAG
<tool_call>
<name>save_generated_question</name>
<arguments>{
  "item_type": "multiple_choice",
  "stem": "What is RAG?",
  "choices": ["A: Retrieval", "B: Augmented", "C: Generation", "D: All"],
  "correct_key": "D",
  "difficulty": 5,
  "categories": ["LLM"],
  "round_id": "test_1"
}</arguments>
</tool_call>'''
    )

    # Setup: mock LLM + DB
    mock_llm = AsyncMock()
    mock_llm.model = "deepseek-chat"
    mock_llm.ainvoke = AsyncMock(return_value=mock_deepseek_response)

    with patch("src.agent.tools.save_question_tool.save_generated_question") as mock_save:
        mock_save.return_value = {"question_id": "q123", "success": True}

        # ResilientExecutor 실행
        agent = create_resilient_agent(mock_llm, MOCK_TOOLS, MOCK_PROMPT)
        result = await agent.ainvoke({"user_id": "test123"})

        # 검증
        assert result is not None
        assert mock_save.called
        call_args = mock_save.call_args
        assert call_args[1]["item_type"] == "multiple_choice"
        assert call_args[1]["stem"] == "What is RAG?"

@pytest.mark.asyncio
async def test_e2e_gemini_structured_output():
    """
    Gemini의 structured output이 정상 동작하는 e2e 검증
    """
    mock_gemini_response = GenerateQuestionsResponse(
        items=[
            GeneratedItem(
                id="q1",
                type="multiple_choice",
                stem="What is AI?",
                choices=["A", "B", "C", "D"],
                difficulty=5,
                category="AI"
            )
        ]
    )

    mock_llm = AsyncMock()
    mock_llm.model = "gemini-2.0-flash"
    structured_llm = AsyncMock()
    structured_llm.ainvoke = AsyncMock(return_value=mock_gemini_response)
    mock_llm.with_structured_output = MagicMock(return_value=structured_llm)

    agent = create_resilient_agent(mock_llm, MOCK_TOOLS, MOCK_PROMPT)
    result = await agent.ainvoke({"user_id": "test123"})

    # 검증
    assert result.items[0].stem == "What is AI?"
    assert mock_llm.with_structured_output.called  # Structured output 사용
```

**추가**: `./tools/dev.sh test`에 e2e 테스트 실행 포함
```bash
# tools/dev.sh
test)
  pytest tests/agent/test_e2e_scenarios.py -v --tb=short
  ;;
```

#### Task 4.3: Key Performance Metrics (G 제안) ⭐ P1
- 목적: 성과 측정 및 모델 간 비교
- 파일: `src/agent/metrics.py` (신규)

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class AgentMetrics:
    """G의 제안: 추적할 핵심 메트릭"""
    agent_execution_status: Literal["success", "failure", "fallback_success"]
    agent_latency_seconds: float
    llm_token_count_total: int
    tool_call_count: int
    tool_call_errors: int
    output_parser_failures: int
    fallback_invocations: int
    model_name: str
    agent_type: str  # "structured", "text_react", "resilient"

class MetricsCollector:
    """메트릭 수집 및 로깅"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.metrics: list[AgentMetrics] = []

    def record_execution(
        self,
        status: Literal["success", "failure", "fallback_success"],
        latency_sec: float,
        token_count: int,
        tool_calls: int,
        tool_errors: int,
        parser_failures: int,
        fallback_count: int,
        agent_type: str
    ):
        """실행 메트릭 기록"""
        metric = AgentMetrics(
            agent_execution_status=status,
            agent_latency_seconds=latency_sec,
            llm_token_count_total=token_count,
            tool_call_count=tool_calls,
            tool_call_errors=tool_errors,
            output_parser_failures=parser_failures,
            fallback_invocations=fallback_count,
            model_name=self.model_name,
            agent_type=agent_type,
        )
        self.metrics.append(metric)
        self._emit_to_monitoring(metric)  # Prometheus, CloudWatch 등

    def _emit_to_monitoring(self, metric: AgentMetrics):
        """외부 모니터링 시스템으로 전송 (Grafana, Datadog)"""
        logger.info(f"METRICS: {json.dumps(asdict(metric), ensure_ascii=False)}")
```

**Grafana 쿼리 예제:**
```sql
-- 모델별 평균 latency
SELECT
  model_name,
  AVG(agent_latency_seconds) as avg_latency,
  COUNT(*) as total_calls
FROM agent_metrics
GROUP BY model_name
ORDER BY avg_latency DESC;

-- Fallback 호출 비율
SELECT
  model_name,
  SUM(CASE WHEN agent_execution_status = 'fallback_success' THEN 1 ELSE 0 END) / COUNT(*) as fallback_rate
FROM agent_metrics
GROUP BY model_name;
```

#### Task 4.4: 구조화된 로깅 (CX 문서) ⭐ NEW
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

## 4. 구현 우선순위 및 일정 (최종 검토 반영)

### 4.1 우선순위 매트릭스 (최종 - v1.2)

| Phase | Task | 영향도 | 위험도 | 우선순위 | 핵심 지적 |
|-------|------|--------|--------|----------|----------|
| **0.0** | **Phase 0 위험 관리** | **Critical** | Medium | **P0** | CX #1 |
| **1.0** | **ResilientAgentExecutor** | **Critical** | Low | **P0** | G 제안 |
| **1.1** | ModelCapability YAML 외부화 | High | Low | P0 | G 제안 |
| **0.1** | with_structured_output 도입 | **Critical** | Medium | **P0** | G 문서 |
| **0.2** | Two-Step (Gather 에러 처리) | **Critical** | Medium | **P0** | CX #2 |
| 0.3 | Pydantic 응답 모델 강화 | High | Low | P1 | G 문서 |
| **1.2** | TextReActAgent + AGENT_CONFIG | **High** | Low | **P0** | CX #3 |
| **1.3** | LiteLLM 설정 충돌 해결 | **High** | Low | **P0** | CX #5 |
| **2.0** | StructuredTool args_schema | **High** | Low | **P0** | CX 문서 |
| **2.1** | ActionSanitizer | **High** | Medium | **P0** | CX 문서 |
| 2.2 | parse_json_robust 전역 활용 | High | Low | P1 | CX #2 |
| 2.3 | MultiFormatOutputParser | High | Medium | P1 | A |
| **4.0** | 테스트 인프라 구축 | **High** | Low | **P0** | CX #4 |
| **4.2** | **E2E 테스트 시나리오** | **High** | Low | **P0** | CX #4 |
| **4.3** | **Key Performance Metrics** | **High** | Low | **P1** | G 제안 |
| 4.4 | 구조화된 로깅 | **High** | Low | **P1** | CX 문서 |

### 4.2 전략적 접근 방식 (개발 → 프로덕션 검증)

```
┌─────────────────────────────────────────────────────────────┐
│  DeepSeek 호환성 검증 전략 (단계적 배포)                     │
│  ─────────────────────────────────                          │
│                                                              │
│  개발 환경 (사외 - Gemini):                                  │
│  └─ Phase 0: with_structured_output 안정화                 │
│  └─ Phase 1: ResilientAgentExecutor + fallback 검증        │
│  └─ Phase 2: ActionSanitizer 테스트 (DeepSeek 시뮬레이션)   │
│  └─ Phase 4: 완벽한 테스트 커버리지 + 메트릭               │
│                                                              │
│  프로덕션 환경 (사내 - DeepSeek):                            │
│  └─ Week 4: 검증된 코드로 사내 환경 배포                    │
│  └─ TextReActAgent + ActionSanitizer로 DeepSeek 실행      │
│  └─ 구조화된 로깅으로 실시간 모니터링                        │
│                                                              │
│  ❌ 모델 선택이 아님:                                        │
│     - Gemini는 "개발 편의성"을 위한 도구일 뿐               │
│     - DeepSeek만이 프로덕션 환경 (사내 폐쇄망)              │
└─────────────────────────────────────────────────────────────┘
```

**핵심 원칙: 개발 환경에서 완벽하게 검증 후 프로덕션 배포**
- Phase 0 (G 문서): Gemini에서 `with_structured_output` 먼저 안정화
- Phase 1-2 (CX 문서): TextReActAgent + ActionSanitizer로 DeepSeek 호환성 확보
- Phase 4: 완전한 e2e 테스트 (DeepSeek XML → Sanitizer → Tool 실행)
- Week 4+: 검증된 코드를 사내 DeepSeek 환경에 배포

### 4.3 구현 순서 (개발환경 Gemini 검증 → 프로덕션 DeepSeek 배포)

```
┌─────────────────────────────────────────────────────────────┐
│ 개발 환경 (사외 - Gemini)에서 완벽한 검증 후                  │
│ 프로덕션 환경 (사내 - DeepSeek)으로 배포                      │
│                                                              │
│ 우선순위: CX 지적 + G 제안 통합                              │
│ - P0: 안전성/테스트/메트릭 (현실적 배포)                      │
│ - P1: 성능 최적화 (추가 개선)                                │
└─────────────────────────────────────────────────────────────┘

📍 개발 환경 (사외 - Gemini): Week 1-4

Week 1: 기반 인프라 + 위험 관리 (Foundation)
├── Day 1-2: 테스트 인프라 구축 (tests/agent/)
│   └─ fixtures, conftest, e2e 시나리오 (DeepSeek XML 시뮬레이션)
├── Day 3: Phase 0 위험 관리 (CX #1)
│   └─ ENABLE_STRUCTURED_OUTPUT flag, should_use_structured_output()
├── Day 4: ResilientAgentExecutor (G 제안)
│   └─ primary/fallback 자동 전환, self-healing
└── Day 5: ModelCapability YAML 외부화 (G 제안)
   └─ config/model_capabilities.yaml

Week 2: 핵심 구현 - Phase 0 + Phase 1 (Gemini 검증)
├── Day 1: LiteLLM 설정 충돌 해결 (CX #5)
│   └─ FORCE_LLM_PROVIDER env var
├── Day 2-3: with_structured_output (Phase 0.1)
│   └─ Gemini에서 완전히 안정화
├── Day 4: Two-Step Gather-Generate (Phase 0.2, CX #2)
│   └─ Gather도 ErrorHandler 적용 (실제 동작 검증)
└── Day 5: E2E 테스트 (CX #4)
   └─ DeepSeek XML 시뮬레이션 → Sanitizer → SaveQuestion

Week 3: 호환성 레이어 + 안전성 (DeepSeek 시뮬레이션)
├── Day 1: TextReActAgent + AGENT_CONFIG (CX #3)
│   └─ agent_steps, partial_result 보장
├── Day 2: StructuredTool args_schema (Phase 2.0)
│   └─ 입력 검증 + type coercion
├── Day 3: ActionSanitizer (Phase 2.1)
│   └─ XML/YAML → JSON 전처리 (완벽하게 검증)
└── Day 4-5: Key Performance Metrics (G 제안)
   └─ agent_execution_status, latency, token_count, fallback_rate

Week 4: 완벽한 검증 + 배포 준비 (Final Validation)
├── Day 1-2: Multi-Model 호환성 테스트
│   └─ DeepSeek XML 형식 → Sanitizer → 검증
├── Day 3: 구조화된 로깅 (Phase 4.4)
│   └─ JSON 형식 로그 자동 내보내기 (사내 검증용 준비)
└── Day 4-5: 배포 준비 + 문서화
   └─ 모든 테스트 통과 확인
   └─ 배포 가이드 작성

📍 프로덕션 환경 (사내 - DeepSeek): Week 4+

Week 4+: 검증된 코드 → DeepSeek 배포
├─ TextReActAgent + ActionSanitizer 활성화 (이미 완벽히 검증됨)
├─ LiteLLM DeepSeek으로 실행
├─ 구조화된 로깅으로 실시간 모니터링
└─ Phase 0b/0c: 필요시 추가 최적화

결과: 개발 단계에서 모든 edge case 검증 완료 → 프로덕션 안정성 보장
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

## 7. 최종 결론 (v1.2 - 완전 통합)

### 7.1 핵심 개선점 요약 (최종 - 3개 검토 의견 통합)

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

### 7.2 기대 효과 (DeepSeek 프로덕션 호환성)

```
Before (현재 - 사외 Gemini만 정상):
┌──────────────────────────────────────────────┐
│ 개발 환경 (사외):                             │
│   Gemini:  ✅ 정상 (native tool calling)     │
│                                               │
│ 프로덕션 환경 (사내):                         │
│   DeepSeek: ❌ 실패 (XML 출력, 파싱 에러)    │
│   디버깅:   😰 수동 로그 복사 필요            │
│   재검증:   😰 매번 사내에서 직접 테스트      │
└──────────────────────────────────────────────┘

After (개선 후 - 개발에서 완벽히 검증 후 프로덕션 배포):
┌──────────────────────────────────────────────┐
│ 개발 환경 (사외 - 완벽한 검증):               │
│   Gemini:        ✅ with_structured_output   │
│   DeepSeek XML:  ✅ Mock 시뮬레이션 + 검증   │
│   Sanitizer:     ✅ XML → JSON 완벽 검증     │
│   TextReActAgent:✅ 도구 호출 완벽 검증      │
│   E2E 테스트:    ✅ 전체 파이프라인 검증     │
│                                               │
│ 프로덕션 환경 (사내 - 검증된 코드 배포):      │
│   DeepSeek:  ✅ 정상 (이미 검증됨)           │
│   디버깅:    😊 JSON 로그 자동 내보내기      │
│   안정성:    😊 개발 단계에서 모든 케이스 커버│
└──────────────────────────────────────────────┘
```

**핵심 차이:**
- ❌ Before: 개발(Gemini만) → 사내에서 DeepSeek 실패 → 재개발
- ✅ After: 개발(Gemini + DeepSeek 시뮬레이션 완벽 검증) → 사내 배포(안정)

### 7.3 다음 단계 (구현 로드맵)

1. **Week 1-4: 개발 환경에서 완벽한 검증** (사외 - Gemini)
   - Phase 0: `with_structured_output` 안정화 (Gemini)
   - Phase 1-2: TextReActAgent + ActionSanitizer (DeepSeek 시뮬레이션)
   - Phase 4: E2E 테스트 + 메트릭 검증
   - **목표**: DeepSeek XML 형식 → 완벽하게 처리하는 코드 검증

2. **Week 4+: 프로덕션 배포** (사내 - DeepSeek)
   - 검증된 코드를 사내 LiteLLM DeepSeek에 배포
   - 구조화된 로깅으로 실시간 모니터링
   - 필요시 Phase 0b/0c 추가 최적화

3. **배포 전 필수 조건**
   - ✅ `tests/agent/` 완전한 테스트 커버리지
   - ✅ DeepSeek XML → Sanitizer → 도구 호출 e2e 검증
   - ✅ 구조화된 JSON 로그 자동 내보내기 가능
   - ✅ 모든 테스트 통과

### 7.4 동료 피드백 통합 현황 + DeepSeek-Only 전략 확정 (v1.2 최종)

**CX 검토 - 5가지 핵심 지적 (모두 반영 ✅):**
- [x] #1: Phase 0 위험 관리 → Task 0.0 (Gemini 개발환경에서 feature flag로 제어)
- [x] #2: Gather 단계의 에러 처리 → Task 0.2 (ErrorHandler 적용)
- [x] #3: TextReActAgent와 AGENT_CONFIG → Task 1.2 (DeepSeek 프로덕션용 agent_steps 보장)
- [x] #4: E2E 테스트 부재 → Task 4.2 (DeepSeek XML 시뮬레이션 → 완벽 검증)
- [x] #5: DeepSeekProvider vs LiteLLM 충돌 → Task 1.3 (FORCE_LLM_PROVIDER env var)

**G 검토 - 3가지 강화 제안 (모두 추가 ✅):**
- [x] 제안 1: ModelCapability YAML 외부화 → Task 1.1 (DeepSeek 프로덕션 설정)
- [x] 제안 2: ResilientAgentExecutor → Task 1.0 (Gemini 개발 → DeepSeek 프로덕션 전환)
- [x] 제안 3: Key Performance Metrics → Task 4.3 (개발/프로덕션 양쪽 모니터링)

**최종 검토 조언 (v1.2.1 - DeepSeek 전략 명확화):**
- [x] 목표 재정의: "Multi-Model 지원" → "DeepSeek 프로덕션 호환성 검증"
- [x] 개발/프로덕션 분리: Gemini (개발 도구) vs DeepSeek (프로덕션 only)
- [x] 개발 단계에서 완벽한 검증: DeepSeek XML 형식 → 모든 케이스 시뮬레이션
- [x] 배포 경로 단순화: 검증된 코드 → 사내 LiteLLM DeepSeek 배포

### 7.5 개발 환경 vs 프로덕션 환경 명확화 ⭐ IMPORTANT

> **핵심 원칙**: 이 문서의 모든 설계는 **DeepSeek 프로덕션 호환성**을 목표로 함
>
> **❌ 오해하면 안 되는 부분:**
> - "Multi-Model 지원" ❌ → "DeepSeek-only 프로덕션" ✅
> - "Gemini와 DeepSeek 중 선택" ❌ → "Gemini로 검증 후 DeepSeek 배포" ✅
> - "모든 모델을 동일하게 지원" ❌ → "DeepSeek 완벽 호환성" ✅

#### 개발 환경 (사외 - Gemini)

```
목적: DeepSeek 프로덕션용 코드 개발 및 검증
─────────────────────────────────────────

Phase 0 (Week 1-2):
├─ Gemini로 with_structured_output 안정화
├─ ENABLE_STRUCTURED_OUTPUT=true (Gemini only)
├─ 모든 기능이 완벽히 작동하는지 검증
└─ 로그 및 메트릭 수집

Phase 1-2 (Week 2-3):
├─ TextReActAgent 구현 (DeepSeek XML 처리용)
├─ ActionSanitizer 구현 (XML → JSON 변환)
├─ ResilientExecutor 구현 (fallback 메커니즘)
└─ mock_deepseek_xml_response로 시뮬레이션 검증

Phase 4 (Week 3-4):
├─ DeepSeek XML 형식을 완벽히 처리하는지 e2e 검증
├─ 구조화된 로깅이 제대로 작동하는지 검증
├─ 모든 메트릭 수집 및 분석
└─ 사내 배포 체크리스트 작성
```

**Gemini는 개발 편의성을 위한 도구일 뿐:**
- ✅ 빠른 반복 개발 가능
- ✅ 강력한 Native Tool Calling으로 안정적 테스트
- ✅ 구조화된 출력으로 검증 용이
- ❌ 프로덕션 환경과 다름 (절대 Gemini로 배포하지 않음)

#### 프로덕션 환경 (사내 - DeepSeek only)

```
목적: LiteLLM을 통한 DeepSeek 실행 및 모니터링
──────────────────────────────────────────────

배포 전 조건:
├─ 개발 환경에서 모든 테스트 통과
├─ DeepSeek XML 형식 완벽히 처리 검증됨
├─ 구조화된 로깅으로 디버깅 가능 확인
└─ 메트릭 수집 가능 확인

배포 (Week 4+):
├─ git pull로 검증된 코드 배포
├─ TextReActAgent + ActionSanitizer 자동 활성화
├─ LiteLLM을 통해 DeepSeek 실행
└─ JSON 로그로 실시간 모니터링

배포 후:
├─ 구조화된 로그를 통한 이슈 추적
├─ 메트릭 대시보드(Grafana)로 성능 모니터링
├─ 필요시 개발 환경에서 재현 및 수정
└─ 다시 배포

결과:
✅ "사내에서 갑자기 실패" 상황 방지 (개발에서 완벽 검증됨)
✅ "로그 복사해달라" 요청 불필요 (구조화된 로깅 자동화)
✅ "왜 실패했나" 알기 어려움 해결 (메트릭 + 로깅)
```

#### 모델별 역할 정리

| 모델 | 환경 | 역할 | 배포 |
|------|------|------|------|
| **Gemini** | 사외 (개발) | 코드 개발 + 검증 | ❌ 사내 배포 금지 |
| **DeepSeek** | 사내 (프로덕션) | 실제 운영 | ✅ 필수 배포 |

**단, Phase 4 테스트에서:**
- Mock DeepSeek XML을 Gemini 개발 환경에서 완벽히 처리하는지 검증
- 실제 사내 DeepSeek은 이미 검증된 코드만 받음

---

## 8. 개발 비용 감소를 위한 설계 원칙

이 계획이 지향하는 핵심 원칙:

```
초반 리뷰 품질 ↑  →  개발 중 리팩토링 ↓  →  전체 개발 비용 ↓

3명의 동료 검토를 통합한 이유:
1. CX: 사실적 운영 관점 (LiteLLM, DB, 재시도 정책 등)
2. G: 아키텍처 관점 (YAML 외부화, 자동 fallback, 메트릭)
3. 최종 검토: 단계적 롤아웃 (실패 위험 최소화)

결과:
- ❌ 1차 구현 후 사내에서 완전 실패 → 대폭 리팩토링
- ✅ 설계 단계에서 모든 함정 식별 → 예측 가능한 구현

추정 절감:
- 리스크: 95% → 10% (초반 리뷰로 위험 지점 명시)
- 리팩토링: 2-3주 → 0주 (롤아웃 단계에서 점진적 검증)
- 팀 신뢰: 구조화된 계획으로 모든 팀원이 방향 이해
```

---

*문서 작성: 2025-12-05*
*최종 업데이트: 2025-12-05 (v1.2.1 - DeepSeek-only 전략 명확화)*
*버전 히스토리:*
  - v1.0: 초기 계획 (A 문서)
  - v1.1: G, CX 1차 피드백 반영
  - v1.2: CX 검토 + G 검토 + 최종 검토의견 완전 통합
  - v1.2.1: DeepSeek 프로덕션 호환성에 집중
    * "Multi-Model 지원" → "DeepSeek-only 프로덕션" 용어 정확화
    * 개발(Gemini) vs 프로덕션(DeepSeek) 환경 명확히 분리
    * 배포 경로: 사외 개발 완벽 검증 → 사내 DeepSeek 배포
    * Section 7.5 추가: 개발 환경 vs 프로덕션 환경 상세 설명
    * Section 4.2, 4.3 리라이팅: "Option A/B 선택" 제거, "단계적 검증" 강조
