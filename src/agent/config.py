"""
Agent Configuration.

REQ: REQ-A-ItemGen

Design Patterns:
- Dependency Inversion Principle (DIP): Use abstract base for LLM providers
- Strategy Pattern: Different LLM providers (GoogleGenerativeAI, LiteLLM)
- Factory Pattern: LLMFactory selects provider based on environment
- Single Responsibility: Each provider handles its own configuration
"""

import logging
from abc import ABC, abstractmethod
from os import getenv
from typing import Any

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


# ============================================================================
# Helper: LiteLLM Message Wrapper (OpenAI 호환성)
# ============================================================================


class LiteLLMCompatibleOpenAI(ChatOpenAI):
    """
    ChatOpenAI wrapper that ensures OpenAI API compatibility with LiteLLM.

    OpenAI API requires 'content' field in assistant messages, even when
    tool_calls are present. This wrapper ensures content field is never null.

    REQ: REQ-A-ItemGen (LiteLLM message format fix for gpt-oss-120b)
    """

    def _process_message_for_api(self, message: AIMessage) -> dict[str, Any]:
        """
        Ensure content field is always present for OpenAI API compatibility.

        Args:
            message: LangChain AIMessage

        Returns:
            Processed message dict for OpenAI API
        """
        msg_dict = {
            "role": "assistant",
            "content": getattr(message, "content", "") or "",  # Ensure content is never None
        }

        # Add tool_calls if present
        if hasattr(message, "tool_calls") and message.tool_calls:
            msg_dict["tool_calls"] = message.tool_calls

        return msg_dict


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Defines interface for creating LLM instances with different backends.
    Adheres to Dependency Inversion Principle (DIP).
    """

    @abstractmethod
    def create(self) -> ChatGoogleGenerativeAI | ChatOpenAI:
        """
        Create LLM instance.

        Returns:
            Union[ChatGoogleGenerativeAI, ChatOpenAI]: Configured LLM instance.

        Raises:
            ValueError: If required environment variables are not set.

        """
        pass


class GoogleGenerativeAIProvider(LLMProvider):
    """
    Google Generative AI (Gemini) LLM provider.

    Creates ChatGoogleGenerativeAI instances with optimized settings for
    MVP 1.0 question generation and scoring tasks.
    """

    def create(self) -> ChatGoogleGenerativeAI:
        """
        Create Google Gemini LLM instance.

        Returns:
            ChatGoogleGenerativeAI: Configured ChatGoogleGenerativeAI instance.

        Raises:
            ValueError: If GEMINI_API_KEY is not set.

        Environment Variables:
            GEMINI_API_KEY: Google Gemini API Key (required).

        """
        api_key = getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

        return ChatGoogleGenerativeAI(
            api_key=api_key,
            model="gemini-2.0-flash",
            temperature=0.3,  # 결정적 도구 호출 (0.7 → 0.3으로 감소: ReAct 형식 일관성 향상)
            max_output_tokens=8192,  # 응답 최대 길이 (2024년 증가: 1024 → 4096 → 8192, 전체 ReAct 대화 및 다중 문항 생성 지원)
            top_p=0.95,  # Nucleus sampling (다양성 제어)
            timeout=30,  # API 타임아웃 (초)
        )


class LiteLLMProvider(LLMProvider):
    """
    LiteLLM-compatible LLM provider using ChatOpenAI client.

    Supports connecting to LiteLLM proxy server which provides unified
    interface for multiple LLM backends (Gemini, Claude, Qwen, etc.)
    """

    def create(self) -> ChatOpenAI:
        """
        Create ChatOpenAI instance connected to LiteLLM proxy.

        Returns:
            ChatOpenAI: Configured ChatOpenAI instance for LiteLLM.

        Raises:
            ValueError: If required environment variables are not set.

        Environment Variables:
            LITELLM_API_KEY: LiteLLM API key (optional, can be any value).
            LITELLM_BASE_URL: LiteLLM proxy base URL (required).
                Example: "http://localhost:4444/v1"
            LITELLM_MODEL: Model name to use (default: "gpt-4").
                Example: "gemini-2.5-pro", "gpt-4o", "claude-3-sonnet"

        """
        base_url = getenv("LITELLM_BASE_URL")
        if not base_url:
            raise ValueError("LITELLM_BASE_URL 환경 변수가 설정되지 않았습니다.")

        api_key = getenv("LITELLM_API_KEY", "sk-dummy-key")
        model = getenv("LITELLM_MODEL", "gpt-4")

        return LiteLLMCompatibleOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.3,  # 결정적 도구 호출 (0.7 → 0.3으로 감소: ReAct 형식 일관성 향상)
            max_tokens=8192,  # LiteLLM 프록시 호환성 (보수적 설정)
            timeout=30,  # API 타임아웃 (초)
            default_headers={
                "Accept": "application/json",
            },
        )


class LLMFactory:
    """
    Factory for creating LLM providers based on configuration.

    Adheres to Factory Pattern and Single Responsibility Principle (SRP).
    Selects appropriate provider based on USE_LITE_LLM environment variable.
    """

    @staticmethod
    def get_provider() -> LLMProvider:
        """
        Get appropriate LLM provider based on environment configuration.

        Returns:
            LLMProvider: Either GoogleGenerativeAIProvider or LiteLLMProvider.

        Environment Variables:
            USE_LITE_LLM: "True" (case-insensitive) to use LiteLLM,
                         otherwise uses Google Generative AI.

        """
        use_lite_llm = getenv("USE_LITE_LLM", "False").lower() == "true"

        if use_lite_llm:
            return LiteLLMProvider()

        return GoogleGenerativeAIProvider()


def create_llm() -> ChatGoogleGenerativeAI | ChatOpenAI:
    """
    Create LLM instance based on environment configuration.

    This is the main public API for LLM creation. It delegates to
    LLMFactory to select the appropriate provider and creates the
    LLM instance with optimized default settings.

    Returns:
        Union[ChatGoogleGenerativeAI, ChatOpenAI]: Configured LLM instance.

    Raises:
        ValueError: If required environment variables are not set.

    Environment Variables:
        USE_LITE_LLM: Set to "True" to use LiteLLM (ChatOpenAI).
                     Otherwise uses Google Generative AI.
        GEMINI_API_KEY: Required if USE_LITE_LLM is not "True".
        LITELLM_BASE_URL: Required if USE_LITE_LLM is "True".
        LITELLM_API_KEY: Optional, defaults to "sk-dummy-key".
        LITELLM_MODEL: Optional, defaults to "gpt-4".

    Example:
        >>> # Use Google Generative AI (default)
        >>> # Set GEMINI_API_KEY in .env
        >>> llm = create_llm()

        >>> # Use LiteLLM
        >>> # Set USE_LITE_LLM=True, LITELLM_BASE_URL, etc in .env
        >>> llm = create_llm()

    """
    provider = LLMFactory.get_provider()
    return provider.create()


# Agent 설정
AGENT_CONFIG = {
    "max_iterations": 10,  # 최대 에이전트 반복 횟수
    "early_stopping_method": "force",  # 최대 반복 도달 시 강제 중지
    "verbose": True,  # 상세 로깅 활성화
    "handle_parsing_errors": True,  # 파싱 에러 자동 처리
    "return_intermediate_steps": True,  # 중간 단계 반환 (디버깅용)
}

# Tool 타임아웃 설정 (최적화: 응답성 개선)
TOOL_CONFIG = {
    "get_user_profile": 3,  # 5초 → 3초 (DB 쿼리 빠름)
    "search_question_templates": 5,  # 10초 → 5초 (캐싱 활용)
    "get_difficulty_keywords": 2,  # 5초 → 2초 (메모리 기반)
    "validate_question_quality": 8,  # 15초 → 8초 (LLM 호출 최적화)
    "save_generated_question": 5,  # 10초 → 5초 (DB 저장)
    "score_and_explain": 8,  # 15초 → 8초 (LLM 호출 최적화)
}

# REQ-AGENT-0-0: Structured Output 위험 관리 설정
STRUCTURED_OUTPUT_CONFIG: dict[str, Any] = {
    "enabled": getenv("ENABLE_STRUCTURED_OUTPUT", "False").lower() == "true",
    "rollout_percentage": float(getenv("STRUCTURED_OUTPUT_ROLLOUT", "100.0")),
    "max_failures_before_disable": int(getenv("MAX_STRUCTURED_FAILURES", "3")),
    "success_rate_threshold": 0.95,  # 95%
    "latency_threshold_seconds": 5.0,
    "parser_error_rate_threshold": 0.01,  # 1%
}


def should_use_structured_output(model_name: str, failure_count: int = 0) -> bool:
    """
    Determine if structured output should be used for given model.

    REQ: REQ-AGENT-0-0 (Risk Management Strategy)

    This function implements a feature flag system to control structured output
    usage across different LLM models (Gemini vs DeepSeek). It includes:
    - Global enable/disable via environment variable
    - Model-based routing (Gemini supports it, DeepSeek doesn't)
    - Circuit breaker pattern (auto-disable after repeated failures)

    Args:
        model_name: LLM model name (e.g., "gemini-2.0-flash", "deepseek-chat").
                   Case-insensitive matching.
        failure_count: Current consecutive failure count for rollback logic.
                      Used to implement circuit breaker pattern.

    Returns:
        bool: True if structured output should be used, False otherwise.

    Decision Logic:
        1. If globally disabled (ENABLE_STRUCTURED_OUTPUT=false) → False
        2. If failure_count >= max_failures_before_disable → False (circuit breaker)
        3. If "gemini" in model_name (case-insensitive) → True
        4. If "deepseek" in model_name → False (uses TextReActAgent)
        5. Otherwise (unknown model) → False (conservative default)

    Side Effects:
        - Logs decision with model name and reason (INFO level)
        - Logs alert if circuit breaker triggers (WARNING level)

    Example:
        >>> should_use_structured_output("gemini-2.0-flash", failure_count=0)
        True

        >>> should_use_structured_output("deepseek-chat", failure_count=0)
        False

        >>> should_use_structured_output("gemini-2.0-flash", failure_count=3)
        False  # Circuit breaker triggered

    Environment Variables:
        ENABLE_STRUCTURED_OUTPUT: "true" to enable globally (default: "false")
        MAX_STRUCTURED_FAILURES: Max failures before auto-disable (default: "3")

    """
    # Step 1: Check global enable flag
    if not STRUCTURED_OUTPUT_CONFIG["enabled"]:
        logger.info(
            f"Structured output disabled globally for model={model_name} "
            f"(ENABLE_STRUCTURED_OUTPUT=false)"
        )
        return False

    # Step 2: Check failure count (circuit breaker)
    max_failures = STRUCTURED_OUTPUT_CONFIG["max_failures_before_disable"]
    if failure_count >= max_failures:
        logger.warning(
            f"Circuit breaker triggered: Auto-disabling structured output for model={model_name} "
            f"(failure_count={failure_count} >= max={max_failures})"
        )
        return False

    # Step 3: Check model compatibility
    model_lower = model_name.lower()

    if "gemini" in model_lower:
        logger.info(f"Structured output enabled for Gemini model={model_name}")
        return True

    if "deepseek" in model_lower:
        logger.info(
            f"Structured output disabled for DeepSeek model={model_name} "
            f"(uses TextReActAgent path)"
        )
        return False

    # Step 4: Unknown model - conservative default
    logger.info(
        f"Structured output disabled for unknown model={model_name} "
        f"(conservative default)"
    )
    return False
