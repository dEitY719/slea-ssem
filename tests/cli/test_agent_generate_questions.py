"""Tests for agent generate-questions command (Mode 1 question generation).

REQ: REQ-CLI-Agent-2
REQ: REQ-A-Agent-Backend-1 (CLI → Backend Service integration)
"""

import json
import re
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console

from src.cli.actions import agent
from src.cli.context import CLIContext


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


class TestGenerateQuestionsHelpAndErrors:
    """Test help command and error handling."""

    @pytest.fixture
    def mock_context(self) -> CLIContext:
        """Create CLIContext with buffered console."""
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=88)
        context = CLIContext(console=console, logger=None)
        context._buffer = buffer
        return context

    def test_help_command(self, mock_context: CLIContext) -> None:
        """TC-1: Verify --help displays usage."""
        agent.generate_questions(mock_context, "--help")
        output = mock_context._buffer.getvalue()

        assert "agent generate-questions" in output
        assert "--survey-id" in output
        assert "--round" in output
        assert "--prev-answers" in output
        assert "Usage:" in output

    def test_missing_survey_id(self, mock_context: CLIContext) -> None:
        """TC-2: Verify error when --survey-id missing."""
        agent.generate_questions(mock_context, "--round", "1")
        output = mock_context._buffer.getvalue()

        assert "Error" in output or "error" in output
        assert "survey-id" in output or "required" in output

    def test_invalid_round_number(self, mock_context: CLIContext) -> None:
        """TC-5: Verify error for invalid round number."""
        agent.generate_questions(mock_context, "--survey-id", "test_survey", "--round", "3")
        output = mock_context._buffer.getvalue()

        assert "Error" in output or "error" in output
        assert "round" in output.lower() or "must be 1 or 2" in output

    def test_invalid_json_prev_answers(self, mock_context: CLIContext) -> None:
        """TC-6: Verify error for invalid JSON."""
        agent.generate_questions(
            mock_context, "--survey-id", "test_survey", "--prev-answers", "not valid json"
        )
        output = mock_context._buffer.getvalue()

        assert "Error" in output or "error" in output
        assert "JSON" in output or "json" in output

    def test_invalid_prev_answers_not_array(self, mock_context: CLIContext) -> None:
        """Verify error when prev-answers is not JSON array."""
        agent.generate_questions(
            mock_context, "--survey-id", "test_survey", "--prev-answers", '{"key":"value"}'
        )
        output = mock_context._buffer.getvalue()

        assert "Error" in output or "error" in output
        assert "array" in output.lower()


class TestGenerateQuestionsSuccess:
    """Test successful generation scenarios."""

    @pytest.fixture
    def mock_context(self) -> CLIContext:
        """Create CLIContext with buffered console and logged-in user."""
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=88)
        context = CLIContext(console=console, logger=None)
        context._buffer = buffer
        # Set user_id for Backend Service integration test
        context.session.user_id = "123"
        return context

    @pytest.fixture
    def mock_service_response(self) -> dict:
        """Create mock Backend Service response (dict format)."""
        return {
            "session_id": "session_20251111_123456_001",
            "questions": [
                {
                    "id": "q_00001_test",
                    "item_type": "short_answer",
                    "stem": "What is a transformer in NLP?",
                    "choices": None,
                    "answer_schema": {"type": "keyword_match", "keywords": ["transformer", "attention", "neural"]},
                    "difficulty": 5,
                    "category": "NLP",
                },
                {
                    "id": "q_00002_test",
                    "item_type": "multiple_choice",
                    "stem": "Which is not a type of neural network?",
                    "choices": ["RNN", "CNN", "Abacus", "Transformer"],
                    "answer_schema": {"type": "exact_match", "correct_answer": "Abacus"},
                    "difficulty": 7,
                    "category": "ML",
                },
                {
                    "id": "q_00003_test",
                    "item_type": "true_false",
                    "stem": "True or False: GPT uses only encoder layers?",
                    "choices": None,
                    "answer_schema": {"type": "exact_match", "correct_answer": "False"},
                    "difficulty": 3,
                    "category": "AI",
                },
            ],
        }

    @patch("src.cli.actions.agent.SessionLocal")
    @patch("src.cli.actions.agent.QuestionGenerationService")
    def test_round1_generation_success(
        self, mock_service_class, mock_session_local, mock_context: CLIContext, mock_service_response
    ) -> None:
        """TC-3: Verify successful Round 1 generation."""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session

        mock_service_instance = AsyncMock()
        mock_service_instance.generate_questions.return_value = mock_service_response
        mock_service_class.return_value = mock_service_instance

        # Execute
        agent.generate_questions(mock_context, "--survey-id", "test_survey", "--round", "1")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Generating questions" in output
        assert "Generation Complete" in output
        assert "session_id: session_20251111_123456_001" in output
        assert "items generated: 3" in output

        # Verify table
        assert "Generated Items" in output
        assert "short_answer" in output
        assert "multiple_choice" in output
        assert "true_false" in output

        # Verify first item details
        assert "First Item Details" in output
        assert "What is a transformer in NLP?" in output

        # Verify service was called correctly
        mock_service_instance.generate_questions.assert_called_once()
        call_args = mock_service_instance.generate_questions.call_args
        assert call_args[1]["user_id"] == 123
        assert call_args[1]["survey_id"] == "test_survey"
        assert call_args[1]["round_num"] == 1

    @patch("src.cli.actions.agent.SessionLocal")
    @patch("src.cli.actions.agent.QuestionGenerationService")
    def test_round2_adaptive_generation(
        self, mock_service_class, mock_session_local, mock_context: CLIContext, mock_service_response
    ) -> None:
        """TC-4: Verify Round 2 adaptive generation."""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session

        mock_service_instance = AsyncMock()
        mock_service_instance.generate_questions.return_value = mock_service_response
        mock_service_class.return_value = mock_service_instance

        # Execute with prev_answers
        prev_answers = '[{"item_id":"q1","score":85}]'
        agent.generate_questions(
            mock_context,
            "--survey-id",
            "test_survey",
            "--round",
            "2",
            "--prev-answers",
            prev_answers,
        )
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Generating questions" in output
        assert "round=2" in output
        assert "items generated: 3" in output

        # Verify service was called with correct parameters
        mock_service_instance.generate_questions.assert_called_once()
        call_args = mock_service_instance.generate_questions.call_args
        assert call_args[1]["round_num"] == 2

    @patch("src.cli.actions.agent.SessionLocal")
    @patch("src.cli.actions.agent.QuestionGenerationService")
    def test_table_output_structure(
        self, mock_service_class, mock_session_local, mock_context: CLIContext, mock_service_response
    ) -> None:
        """TC-9: Verify Rich table structure."""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session

        mock_service_instance = AsyncMock()
        mock_service_instance.generate_questions.return_value = mock_service_response
        mock_service_class.return_value = mock_service_instance

        # Execute
        agent.generate_questions(mock_context, "--survey-id", "test_survey")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions for table
        assert "ID" in output
        assert "Type" in output
        assert "Difficulty" in output
        assert "Category" in output

        # Check values in output
        assert "5" in output  # Difficulty value
        assert "7" in output  # Difficulty value
        assert "3" in output  # Difficulty value
        assert "NLP" in output  # Category
        assert "ML" in output  # Category
        assert "AI" in output  # Category

    @patch("src.cli.actions.agent.SessionLocal")
    @patch("src.cli.actions.agent.QuestionGenerationService")
    def test_agent_init_failure(
        self, mock_service_class, mock_session_local, mock_context: CLIContext
    ) -> None:
        """TC-8: Verify error handling for service failure."""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session

        # Service initialization fails
        mock_service_class.side_effect = ValueError("Database connection error")

        # Execute
        agent.generate_questions(mock_context, "--survey-id", "test_survey")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Error" in output or "error" in output
        assert "Question generation failed" in output

    @patch("src.cli.actions.agent.SessionLocal")
    @patch("src.cli.actions.agent.QuestionGenerationService")
    def test_agent_execution_failure(
        self, mock_service_class, mock_session_local, mock_context: CLIContext
    ) -> None:
        """Verify error handling for service execution failure."""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session

        mock_service_instance = AsyncMock()
        mock_service_instance.generate_questions.side_effect = RuntimeError(
            "Tool timeout after 8 seconds"
        )
        mock_service_class.return_value = mock_service_instance

        # Execute
        agent.generate_questions(mock_context, "--survey-id", "test_survey")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Error" in output or "error" in output
        assert "Question generation failed" in output
        assert "Tool timeout" in output

    @patch("src.cli.actions.agent.SessionLocal")
    @patch("src.cli.actions.agent.QuestionGenerationService")
    def test_empty_items_response(
        self, mock_service_class, mock_session_local, mock_context: CLIContext
    ) -> None:
        """Verify handling of generation with no items."""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session

        empty_response = {
            "session_id": "session_20251111_123456_001",
            "questions": [],
        }
        mock_service_instance = AsyncMock()
        mock_service_instance.generate_questions.return_value = empty_response
        mock_service_class.return_value = mock_service_instance

        # Execute
        agent.generate_questions(mock_context, "--survey-id", "test_survey")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Generation Complete" in output
        assert "items generated: 0" in output
        # First item details should not be shown
        assert "First Item Details" not in output
        assert "No questions were generated" in output

    @patch("src.cli.actions.agent.SessionLocal")
    @patch("src.cli.actions.agent.QuestionGenerationService")
    def test_round1_default_when_not_specified(
        self, mock_service_class, mock_session_local, mock_context: CLIContext, mock_service_response
    ) -> None:
        """Verify Round 1 is default when --round not specified."""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session

        mock_service_instance = AsyncMock()
        mock_service_instance.generate_questions.return_value = mock_service_response
        mock_service_class.return_value = mock_service_instance

        # Execute without specifying round
        agent.generate_questions(mock_context, "--survey-id", "test_survey")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "round=1" in output
        assert "items generated: 3" in output

        # Verify service was called with round_num=1
        mock_service_instance.generate_questions.assert_called_once()
        call_args = mock_service_instance.generate_questions.call_args
        assert call_args[1]["round_num"] == 1
