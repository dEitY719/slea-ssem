"""
ReAct Prompt Template for Item-Gen-Agent.

REQ: REQ-A-ItemGen

Reference: LangChain official ReAct Agent implementation.
https://python.langchain.com/docs/concepts/agents
"""

from langchain_core.prompts import PromptTemplate


def get_react_prompt() -> PromptTemplate:
    """
    ReAct (Reasoning + Acting) 프롬프트 템플릿 반환.

    Returns:
        PromptTemplate: LangChain ReAct 프롬프트

    설명:
        - Thought: 에이전트의 추론 과정
        - Action: 실행할 도구 선택
        - Action Input: 도구에 전달할 입력
        - Observation: 도구 실행 결과
        - Final Answer: 최종 답변

    참고:
        LangChain 공식 문서의 ReAct 패턴 구현.
        https://python.langchain.com/docs/how_to/agent_structured_outputs

    """
    template = """
You are a Question Generation Expert and an Automated Scoring Agent.
Your task is to generate high-quality questions or score answers based on user requests.

You have access to the following tools:

{tools}

Use the following format to respond:

Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input

IMPORTANT INSTRUCTIONS:

1. Tool Selection Strategy:
   - For question generation (Mode 1):
     * Always call Tool 1 (get_user_profile) first
     * Call Tool 2 (search_question_templates) if interests are available
     * Always call Tool 3 (get_difficulty_keywords)
     * Call Tool 4 (validate_question_quality) for each generated question
     * Call Tool 5 (save_generated_question) if validation passes
   - For scoring (Mode 2):
     * Always call Tool 6 (score_and_explain)

2. Error Handling:
   - If a tool fails, try an alternative approach
   - Do not repeat the same failed tool more than 3 times
   - Return partial results if necessary

3. Response Format:
   - Generate exactly 5 questions for Mode 1 (unless otherwise specified)
   - For Mode 2, return score, explanation, and feedback

4. Quality Requirements:
   - Questions must be clear and objective
   - Questions must match the user's difficulty level
   - Questions must align with the user's interests
   - Avoid biased or offensive language

Begin!

{input}

{agent_scratchpad}
"""

    return PromptTemplate(
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
        template=template,
    )


# 대체 프롬프트 (간단한 버전)
def get_simple_react_prompt() -> PromptTemplate:
    """
    간단한 ReAct 프롬프트 (MVP용).

    Returns:
        PromptTemplate: 간단한 ReAct 프롬프트.

    """
    template = """Answer the following questions as best you can. You have access to the following tools:

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
Thought:{agent_scratchpad}"""

    return PromptTemplate(
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
        template=template,
    )
