"""
Tests for agent configuration module.

REQ: REQ-A-LiteLLM (LiteLLM support for create_llm())
"""

import os
from unittest.mock import patch

import pytest
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from src.agent.config import (
    GoogleGenerativeAIProvider,
    LiteLLMProvider,
    LLMFactory,
    LLMProvider,
    create_llm,
)


class TestGoogleGenerativeAIProvider:
    """Tests for GoogleGenerativeAIProvider class."""

    def test_create_with_valid_gemini_api_key(self) -> None:
        """
        Test GoogleGenerativeAIProvider.create() returns ChatGoogleGenerativeAI instance.

        Acceptance Criteria:
        - Provider creates ChatGoogleGenerativeAI with GEMINI_API_KEY
        - Instance has correct model name ("gemini-2.0-flash")
        - Instance has correct temperature (0.7)
        - Instance has correct max_output_tokens (8192)
        """
        provider = GoogleGenerativeAIProvider()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-12345"}):
            llm = provider.create()

            assert isinstance(llm, ChatGoogleGenerativeAI)
            # ChatGoogleGenerativeAI automatically prepends "models/" to model name
            assert llm.model == "models/gemini-2.0-flash"
            assert llm.temperature == 0.7
            assert llm.max_output_tokens == 8192

    def test_create_raises_error_when_gemini_api_key_missing(self) -> None:
        """
        Test GoogleGenerativeAIProvider.create() raises ValueError when GEMINI_API_KEY is missing.

        Acceptance Criteria:
        - Raises ValueError
        - Error message mentions GEMINI_API_KEY
        """
        provider = GoogleGenerativeAIProvider()
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="GEMINI_API_KEY 환경 변수가 설정되지 않았습니다"
            ):
                provider.create()

    def test_provider_is_abstract_interface(self) -> None:
        """
        Test that GoogleGenerativeAIProvider implements LLMProvider interface.

        Acceptance Criteria:
        - GoogleGenerativeAIProvider is subclass of LLMProvider
        - Implements create() method
        """
        provider = GoogleGenerativeAIProvider()
        assert isinstance(provider, LLMProvider)
        assert hasattr(provider, "create")
        assert callable(provider.create)


class TestLiteLLMProvider:
    """Tests for LiteLLMProvider class."""

    def test_create_with_valid_litellm_config(self) -> None:
        """
        Test LiteLLMProvider.create() returns ChatOpenAI instance with LiteLLM settings.

        Acceptance Criteria:
        - Provider creates ChatOpenAI instance
        - Instance uses custom base_url (LiteLLM proxy endpoint)
        - Instance has correct model from environment
        - Instance has correct temperature (0.7)
        - Instance has correct max_tokens (2048)
        """
        provider = LiteLLMProvider()
        env_vars = {
            "LITELLM_BASE_URL": "http://localhost:4444/v1",
            "LITELLM_API_KEY": "sk-4444",
            "LITELLM_MODEL": "gemini-2.5-pro",
        }
        with patch.dict(os.environ, env_vars):
            llm = provider.create()

            assert isinstance(llm, ChatOpenAI)
            assert llm.model_name == "gemini-2.5-pro"
            assert llm.temperature == 0.7
            assert llm.max_tokens == 2048

    def test_create_raises_error_when_litellm_base_url_missing(self) -> None:
        """
        Test LiteLLMProvider.create() raises ValueError when LITELLM_BASE_URL is missing.

        Acceptance Criteria:
        - Raises ValueError
        - Error message mentions LITELLM_BASE_URL
        """
        provider = LiteLLMProvider()
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="LITELLM_BASE_URL 환경 변수가 설정되지 않았습니다"
            ):
                provider.create()

    def test_create_with_default_api_key(self) -> None:
        """
        Test LiteLLMProvider.create() uses default API key when LITELLM_API_KEY is not set.

        Acceptance Criteria:
        - Creates ChatOpenAI with default api_key="sk-dummy-key"
        """
        provider = LiteLLMProvider()
        env_vars = {
            "LITELLM_BASE_URL": "http://localhost:4444/v1",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            llm = provider.create()
            assert isinstance(llm, ChatOpenAI)

    def test_create_with_default_model(self) -> None:
        """
        Test LiteLLMProvider.create() uses default model when LITELLM_MODEL is not set.

        Acceptance Criteria:
        - Creates ChatOpenAI with default model="gpt-4"
        """
        provider = LiteLLMProvider()
        env_vars = {
            "LITELLM_BASE_URL": "http://localhost:4444/v1",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            llm = provider.create()
            assert llm.model_name == "gpt-4"

    def test_provider_is_abstract_interface(self) -> None:
        """
        Test that LiteLLMProvider implements LLMProvider interface.

        Acceptance Criteria:
        - LiteLLMProvider is subclass of LLMProvider
        - Implements create() method
        """
        provider = LiteLLMProvider()
        assert isinstance(provider, LLMProvider)
        assert hasattr(provider, "create")
        assert callable(provider.create)


class TestLLMFactory:
    """Tests for LLMFactory class."""

    def test_get_provider_returns_litellm_when_use_lite_llm_true(self) -> None:
        """
        Test LLMFactory.get_provider() returns LiteLLMProvider when USE_LITE_LLM=True.

        Acceptance Criteria:
        - Returns LiteLLMProvider instance
        - Provider is LLMProvider subclass
        """
        with patch.dict(os.environ, {"USE_LITE_LLM": "True"}):
            provider = LLMFactory.get_provider()
            assert isinstance(provider, LiteLLMProvider)
            assert isinstance(provider, LLMProvider)

    def test_get_provider_returns_google_when_use_lite_llm_false(self) -> None:
        """
        Test LLMFactory.get_provider() returns GoogleGenerativeAIProvider when USE_LITE_LLM=False.

        Acceptance Criteria:
        - Returns GoogleGenerativeAIProvider instance
        - Provider is LLMProvider subclass
        """
        with patch.dict(os.environ, {"USE_LITE_LLM": "False"}):
            provider = LLMFactory.get_provider()
            assert isinstance(provider, GoogleGenerativeAIProvider)
            assert isinstance(provider, LLMProvider)

    def test_get_provider_returns_google_when_use_lite_llm_not_set(self) -> None:
        """
        Test LLMFactory.get_provider() returns GoogleGenerativeAIProvider when USE_LITE_LLM is not set.

        Acceptance Criteria:
        - Default behavior returns GoogleGenerativeAIProvider
        """
        with patch.dict(os.environ, {}, clear=True):
            provider = LLMFactory.get_provider()
            assert isinstance(provider, GoogleGenerativeAIProvider)

    def test_get_provider_case_insensitive(self) -> None:
        """
        Test LLMFactory.get_provider() is case-insensitive for USE_LITE_LLM.

        Acceptance Criteria:
        - "true", "True", "TRUE" all return LiteLLMProvider
        - "false", "False", "FALSE" all return GoogleGenerativeAIProvider
        """
        for value in ["true", "True", "TRUE"]:
            with patch.dict(os.environ, {"USE_LITE_LLM": value}):
                provider = LLMFactory.get_provider()
                assert isinstance(provider, LiteLLMProvider)

        for value in ["false", "False", "FALSE"]:
            with patch.dict(os.environ, {"USE_LITE_LLM": value}):
                provider = LLMFactory.get_provider()
                assert isinstance(provider, GoogleGenerativeAIProvider)


class TestCreateLLMFunction:
    """Tests for create_llm() public API function."""

    def test_create_llm_with_google_provider(self) -> None:
        """
        Test create_llm() returns ChatGoogleGenerativeAI when USE_LITE_LLM=False.

        Acceptance Criteria:
        - Returns ChatGoogleGenerativeAI instance
        - No errors with valid GEMINI_API_KEY
        """
        env_vars = {
            "USE_LITE_LLM": "False",
            "GEMINI_API_KEY": "test-key-12345",
        }
        with patch.dict(os.environ, env_vars):
            llm = create_llm()
            assert isinstance(llm, ChatGoogleGenerativeAI)

    def test_create_llm_with_litellm_provider(self) -> None:
        """
        Test create_llm() returns ChatOpenAI when USE_LITE_LLM=True.

        Acceptance Criteria:
        - Returns ChatOpenAI instance
        - No errors with valid LiteLLM configuration
        """
        env_vars = {
            "USE_LITE_LLM": "True",
            "LITELLM_BASE_URL": "http://localhost:4444/v1",
            "LITELLM_MODEL": "gpt-4",
        }
        with patch.dict(os.environ, env_vars):
            llm = create_llm()
            assert isinstance(llm, ChatOpenAI)

    def test_create_llm_propagates_google_provider_errors(self) -> None:
        """
        Test create_llm() propagates errors from GoogleGenerativeAIProvider.

        Acceptance Criteria:
        - Raises ValueError when GEMINI_API_KEY is missing
        """
        with patch.dict(os.environ, {"USE_LITE_LLM": "False"}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                create_llm()

    def test_create_llm_propagates_litellm_provider_errors(self) -> None:
        """
        Test create_llm() propagates errors from LiteLLMProvider.

        Acceptance Criteria:
        - Raises ValueError when LITELLM_BASE_URL is missing
        """
        with patch.dict(os.environ, {"USE_LITE_LLM": "True"}, clear=True):
            with pytest.raises(ValueError, match="LITELLM_BASE_URL"):
                create_llm()

    def test_create_llm_default_behavior(self) -> None:
        """
        Test create_llm() defaults to GoogleGenerativeAIProvider when USE_LITE_LLM is not set.

        Acceptance Criteria:
        - Returns ChatGoogleGenerativeAI with default configuration
        """
        env_vars = {
            "GEMINI_API_KEY": "test-key-12345",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            llm = create_llm()
            assert isinstance(llm, ChatGoogleGenerativeAI)
