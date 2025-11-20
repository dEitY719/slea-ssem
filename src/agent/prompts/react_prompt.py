"""
ReAct Prompt Template for Item-Gen-Agent.

REQ: REQ-A-ItemGen

Reference: LangChain official ReAct Agent implementation.
https://python.langchain.com/docs/concepts/agents

NOTE: Updated for LangGraph v2 compatibility using ChatPromptTemplate.from_messages()

DESIGN: Uses Builder Pattern (prompt_builder.py) to separate content from template logic.
- Content: Stored in prompt_content.py (pure text, no escaping needed)
- Template: Built by PromptBuilder classes (clean logic, no special handling)
- Benefits: Prevents JSON escaping issues, easier maintenance, better testability
"""

from langchain_core.prompts import ChatPromptTemplate

from src.agent.prompts.prompt_builder import PromptFactory


def get_react_prompt() -> ChatPromptTemplate:
    """
    ReAct (Reasoning + Acting) 프롬프트 템플릿 반환 (LangGraph v2 호환).

    Uses Builder Pattern to separate prompt content from template logic.

    Returns:
        ChatPromptTemplate: LangGraph v2 호환 ReAct 프롬프트

    설명:
        - Thought: 에이전트의 추론 과정
        - Action: 실행할 도구 선택
        - Action Input: 도구에 전달할 입력
        - Observation: 도구 실행 결과
        - Final Answer: 최종 답변

    참고:
        LangGraph v2 message-based 프롬프트 형식.
        Tool descriptions은 LangGraph v2가 자동으로 처리합니다.
        https://python.langchain.com/docs/how_to/agent_structured_outputs

    Design:
        Uses PromptFactory to get ReactPromptBuilder which handles
        template construction. Prompt content is stored separately in
        prompt_content.py to prevent JSON escaping issues.

    """
    builder = PromptFactory.get_builder("react")
    return builder.build()


# 대체 프롬프트 (간단한 버전)
def get_simple_react_prompt() -> ChatPromptTemplate:
    """
    간단한 ReAct 프롬프트 (MVP용, LangGraph v2 호환).

    Uses SimpleReactPromptBuilder for lightweight prompt without detailed rules.

    Returns:
        ChatPromptTemplate: 간단한 ReAct 프롬프트.

    """
    builder = PromptFactory.get_builder("simple")
    return builder.build()
