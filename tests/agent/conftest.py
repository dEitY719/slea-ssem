"""
Pytest Configuration for Agent Tests

Provides shared fixtures and configuration for ItemGenAgent testing.
"""

import os
import sys
from typing import Any
from unittest.mock import AsyncMock

import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


@pytest.fixture
async def mock_executor() -> AsyncMock:
    """Fixture: Mock AgentExecutor for testing."""
    executor = AsyncMock()
    executor.ainvoke = AsyncMock()
    return executor


@pytest.fixture
def mock_llm_response() -> dict[str, Any]:
    """Fixture: Common LLM response patterns."""
    return {
        "success_generate": {
            "output": "Generated question successfully",
            "intermediate_steps": [
                ("Tool 1", "user_profile"),
                ("Tool 3", "keywords"),
                ("Tool 4", "validation"),
                ("Tool 5", "saved"),
            ],
        },
        "success_score": {
            "output": "Score: 85\nExplanation: Well answered",
            "intermediate_steps": [("Tool 6", "graded")],
        },
        "error_response": {
            "output": "Error occurred during processing",
            "error": True,
        },
    }


@pytest.fixture
def sample_pydantic_schemas() -> dict[str, Any]:
    """Fixture: Sample Pydantic schema instances."""
    from src.agent.llm_agent import GenerateQuestionsRequest, ScoreAnswerRequest

    return {
        "valid_generate_request": GenerateQuestionsRequest(
            session_id="session_test",
            survey_id="survey_test",
            round_idx=1,
        ),
        "valid_score_request": ScoreAnswerRequest(
            round_id="round_test",
            item_id="item_test",
            user_answer="Test answer",
        ),
    }
