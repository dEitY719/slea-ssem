# REQ-A-ItemGen: Item-Gen-Agent 통합 구현

**Requirement**: Item-Gen-Agent (LangChain 기반 자율 AI 에이전트)

**Status**: Phase 1 - Specification (진행 중)

**Last Updated**: 2025-11-08

**Framework**: LangChain 최신 버전 (0.3.x+) + FastMCP + Google Gemini

---

## 📋 PHASE 1: SPECIFICATION

### 1.1 Requirement Summary

| Aspect | Details |
|--------|---------|
| **REQ ID** | REQ-A-ItemGen |
| **Title** | Item-Gen-Agent 통합 (LangChain ReAct 패턴) |
| **Priority** | **M** (Must) |
| **MVP** | 1.0 |
| **Framework** | LangChain Agent + FastMCP + Google Gemini |
| **Intent** | LangChain의 최신 Agent 패턴(ReAct)을 사용하여 자율적으로 도구를 선택·활용하는 AI 에이전트 구현 |

### 1.2 Scope

**In Scope**:
- LangChain `create_react_agent()` 사용 (최신 API)
- FastMCP `@tool` 데코레이터로 6개 도구 등록
- ReAct 패턴: Thought → Action → Observation → Reflection
- Google Gemini LLM 통합 (`ChatGoogle`)
- 두 가지 Mode:
  - **Mode 1**: 문항 생성 (Tool 1-5)
  - **Mode 2**: 자동 채점 (Tool 6)
- 에러 처리 및 재시도 로직
- 상세한 로깅 (Thought/Action/Observation 추적)

**Out of Scope**:
- 개별 Tool 구현 (Tool 1-6은 별도 REQ)
- 데이터베이스 레이어 (FastAPI 백엔드)
- 프롬프트 튜닝 최적화 (MVP 2.0)

### 1.3 Architecture

#### **High-Level Flow**

```
┌─────────────────────────────────────────────┐
│        Frontend / API Request                │
│  (Mode: generate_questions | score_answer)  │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│   LangChain Item-Gen-Agent                  │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  1. Agent Initialization            │   │
│  │     - LLM: ChatGoogle (Gemini)      │   │
│  │     - Tools: FastMCP @tool (6개)   │   │
│  │     - Prompt: ReAct 프롬프트        │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  2. Agent Execution Loop            │   │
│  │     Thought → Action → Observation  │   │
│  │     (최대 10 반복, 또는 종료)        │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  3. Tool Selection & Execution      │   │
│  │     Tool 1-6 동적 호출              │   │
│  │     (Mode 1: Tool 1-5)              │   │
│  │     (Mode 2: Tool 6)                │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  4. Result Parsing & Return         │   │
│  │     구조화된 JSON 반환               │   │
│  └─────────────────────────────────────┘   │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│        Result: Generated Questions / Scores  │
│        + Metadata (validation_score, etc.)   │
└─────────────────────────────────────────────┘
```

#### **Directory Structure**

```
src/agent/
├── __init__.py
├── llm_agent.py              # REQ-A-ItemGen: 메인 에이전트 클래스
├── fastmcp_server.py         # REQ-A-FastMCP: FastMCP 도구 서버
├── prompts/
│   ├── __init__.py
│   ├── react_prompt.py       # ReAct 프롬프트 템플릿
│   └── tool_instructions.py  # 각 Tool의 상세 지시사항
├── tools/
│   ├── __init__.py
│   ├── tool_1_profile.py     # REQ-A-Mode1-Tool1 (별도)
│   ├── tool_2_templates.py   # REQ-A-Mode1-Tool2 (별도)
│   ├── tool_3_keywords.py    # REQ-A-Mode1-Tool3 (별도)
│   ├── tool_4_validate.py    # REQ-A-Mode1-Tool4 (별도)
│   ├── tool_5_save.py        # REQ-A-Mode1-Tool5 (별도)
│   └── tool_6_score.py       # REQ-A-Mode2-Tool6 (별도)
├── config.py                 # 설정 (LLM 파라미터, 모델명 등)
└── schemas.py                # Pydantic 스키마 (입출력)
```

### 1.4 Core Components

#### **1.4.1 ItemGenAgent Class**

**위치**: `src/agent/llm_agent.py`

**핵심 메서드**:

```python
class ItemGenAgent:
    """LangChain ReAct 기반 Item-Gen-Agent"""

    def __init__(self, llm, tools, prompt_template):
        """에이전트 초기화"""
        self.llm = llm
        self.agent = create_react_agent(
            llm=llm,
            tools=tools,
            prompt=prompt_template
        )
        self.executor = AgentExecutor(agent=self.agent, tools=tools)

    async def generate_questions(self, user_id: str, difficulty: int,
                                 interests: list[str]) -> list[dict]:
        """
        Mode 1: 문항 생성
        - Tool 1-5 자동 선택 & 실행
        - 반환: [문항 리스트]
        """
        pass

    async def score_and_explain(self, session_id: str,
                               question_id: str,
                               user_answer: str) -> dict:
        """
        Mode 2: 자동 채점
        - Tool 6 실행
        - 반환: {점수, 해설, 피드백}
        """
        pass

    def _parse_agent_output(self, result: dict) -> list[dict] | dict:
        """에이전트 출력 파싱"""
        pass
```

#### **1.4.2 LangChain Agent 설정**

**LLM 초기화** (`src/agent/config.py`):

```python
from langchain_google_genai import ChatGoogle
from os import getenv

def create_llm():
    """Google Gemini LLM 생성"""
    return ChatGoogle(
        api_key=getenv("GEMINI_API_KEY"),
        model="gemini-1.5-pro",
        temperature=0.7,      # 창의성과 정확성 균형
        max_tokens=2048,      # 응답 최대 길이
        top_p=0.95           # 확률 샘플링
    )
```

**Agent 생성** (`src/agent/llm_agent.py`):

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from src.agent.prompts.react_prompt import REACT_PROMPT

def create_agent(llm, tools):
    """ReAct 에이전트 생성"""
    # 프롬프트 템플릿
    prompt = PromptTemplate.from_template(REACT_PROMPT)

    # 에이전트 생성
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    # 에이전트 실행기
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=10,          # 최대 10번 반복
        early_stopping_method="force",  # 최대 반복 도달 시 강제 중지
        verbose=True,               # 상세 로깅
        handle_parsing_errors=True  # 파싱 에러 처리
    )

    return executor
```

#### **1.4.3 ReAct Prompt Template**

**위치**: `src/agent/prompts/react_prompt.py`

```python
REACT_PROMPT = """
Thought: You are a question generation expert. Analyze the user request and decide which tool to use.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""
```

#### **1.4.4 FastMCP Tool 등록**

**위치**: `src/agent/fastmcp_server.py`

```python
from langchain_core.tools import tool

@tool
def get_user_profile(user_id: str) -> dict:
    """
    사용자의 자기평가 정보 조회

    Args:
        user_id: 사용자 ID

    Returns:
        {
            "user_id": "...",
            "self_level": "beginner|intermediate|advanced",
            "years_experience": 3,
            "job_role": "...",
            "interests": ["LLM", "RAG", ...]
        }
    """
    # Tool 1 구현 (별도 REQ-A-Mode1-Tool1)
    pass

@tool
def search_question_templates(interests: list[str],
                            difficulty: int,
                            category: str) -> list[dict]:
    """
    문항 템플릿 검색
    """
    # Tool 2 구현 (별도 REQ-A-Mode1-Tool2)
    pass

# ... Tool 3-6 동일하게 등록

# 도구 목록
TOOLS = [
    get_user_profile,
    search_question_templates,
    get_difficulty_keywords,
    validate_question_quality,
    save_generated_question,
    score_and_explain
]
```

### 1.5 Execution Flow (Mode 1: 문항 생성)

```
Step 1: generate_questions(user_id="123", difficulty=5, interests=["LLM", "RAG"])
   ↓
Step 2: Agent 초기화 (ReAct 프롬프트 + 6개 도구 바인딩)
   ↓
Step 3: Agent Executor 시작

   Iteration 1:
   - Thought: "사용자 123의 정보가 필요하다"
   - Action: Tool 1 (get_user_profile) 호출
   - Observation: {self_level: "intermediate", interests: [...]}

   Iteration 2:
   - Thought: "관심분야 템플릿 검색이 필요하다"
   - Action: Tool 2 (search_question_templates) 호출
   - Observation: [{stem: "...", ...}, ...]

   Iteration 3:
   - Thought: "난이도 5에 맞는 키워드 필요"
   - Action: Tool 3 (get_difficulty_keywords) 호출
   - Observation: {keywords: [...], concepts: [...]}

   Iteration 4:
   - Thought: "LLM으로 문항 생성 및 검증"
   - Action: Tool 4 (validate_question_quality) 호출 (여러 번)
   - Observation: {is_valid: True, score: 0.92, ...}

   Iteration 5:
   - Thought: "검증된 문항 저장"
   - Action: Tool 5 (save_generated_question) 호출 (여러 번)
   - Observation: {question_id: "...", saved_at: "..."}

   Final Answer: [생성된 5개 문항 리스트]
   ↓
Step 4: _parse_agent_output() 로 결과 파싱
   ↓
Step 5: API 응답으로 반환
```

### 1.6 Error Handling Strategy

| 에러 유형 | 처리 방식 | 재시도 |
|----------|---------|--------|
| Tool 호출 실패 | 로그 + 다른 도구 시도 | 최대 3회 |
| LLM 응답 파싱 오류 | handle_parsing_errors=True | 자동 |
| 최대 반복 도달 | early_stopping_method="force" | N/A |
| 네트워크 에러 | 재시도 + timeout 설정 | 3회 |
| Tool 반환값 형식 오류 | 타입 검증 + 기본값 | 1회 |

### 1.7 LangChain 공식 문서 참고 사항

**최신 API 버전**: LangChain 0.3.x+

**주요 특징**:
1. ✅ `create_react_agent()` - 최신 ReAct 에이전트 생성 (권장)
2. ✅ `AgentExecutor` - 에이전트 실행 및 도구 호출
3. ✅ `@tool` 데코레이터 - FastMCP 도구 정의 (최신)
4. ✅ `ChatGoogle` - Google Gemini 통합 (공식 지원)
5. ✅ 구조화된 출력 (JSON) - 파싱 안정성 향상

**이전 API 버전 (deprecated)**:
- ❌ `initialize_agent()` (구식, 제거 예정)
- ❌ `Tool` 클래스 (대신 `@tool` 사용)
- ❌ 직접 에이전트 클래스 상속

---

## 📝 PHASE 2: TEST DESIGN (TBD)

**테스트 전략**:
- 단위 테스트: 각 Tool 동작 확인
- 통합 테스트: Mode 1 & Mode 2 E2E
- Mock LLM으로 응답 테스트
- 에러 처리 테스트

---

## 💻 PHASE 3: IMPLEMENTATION (TBD)

**구현 순서**:
1. 에이전트 기본 구조 + Config
2. ReAct 프롬프트 정의
3. FastMCP 도구 등록 (Stub)
4. Agent 생성 및 실행
5. 결과 파싱 & 에러 처리
6. 로깅 & 모니터링

---

## 📄 PHASE 4: DOCUMENTATION (TBD)

**문서화**:
- 코드 주석 (공식 문서 참고)
- 사용 예시
- 문제 해결 가이드

---

## 🔗 Reference & Best Practices

### **LangChain 공식 문서**:
- [Agents | LangChain](https://python.langchain.com/docs/concepts/agents)
- [create_react_agent | LangChain API](https://python.langchain.com/api_reference/langchain/agents/langchain.agents.agent.create_react_agent.html)
- [Tools | LangChain](https://python.langchain.com/docs/concepts/tools)

### **Best Practices**:
1. ✅ `create_react_agent()` 사용 (최신)
2. ✅ `@tool` 데코레이터 (권장)
3. ✅ 구조화된 스키마 (Pydantic)
4. ✅ 상세한 로깅 (디버깅)
5. ✅ 타입 힌트 (코드 품질)
6. ✅ 에러 처리 명시적으로 (안정성)
7. ✅ 도구 설명 상세 (LLM 이해도)

### **팀 동료 참고 체크리스트**:
- [ ] LangChain 버전 0.3.x+ 사용 확인
- [ ] `create_react_agent()` 사용 (initialize_agent X)
- [ ] `@tool` 데코레이터 사용
- [ ] Pydantic 스키마 정의
- [ ] 타입 힌트 명시
- [ ] 에러 처리 로직 포함
- [ ] 로깅으로 Thought/Action/Observation 추적
- [ ] 공식 문서와 예시 코드 참고

---

**Implementation Status**: Phase 1 Specification ✅ → Phase 2 (Testing) ⏳
**Quality Level**: 팀 동료 참고 코드 기준 (높은 수준의 문서화 + 예시)
