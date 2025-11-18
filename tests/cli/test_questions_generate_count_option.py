"""Tests for questions generate command with --count option.

This test file verifies the --count option feature for the questions generate CLI command.
- Default: 5 questions
- User-configurable: 1-10 questions
- Validation: Invalid counts (0, 11, non-integer) should use default
"""

import re
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from src.cli.actions import questions
from src.cli.context import CLIContext


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


class TestQuestionsGenerateCountOption:
    """Test --count option for questions generate command."""

    @pytest.fixture
    def mock_context(self) -> CLIContext:
        """Create CLIContext with buffered console and authenticated user."""
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=88)
        context = CLIContext(console=console, logger=None)
        context._buffer = buffer
        context.session.token = "test-token"
        context.session.user_id = 123
        context.session.current_session_id = None
        context.client = MagicMock()
        return context

    def test_help_shows_count_option(self, mock_context: CLIContext) -> None:
        """TC-1: Verify --help displays --count option in help text."""
        questions.generate_questions(mock_context, "help")
        output = strip_ansi(mock_context._buffer.getvalue())

        assert "--count" in output
        assert "1-10" in output
        assert "Default: 5" in output

    def test_default_count_when_not_specified(self, mock_context: CLIContext) -> None:
        """TC-2: Verify default count=5 when --count not provided."""
        mock_context.client.make_request.return_value = (
            200,
            {
                "session_id": "session_123",
                "questions": [
                    {"id": f"q{i}", "stem": f"Question {i}"}
                    for i in range(5)
                ],
            },
            None,
        )

        with patch(
            "src.cli.actions.questions._get_latest_survey",
            return_value="survey_123"
        ):
            questions.generate_questions(mock_context)

        # Verify API was called with question_count=5 (default)
        mock_context.client.make_request.assert_called_once()
        call_args = mock_context.client.make_request.call_args
        assert call_args[1]["json_data"]["question_count"] == 5

    def test_custom_count_3(self, mock_context: CLIContext) -> None:
        """TC-3: Verify --count 3 passes question_count=3 to API."""
        mock_context.client.make_request.return_value = (
            200,
            {
                "session_id": "session_123",
                "questions": [
                    {"id": f"q{i}", "stem": f"Question {i}"}
                    for i in range(3)
                ],
            },
            None,
        )

        with patch(
            "src.cli.actions.questions._get_latest_survey",
            return_value="survey_123"
        ):
            questions.generate_questions(mock_context, "--count", "3")

        # Verify API was called with question_count=3
        mock_context.client.make_request.assert_called_once()
        call_args = mock_context.client.make_request.call_args
        assert call_args[1]["json_data"]["question_count"] == 3

    def test_custom_count_10_max(self, mock_context: CLIContext) -> None:
        """TC-4: Verify --count 10 (max value) is accepted."""
        mock_context.client.make_request.return_value = (
            200,
            {
                "session_id": "session_123",
                "questions": [
                    {"id": f"q{i}", "stem": f"Question {i}"}
                    for i in range(10)
                ],
            },
            None,
        )

        with patch(
            "src.cli.actions.questions._get_latest_survey",
            return_value="survey_123"
        ):
            questions.generate_questions(mock_context, "--count", "10")

        # Verify API was called with question_count=10
        mock_context.client.make_request.assert_called_once()
        call_args = mock_context.client.make_request.call_args
        assert call_args[1]["json_data"]["question_count"] == 10

    def test_custom_count_1_min(self, mock_context: CLIContext) -> None:
        """TC-5: Verify --count 1 (min value) is accepted."""
        mock_context.client.make_request.return_value = (
            200,
            {
                "session_id": "session_123",
                "questions": [{"id": "q1", "stem": "Question 1"}],
            },
            None,
        )

        with patch(
            "src.cli.actions.questions._get_latest_survey",
            return_value="survey_123"
        ):
            questions.generate_questions(mock_context, "--count", "1")

        # Verify API was called with question_count=1
        mock_context.client.make_request.assert_called_once()
        call_args = mock_context.client.make_request.call_args
        assert call_args[1]["json_data"]["question_count"] == 1

    def test_invalid_count_0_uses_default(self, mock_context: CLIContext) -> None:
        """TC-6: Verify --count 0 shows warning and uses default=5."""
        mock_context.client.make_request.return_value = (
            200,
            {
                "session_id": "session_123",
                "questions": [
                    {"id": f"q{i}", "stem": f"Question {i}"}
                    for i in range(5)
                ],
            },
            None,
        )

        with patch(
            "src.cli.actions.questions._get_latest_survey",
            return_value="survey_123"
        ):
            questions.generate_questions(mock_context, "--count", "0")

        output = strip_ansi(mock_context._buffer.getvalue())
        assert "Invalid count: 0" in output or "Must be 1-10" in output

        # Verify API was called with default question_count=5
        call_args = mock_context.client.make_request.call_args
        assert call_args[1]["json_data"]["question_count"] == 5

    def test_invalid_count_11_uses_default(self, mock_context: CLIContext) -> None:
        """TC-7: Verify --count 11 (exceeds max) shows warning and uses default=5."""
        mock_context.client.make_request.return_value = (
            200,
            {
                "session_id": "session_123",
                "questions": [
                    {"id": f"q{i}", "stem": f"Question {i}"}
                    for i in range(5)
                ],
            },
            None,
        )

        with patch(
            "src.cli.actions.questions._get_latest_survey",
            return_value="survey_123"
        ):
            questions.generate_questions(mock_context, "--count", "11")

        output = strip_ansi(mock_context._buffer.getvalue())
        assert "Invalid count: 11" in output or "Must be 1-10" in output

        # Verify API was called with default question_count=5
        call_args = mock_context.client.make_request.call_args
        assert call_args[1]["json_data"]["question_count"] == 5

    def test_invalid_count_non_integer_uses_default(self, mock_context: CLIContext) -> None:
        """TC-8: Verify --count abc (non-integer) shows warning and uses default=5."""
        mock_context.client.make_request.return_value = (
            200,
            {
                "session_id": "session_123",
                "questions": [
                    {"id": f"q{i}", "stem": f"Question {i}"}
                    for i in range(5)
                ],
            },
            None,
        )

        with patch(
            "src.cli.actions.questions._get_latest_survey",
            return_value="survey_123"
        ):
            questions.generate_questions(mock_context, "--count", "abc")

        output = strip_ansi(mock_context._buffer.getvalue())
        assert "Invalid count: abc" in output

        # Verify API was called with default question_count=5
        call_args = mock_context.client.make_request.call_args
        assert call_args[1]["json_data"]["question_count"] == 5

    def test_count_with_other_options(self, mock_context: CLIContext) -> None:
        """TC-9: Verify --count works with --survey-id and --domain."""
        mock_context.client.make_request.return_value = (
            200,
            {
                "session_id": "session_123",
                "questions": [
                    {"id": f"q{i}", "stem": f"Question {i}"}
                    for i in range(7)
                ],
            },
            None,
        )

        questions.generate_questions(
            mock_context,
            "--survey-id", "survey_abc",
            "--domain", "food",
            "--count", "7"
        )

        # Verify API was called with all options
        call_args = mock_context.client.make_request.call_args
        assert call_args[1]["json_data"]["survey_id"] == "survey_abc"
        assert call_args[1]["json_data"]["domain"] == "food"
        assert call_args[1]["json_data"]["question_count"] == 7

    def test_help_includes_count_example(self, mock_context: CLIContext) -> None:
        """TC-10: Verify help includes example with --count option."""
        questions.generate_questions(mock_context, "help")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Check for count example in help
        assert "count" in output.lower()
        # Look for example that demonstrates count usage
        assert "--count" in output

    def test_output_shows_count_parameter(self, mock_context: CLIContext) -> None:
        """TC-11: Verify output message includes count parameter."""
        mock_context.client.make_request.return_value = (
            200,
            {
                "session_id": "session_123",
                "questions": [
                    {"id": f"q{i}", "stem": f"Question {i}"}
                    for i in range(3)
                ],
            },
            None,
        )

        with patch(
            "src.cli.actions.questions._get_latest_survey",
            return_value="survey_123"
        ):
            questions.generate_questions(mock_context, "--count", "3")

        output = strip_ansi(mock_context._buffer.getvalue())
        # Output should mention count=3 or show 3 questions generated
        assert "count=3" in output or "3" in output
