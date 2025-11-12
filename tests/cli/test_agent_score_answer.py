"""Tests for agent score-answer command (Mode 2 single scoring).

REQ: REQ-CLI-Agent-3
"""

import json
import re
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console

from src.agent.llm_agent import (
    ScoreAnswerResponse,
)
from src.cli.actions import agent
from src.cli.context import CLIContext


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


class TestScoreAnswerHelpAndErrors:
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
        agent.score_answer(mock_context, "--help")
        output = mock_context._buffer.getvalue()

        assert "agent score-answer" in output
        assert "--question-id" in output
        assert "--question" in output
        assert "--answer-type" in output
        assert "--user-answer" in output
        assert "--correct-answer" in output
        assert "Usage:" in output

    def test_missing_question_id(self, mock_context: CLIContext) -> None:
        """TC-2: Verify error when --question-id missing."""
        agent.score_answer(
            mock_context,
            "--question", "What is X?",
            "--answer-type", "multiple_choice",
            "--user-answer", "A",
            "--correct-answer", "A"
        )
        output = mock_context._buffer.getvalue()

        assert "Error" in output or "error" in output
        assert "question-id" in output or "required" in output

    def test_missing_question(self, mock_context: CLIContext) -> None:
        """Verify error when --question missing."""
        agent.score_answer(
            mock_context,
            "--question-id", "q_001",
            "--answer-type", "multiple_choice",
            "--user-answer", "A",
            "--correct-answer", "A"
        )
        output = mock_context._buffer.getvalue()

        assert "Error" in output or "error" in output
        assert "question" in output.lower()

    def test_invalid_answer_type(self, mock_context: CLIContext) -> None:
        """TC-6: Verify error for invalid answer-type."""
        agent.score_answer(
            mock_context,
            "--question-id", "q_001",
            "--question", "What is X?",
            "--answer-type", "invalid_type",
            "--user-answer", "A",
            "--correct-answer", "A"
        )
        output = mock_context._buffer.getvalue()

        assert "Error" in output or "error" in output
        assert "answer-type" in output.lower() or "type" in output.lower()

    def test_missing_user_answer(self, mock_context: CLIContext) -> None:
        """Verify error when --user-answer missing."""
        agent.score_answer(
            mock_context,
            "--question-id", "q_001",
            "--question", "What is X?",
            "--answer-type", "multiple_choice",
            "--correct-answer", "A"
        )
        output = mock_context._buffer.getvalue()

        assert "Error" in output or "error" in output
        assert "user-answer" in output.lower()

    def test_missing_correct_answer(self, mock_context: CLIContext) -> None:
        """Verify error when --correct-answer missing."""
        agent.score_answer(
            mock_context,
            "--question-id", "q_001",
            "--question", "What is X?",
            "--answer-type", "multiple_choice",
            "--user-answer", "A"
        )
        output = mock_context._buffer.getvalue()

        assert "Error" in output or "error" in output
        assert "correct-answer" in output.lower()


class TestScoreAnswerSuccess:
    """Test successful scoring scenarios."""

    @pytest.fixture
    def mock_context(self) -> CLIContext:
        """Create CLIContext with buffered console."""
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=88)
        context = CLIContext(console=console, logger=None)
        context._buffer = buffer
        return context

    @pytest.fixture
    def mock_score_response_correct(self) -> ScoreAnswerResponse:
        """Create mock response for correct answer."""
        return ScoreAnswerResponse(
            item_id="q_001_test",
            score=100,
            correct=True,
            explanation="The answer 'Option A' is correct because...",
            keyword_matches=["keyword1", "keyword2"],
            feedback="Excellent answer!",
            confidence=0.95,
            graded_at="2025-11-11T12:00:00Z",
        )

    @pytest.fixture
    def mock_score_response_incorrect(self) -> ScoreAnswerResponse:
        """Create mock response for incorrect answer."""
        return ScoreAnswerResponse(
            item_id="q_002_test",
            score=0,
            correct=False,
            explanation="The correct answer is 'Option A', but you selected 'Option B'",
            keyword_matches=[],
            feedback="Incorrect. Please review the material.",
            confidence=0.92,
            graded_at="2025-11-11T12:00:01Z",
        )

    @pytest.fixture
    def mock_score_response_partial(self) -> ScoreAnswerResponse:
        """Create mock response for partial credit."""
        return ScoreAnswerResponse(
            item_id="q_003_test",
            score=65,
            correct=False,
            explanation="Your answer is partially correct. You covered...",
            keyword_matches=["concept1"],
            feedback="Good effort, but missing some key points.",
            confidence=0.88,
            graded_at="2025-11-11T12:00:02Z",
        )

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_score_multiple_choice_correct(
        self, mock_agent_class, mock_context: CLIContext, mock_score_response_correct
    ) -> None:
        """TC-3: Verify successful MC answer scoring (correct)."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.score_answer.return_value = mock_score_response_correct
        mock_agent_class.return_value = mock_agent_instance

        # Execute
        agent.score_answer(
            mock_context,
            "--question-id", "q_001",
            "--question", "What is a transformer?",
            "--answer-type", "multiple_choice",
            "--user-answer", "Option A",
            "--correct-answer", "Option A"
        )
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Initializing Agent" in output
        assert "Agent initialized" in output
        assert "Scoring answer" in output
        assert "Scoring Complete" in output
        assert "correct: True" in output
        assert "score: 100" in output
        assert "Scoring Result" in output
        assert "Explanation" in output

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_score_multiple_choice_incorrect(
        self, mock_agent_class, mock_context: CLIContext, mock_score_response_incorrect
    ) -> None:
        """TC-4: Verify scoring for incorrect answer."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.score_answer.return_value = mock_score_response_incorrect
        mock_agent_class.return_value = mock_agent_instance

        # Execute
        agent.score_answer(
            mock_context,
            "--question-id", "q_002",
            "--question", "What is a transformer?",
            "--answer-type", "multiple_choice",
            "--user-answer", "Option B",
            "--correct-answer", "Option A"
        )
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Scoring Complete" in output
        assert "correct: False" in output
        assert "score: 0" in output
        assert "INCORRECT" in output

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_score_short_answer_partial(
        self, mock_agent_class, mock_context: CLIContext, mock_score_response_partial
    ) -> None:
        """TC-5: Verify partial credit for short answer."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.score_answer.return_value = mock_score_response_partial
        mock_agent_class.return_value = mock_agent_instance

        # Execute
        agent.score_answer(
            mock_context,
            "--question-id", "q_003",
            "--question", "Explain transformer architecture.",
            "--answer-type", "short_answer",
            "--user-answer", "Partial response",
            "--correct-answer", "Complete response about transformers"
        )
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Scoring Complete" in output
        assert "correct: False" in output
        assert "score: 65" in output  # Partial credit

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_agent_init_failure(
        self, mock_agent_class, mock_context: CLIContext
    ) -> None:
        """TC-7: Verify error handling for agent init failure."""
        # Setup mock to raise exception
        mock_agent_class.side_effect = ValueError("GEMINI_API_KEY not found")

        # Execute
        agent.score_answer(
            mock_context,
            "--question-id", "q_001",
            "--question", "What is X?",
            "--answer-type", "multiple_choice",
            "--user-answer", "A",
            "--correct-answer", "A"
        )
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Error" in output or "error" in output
        assert "Agent initialization failed" in output
        assert "GEMINI_API_KEY" in output

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_agent_execution_failure(
        self, mock_agent_class, mock_context: CLIContext
    ) -> None:
        """TC-8: Verify error handling for agent execution failure."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.score_answer.side_effect = RuntimeError(
            "Tool timeout after 30 seconds"
        )
        mock_agent_class.return_value = mock_agent_instance

        # Execute
        agent.score_answer(
            mock_context,
            "--question-id", "q_001",
            "--question", "What is X?",
            "--answer-type", "multiple_choice",
            "--user-answer", "A",
            "--correct-answer", "A"
        )
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions
        assert "Error" in output or "error" in output
        assert "Answer scoring failed" in output
        assert "Tool timeout" in output

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_scoring_output_structure(
        self, mock_agent_class, mock_context: CLIContext, mock_score_response_correct
    ) -> None:
        """TC-9: Verify Rich output structure."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.score_answer.return_value = mock_score_response_correct
        mock_agent_class.return_value = mock_agent_instance

        # Execute
        agent.score_answer(
            mock_context,
            "--question-id", "q_001",
            "--question", "What is a transformer?",
            "--answer-type", "multiple_choice",
            "--user-answer", "Option A",
            "--correct-answer", "Option A"
        )
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions for output structure
        assert "Scoring Result" in output
        assert "Question:" in output
        assert "User Answer:" in output
        assert "Correct Answer:" in output
        assert "Score:" in output or "score:" in output
        assert "Status:" in output or "CORRECT" in output
        assert "Explanation:" in output or "Explanation" in output

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_all_answer_types(
        self, mock_agent_class, mock_context, mock_score_response_correct
    ) -> None:
        """TC-10: Verify scoring for all answer types."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.score_answer.return_value = mock_score_response_correct
        mock_agent_class.return_value = mock_agent_instance

        answer_types = ["multiple_choice", "short_answer", "true_false"]

        for answer_type in answer_types:
            mock_context._buffer.truncate(0)
            mock_context._buffer.seek(0)

            agent.score_answer(
                mock_context,
                "--question-id", "q_001",
                "--question", "Test question?",
                "--answer-type", answer_type,
                "--user-answer", "Some answer",
                "--correct-answer", "Correct answer"
            )
            output = strip_ansi(mock_context._buffer.getvalue())

            assert "Scoring Complete" in output, f"Failed for type {answer_type}"
            assert "score: 100" in output, f"Score not shown for type {answer_type}"

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_with_context_parameter(
        self, mock_agent_class, mock_context: CLIContext, mock_score_response_correct
    ) -> None:
        """Verify scoring with optional context parameter."""
        # Setup mock
        mock_agent_instance = AsyncMock()
        mock_agent_instance.score_answer.return_value = mock_score_response_correct
        mock_agent_class.return_value = mock_agent_instance

        # Execute with context
        agent.score_answer(
            mock_context,
            "--question-id", "q_001",
            "--question", "What is X?",
            "--answer-type", "multiple_choice",
            "--user-answer", "A",
            "--correct-answer", "A",
            "--context", "Additional context for scoring"
        )
        output = strip_ansi(mock_context._buffer.getvalue())

        # Verify agent was called successfully (context parameter accepted)
        assert "Scoring Complete" in output
        call_args = mock_agent_instance.score_answer.call_args
        assert call_args is not None  # Verify agent was called

    @patch("src.cli.actions.agent.ItemGenAgent")
    def test_scoring_with_explanation_and_keywords(
        self, mock_agent_class, mock_context: CLIContext, mock_score_response_correct
    ) -> None:
        """Verify explanation and keywords are displayed."""
        # Setup mock with explanation and keywords
        response = ScoreAnswerResponse(
            item_id="q_001_test",
            score=100,
            correct=True,
            explanation="This is a detailed explanation.",
            keyword_matches=["keyword1", "keyword2"],
            feedback="Good",
            confidence=None,  # Confidence may be None
            graded_at="2025-11-11T12:00:00Z",
        )
        mock_agent_instance = AsyncMock()
        mock_agent_instance.score_answer.return_value = response
        mock_agent_class.return_value = mock_agent_instance

        # Execute
        agent.score_answer(
            mock_context,
            "--question-id", "q_001",
            "--question", "What is X?",
            "--answer-type", "multiple_choice",
            "--user-answer", "A",
            "--correct-answer", "A"
        )
        output = strip_ansi(mock_context._buffer.getvalue())

        # Assertions - check that explanation and keywords are displayed
        assert "Explanation:" in output
        assert "This is a detailed explanation" in output
        assert "Keywords Matched:" in output or "Keywords Matched" in output
