"""
Pytest Configuration for Agent Tests

Provides shared fixtures and configuration for ItemGenAgent testing.
"""

import pytest
from unittest.mock import AsyncMock
import sys
import os
from typing import Any

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
            user_id="test_user",
            difficulty=5,
            interests=["AI", "ML"],
            num_questions=3,
        ),
        "valid_score_request": ScoreAnswerRequest(
            session_id="sess_test",
            user_id="user_test",
            question_id="q_test",
            question_type="short_answer",
            user_answer="Test answer",
            correct_keywords=["test", "answer"],
        ),
    }
