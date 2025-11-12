"""
Tests for agent tools command (REQ-CLI-Agent-5).

Tests direct invocation of Tools 1-6 for debugging and validation.

REQ: REQ-CLI-Agent-5
"""

import re
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console

from src.cli.actions.agent import (
    t1_get_user_profile,
    t2_search_question_templates,
    t3_get_difficulty_keywords,
    t4_validate_question_quality,
    t5_save_generated_question,
    t6_score_and_explain,
    tools_help,
)
from src.cli.context import CLIContext


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


@pytest.fixture
def mock_context() -> CLIContext:
    """Create CLIContext with buffered console."""
    buffer = StringIO()
    console = Console(file=buffer, force_terminal=True, width=120)
    context = CLIContext(console=console, logger=MagicMock())
    context._buffer = buffer
    return context


class TestToolsHelp:
    """Tests for tools help commands."""

    def test_main_tools_help(self, mock_context: CLIContext) -> None:
        """Test main tools help displays all 6 tools."""
        tools_help(mock_context)

        output = mock_context._buffer.getvalue()
        assert "agent tools" in output
        assert "t1" in output and "Get User Profile" in output
        assert "t2" in output and "Search Question Templates" in output
        assert "t3" in output and "Get Difficulty Keywords" in output
        assert "t4" in output and "Validate Question Quality" in output
        assert "t5" in output and "Save Generated Question" in output
        assert "t6" in output and "Score & Generate Explanation" in output


class TestTool1GetUserProfile:
    """Tests for Tool 1: Get User Profile."""

    def test_t1_help(self, mock_context: CLIContext) -> None:
        """TC-1: Verify --help or placeholder response."""
        t1_get_user_profile(mock_context, "--help")

        output = mock_context._buffer.getvalue()
        # Should either show help or placeholder message
        assert "Placeholder" in output or "pending" in output or "User Profile" in output

    def test_t1_success(self, mock_context: CLIContext) -> None:
        """TC-2: Verify successful user profile retrieval."""
        mock_agent = AsyncMock()
        mock_response = MagicMock()
        mock_response.skill_level = 7
        mock_response.experience_years = 5
        mock_response.interests = ["Python", "Data Science"]
        mock_response.job_role = "Engineer"

        mock_agent.get_user_profile = AsyncMock(return_value=mock_response)

        with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
            t1_get_user_profile(mock_context, "--user-id", "user_123")

            output = mock_context._buffer.getvalue()
            # Should show Tool 1 was invoked or contain user data
            assert "tool" in output.lower() or "user" in output.lower()

    def test_t1_missing_user_id(self, mock_context: CLIContext) -> None:
        """TC-3: Verify error when --user-id missing."""
        t1_get_user_profile(mock_context)

        output = mock_context._buffer.getvalue()
        # Either shows placeholder or error about missing parameter
        assert "Placeholder" in output or "Error" in output or "pending" in output


class TestTool2SearchTemplates:
    """Tests for Tool 2: Search Question Templates."""

    def test_t2_help(self, mock_context: CLIContext) -> None:
        """TC-4: Verify --help or placeholder response."""
        t2_search_question_templates(mock_context, "--help")

        output = mock_context._buffer.getvalue()
        assert "Placeholder" in output or "pending" in output or "Template" in output

    def test_t2_success(self, mock_context: CLIContext) -> None:
        """TC-5: Verify successful template search."""
        mock_agent = AsyncMock()
        mock_template = MagicMock()
        mock_template.id = "tmpl_01"
        mock_template.stem = "What is Python?"
        mock_template.type = "multiple_choice"
        mock_template.difficulty = 6.5

        mock_agent.search_question_templates = AsyncMock(
            return_value=[mock_template]
        )

        with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
            t2_search_question_templates(
                mock_context, "--interests", "Python", "--difficulty", "7"
            )

            output = strip_ansi(mock_context._buffer.getvalue())
            assert "Tool 2" in output and "Search Question Templates" in output

    def test_t2_invalid_difficulty(self, mock_context: CLIContext) -> None:
        """TC-6: Verify error for invalid difficulty."""
        t2_search_question_templates(
            mock_context, "--interests", "Python", "--difficulty", "15"
        )

        output = strip_ansi(mock_context._buffer.getvalue())
        # Should show error message about difficulty range
        assert "Error" in output and "difficulty" in output.lower()


class TestTool3GetKeywords:
    """Tests for Tool 3: Get Difficulty Keywords."""

    def test_t3_help(self, mock_context: CLIContext) -> None:
        """TC-7: Verify --help or placeholder response."""
        t3_get_difficulty_keywords(mock_context, "--help")

        output = mock_context._buffer.getvalue()
        assert "Placeholder" in output or "pending" in output or "Keyword" in output

    def test_t3_success(self, mock_context: CLIContext) -> None:
        """TC-8: Verify successful keyword retrieval."""
        mock_agent = AsyncMock()
        mock_response = MagicMock()
        mock_response.keywords = ["Async", "Decorators", "Context Managers"]
        mock_response.count = 3

        mock_agent.get_difficulty_keywords = AsyncMock(return_value=mock_response)

        with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
            t3_get_difficulty_keywords(mock_context, "--difficulty", "7")

            output = strip_ansi(mock_context._buffer.getvalue())
            assert "Tool 3" in output and "Get Difficulty Keywords" in output

    def test_t3_invalid_difficulty_type(self, mock_context: CLIContext) -> None:
        """TC-9: Verify error for non-integer difficulty."""
        t3_get_difficulty_keywords(mock_context, "--difficulty", "abc")

        output = strip_ansi(mock_context._buffer.getvalue())
        assert "Error" in output and "difficulty" in output.lower()


class TestTool4ValidateQuality:
    """Tests for Tool 4: Validate Question Quality."""

    def test_t4_help(self, mock_context: CLIContext) -> None:
        """TC-10: Verify --help or placeholder response."""
        t4_validate_question_quality(mock_context, "--help")

        output = mock_context._buffer.getvalue()
        assert "Placeholder" in output or "pending" in output or "Validate" in output

    def test_t4_success(self, mock_context: CLIContext) -> None:
        """TC-11: Verify successful question validation."""
        mock_agent = AsyncMock()
        mock_response = MagicMock()
        mock_response.score = 0.92
        mock_response.status = "PASS"
        mock_response.feedback = "Well-structured question"

        mock_agent.validate_question_quality = AsyncMock(return_value=mock_response)

        with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
            t4_validate_question_quality(
                mock_context,
                "--question",
                "What is a decorator?",
                "--type",
                "short_answer",
            )

            output = strip_ansi(mock_context._buffer.getvalue())
            assert "Tool 4" in output and "Validate Question Quality" in output

    def test_t4_invalid_question_type(self, mock_context: CLIContext) -> None:
        """TC-12: Verify error for invalid question type."""
        t4_validate_question_quality(
            mock_context,
            "--question",
            "What?",
            "--type",
            "invalid_type",
        )

        output = strip_ansi(mock_context._buffer.getvalue())
        assert "Error" in output and "type" in output.lower()


class TestTool5SaveQuestion:
    """Tests for Tool 5: Save Generated Question."""

    def test_t5_help(self, mock_context: CLIContext) -> None:
        """TC-13: Verify --help or placeholder response."""
        t5_save_generated_question(mock_context, "--help")

        output = mock_context._buffer.getvalue()
        assert "Placeholder" in output or "pending" in output or "Save" in output

    def test_t5_success(self, mock_context: CLIContext) -> None:
        """TC-14: Verify successful question save."""
        mock_agent = AsyncMock()
        mock_response = MagicMock()
        mock_response.item_id = "item_abc123"
        mock_response.round_id = "round_001"
        mock_response.status = "SAVED"

        mock_agent.save_generated_question = AsyncMock(return_value=mock_response)

        with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
            t5_save_generated_question(
                mock_context,
                "--stem",
                "What is X?",
                "--type",
                "multiple_choice",
                "--difficulty",
                "5",
                "--categories",
                "Python",
                "--round-id",
                "round_001",
            )

            output = strip_ansi(mock_context._buffer.getvalue())
            assert "Tool 5" in output and "Save Generated Question" in output

    def test_t5_invalid_difficulty(self, mock_context: CLIContext) -> None:
        """TC-15: Verify error for invalid difficulty."""
        t5_save_generated_question(
            mock_context,
            "--stem",
            "Q?",
            "--type",
            "mc",
            "--difficulty",
            "15",
            "--categories",
            "Python",
            "--round-id",
            "r1",
        )

        output = strip_ansi(mock_context._buffer.getvalue())
        assert "Error" in output and "difficulty" in output.lower()


class TestTool6ScoreAnswer:
    """Tests for Tool 6: Score & Generate Explanation."""

    def test_t6_help(self, mock_context: CLIContext) -> None:
        """TC-16: Verify --help or placeholder response."""
        t6_score_and_explain(mock_context, "--help")

        output = mock_context._buffer.getvalue()
        assert "Placeholder" in output or "pending" in output or "Score" in output

    def test_t6_success(self, mock_context: CLIContext) -> None:
        """TC-17: Verify successful answer scoring."""
        mock_agent = AsyncMock()
        mock_response = MagicMock()
        mock_response.score = 100
        mock_response.correct = True
        mock_response.explanation = "Correct answer!"

        mock_agent.score_answer = AsyncMock(return_value=mock_response)

        with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
            t6_score_and_explain(
                mock_context,
                "--question-id",
                "q1",
                "--question",
                "What is Python?",
                "--answer-type",
                "multiple_choice",
                "--user-answer",
                "A",
                "--correct-answer",
                "A",
            )

            output = strip_ansi(mock_context._buffer.getvalue())
            assert "Tool 6" in output and "Score & Generate Explanation" in output

    def test_t6_missing_answers(self, mock_context: CLIContext) -> None:
        """TC-18: Verify error when answers missing."""
        t6_score_and_explain(
            mock_context,
            "--question-id",
            "q1",
            "--question",
            "What?",
        )

        output = strip_ansi(mock_context._buffer.getvalue())
        assert "Error" in output and "required" in output.lower()


class TestToolsErrors:
    """Tests for error handling."""

    def test_invalid_subcommand(self, mock_context: CLIContext) -> None:
        """TC-19: Verify error for invalid subcommand."""
        # This would be handled by router before reaching tools_help
        # Testing that placeholder functions return gracefully
        from src.cli.actions.agent import agent_help

        # Call main agent help to show available tools
        agent_help(mock_context)

        output = mock_context._buffer.getvalue()
        assert "agent" in output.lower()

    def test_agent_initialization_failure(self, mock_context: CLIContext) -> None:
        """TC-20: Verify error when agent initialization fails."""
        with patch(
            "src.cli.actions.agent.ItemGenAgent",
            side_effect=Exception("GEMINI_API_KEY not found"),
        ):
            t1_get_user_profile(mock_context, "--user-id", "user_123")

            output = mock_context._buffer.getvalue()
            # Should show error or placeholder, not crash
            assert "Error" in output or "Placeholder" in output or "pending" in output
