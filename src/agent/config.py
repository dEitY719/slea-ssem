"""
Agent Configuration.

REQ: REQ-A-ItemGen
"""

from os import getenv

from langchain_google_genai import ChatGoogleGenerativeAI


def create_llm() -> ChatGoogleGenerativeAI:
    """
    Create Google Gemini LLM for MVP 1.0.

    Returns:
        ChatGoogleGenerativeAI: LangChain ChatGoogleGenerativeAI instance.

    Environment Variables:
        GEMINI_API_KEY: Google Gemini API Key.

    """
    api_key = getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

    return ChatGoogleGenerativeAI(
        api_key=api_key,
        model="gemini-1.5-pro",
        temperature=0.7,  # 창의성과 정확성의 균형 (0~1)
        max_tokens=2048,  # 응답 최대 길이
        top_p=0.95,  # Nucleus sampling (다양성 제어)
        timeout=30,  # API 타임아웃 (초)
    )


# Agent 설정
AGENT_CONFIG = {
    "max_iterations": 10,  # 최대 에이전트 반복 횟수
    "early_stopping_method": "force",  # 최대 반복 도달 시 강제 중지
    "verbose": True,  # 상세 로깅 활성화
    "handle_parsing_errors": True,  # 파싱 에러 자동 처리
    "return_intermediate_steps": True,  # 중간 단계 반환 (디버깅용)
}

# Tool 타임아웃 설정
TOOL_CONFIG = {
    "get_user_profile": 5,  # 5초
    "search_question_templates": 10,  # 10초
    "get_difficulty_keywords": 5,  # 5초
    "validate_question_quality": 15,  # 15초 (LLM 호출)
    "save_generated_question": 10,  # 10초
    "score_and_explain": 15,  # 15초 (LLM 호출)
}
