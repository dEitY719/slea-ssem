"""Tests for agent generate-questions command (Mode 1 question generation).

REQ: REQ-CLI-Agent-2
"""

import json
import re
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console

from src.agent.llm_agent import (
    AnswerSchema,
    GenerateQuestionsResponse,
    GeneratedItem,
)
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
        """Create CLIContext with buffered console."""
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=88)
        context = CLIContext(console=console, logger=None)
        context._buffer = buffer
        return context

    @pytest.fixture
    def mock_agent_response(self) -> GenerateQuestionsResponse:
        """Create mock agent response with 3 questions."""
        items = [
            GeneratedItem(
                id="q_00001_test",
                type="short_answer",
                stem="What is a transformer in NLP?",
                choices=None,
                answer_schema=AnswerSchema(
                    type="keyword_match", keywords=["transformer", "attention", "neural"]
                ),
                difficulty=5,
                category="NLP",
                validation_score=0.92,
            ),
            GeneratedItem(
                id="q_00002_test",
                type="multiple_choice",
                stem="Which is not a type of neural network?",
                choices=["RNN", "CNN", "Abacus", "Transformer"],
                answer_schema=AnswerSchema(type="exact_match", correct_answer="Abacus"),
                difficulty=7,
                category="ML",
                validation_score=0.89,
            ),
            GeneratedItem(
                id="q_00003_test",
                type="true_false",
                stem="True or False: GPT uses only encoder layers?",
                choices=None,
                answer_schema=AnswerSchema(type="exact_match", correct_answer="False"),
                difficulty=3,
                category="AI",
                validation_score=0.95,
            ),
        ]
        return GenerateQuestionsResponse(
            round_id="round_20251111_123456_001",
            items=items,
            agent_steps=12,
            failed_count=0,
        )

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_round1_generation_success(
        self, mock_agent_class, mock_context: CLIContext, mock_agent_response
    ) -> None:
        """TC-3: Verify successful Round 1 generation."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.generate_questions.return_value = mock_agent_response
        mock_agent_class.return_value = mock_agent_instance

        # Execute
        agent.generate_questions(mock_context, "--survey-id", "test_survey", "--round", "1")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Initializing Agent" in output
        assert "Agent initialized" in output
        assert "Generating questions" in output
        assert "Generation Complete" in output
        assert "round_id: round_20251111_123456_001" in output
        assert "items generated: 3" in output
        assert "agent_steps: 12" in output

        # Verify table
        assert "Generated Items" in output
        assert "short_answer" in output
        assert "multiple_choice" in output
        assert "true_false" in output

        # Verify first item details
        assert "First Item Details" in output
        assert "What is a transformer in NLP?" in output
        assert "keyword_match" in output

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_round2_adaptive_generation(
        self, mock_agent_class, mock_context: CLIContext, mock_agent_response
    ) -> None:
        """TC-4: Verify Round 2 adaptive generation."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.generate_questions.return_value = mock_agent_response
        mock_agent_class.return_value = mock_agent_instance

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

        # Verify agent was called with correct request
        mock_agent_instance.generate_questions.assert_called_once()
        call_args = mock_agent_instance.generate_questions.call_args
        request = call_args[0][0]
        assert request.round_idx == 2
        assert request.prev_answers == [{"item_id": "q1", "score": 85}]

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_table_output_structure(
        self, mock_agent_class, mock_context: CLIContext, mock_agent_response
    ) -> None:
        """TC-9: Verify Rich table structure."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.generate_questions.return_value = mock_agent_response
        mock_agent_class.return_value = mock_agent_instance

        # Execute
        agent.generate_questions(mock_context, "--survey-id", "test_survey")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions for table
        assert "ID" in output
        assert "Type" in output
        assert "Difficulty" in output
        assert "Validation" in output

        # Check values in output
        assert "5" in output  # Difficulty value
        assert "7" in output  # Difficulty value
        assert "3" in output  # Difficulty value
        assert "0.92" in output  # Validation score
        assert "0.89" in output  # Validation score
        assert "0.95" in output  # Validation score

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_agent_init_failure(
        self, mock_agent_class, mock_context: CLIContext
    ) -> None:
        """TC-8: Verify error handling for agent init failure."""
        # Setup mock to raise exception
        mock_agent_class.side_effect = ValueError("GEMINI_API_KEY not found")

        # Execute
        agent.generate_questions(mock_context, "--survey-id", "test_survey")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Error" in output or "error" in output
        assert "Agent initialization failed" in output
        assert "GEMINI_API_KEY" in output

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_agent_execution_failure(
        self, mock_agent_class, mock_context: CLIContext
    ) -> None:
        """Verify error handling for agent execution failure."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.generate_questions.side_effect = RuntimeError(
            "Tool timeout after 8 seconds"
        )
        mock_agent_class.return_value = mock_agent_instance

        # Execute
        agent.generate_questions(mock_context, "--survey-id", "test_survey")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Error" in output or "error" in output
        assert "Question generation failed" in output
        assert "Tool timeout" in output

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_empty_items_response(
        self, mock_agent_class, mock_context: CLIContext
    ) -> None:
        """Verify handling of generation with no items."""
        # Setup mock with empty response
        empty_response = GenerateQuestionsResponse(
            round_id="round_20251111_123456_001",
            items=[],
            agent_steps=5,
            failed_count=0,
        )
        mock_agent_instance = AsyncMock()
        mock_agent_instance.generate_questions.return_value = empty_response
        mock_agent_class.return_value = mock_agent_instance

        # Execute
        agent.generate_questions(mock_context, "--survey-id", "test_survey")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Generation Complete" in output
        assert "items generated: 0" in output
        # First item details should not be shown
        assert "First Item Details" not in output

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_round1_default_when_not_specified(
        self, mock_agent_class, mock_context: CLIContext, mock_agent_response
    ) -> None:
        """Verify Round 1 is default when --round not specified."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.generate_questions.return_value = mock_agent_response
        mock_agent_class.return_value = mock_agent_instance

        # Execute without specifying round
        agent.generate_questions(mock_context, "--survey-id", "test_survey")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "round=1" in output

        # Verify agent was called with round_idx=1
        call_args = mock_agent_instance.generate_questions.call_args
        request = call_args[0][0]
        assert request.round_idx == 1
