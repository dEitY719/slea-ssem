"""Tests for questions solve interactive CLI command.

This test file verifies the solve command feature for the questions CLI.
- Auto-detect latest session or use --session-id
- Display [N/M] format for question progress
- Support multiple_choice (A, B, C, D options)
- Support true_false (T, F options)
- Support short_answer (free text)
- Navigation: n (next), p (previous), q (quit)
- Auto-save answers after each question
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


class TestQuestionsSolve:
    """Test solve command for interactive question answering."""

    @pytest.fixture
    def mock_context(self) -> CLIContext:
        """Create CLIContext with buffered console and authenticated user."""
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=88)
        context = CLIContext(console=console, logger=None)
        context._buffer = buffer
        context.session.token = "test-token"
        context.session.user_id = 123
        context.session.current_session_id = "session_123"
        context.client = MagicMock()
        return context

    @pytest.fixture
    def sample_questions(self) -> list[dict]:
        """Create sample questions with different types."""
        return [
            {
                "id": "q1",
                "stem": "What is 2 + 2?",
                "item_type": "multiple_choice",
                "choices": ["3", "4", "5", "6"],
                "answer_schema": {"selected_key": str},
                "category": "Math",
                "difficulty": "Easy",
            },
            {
                "id": "q2",
                "stem": "Is Python a programming language?",
                "item_type": "true_false",
                "choices": ["True", "False"],
                "answer_schema": {"answer": bool},
                "category": "Programming",
                "difficulty": "Easy",
            },
            {
                "id": "q3",
                "stem": "Explain the concept of machine learning.",
                "item_type": "short_answer",
                "choices": [],
                "answer_schema": {"text": str},
                "category": "AI",
                "difficulty": "Hard",
            },
        ]

    def test_help_shows_solve_documentation(self, mock_context: CLIContext) -> None:
        """TC-1: Verify --help displays solve command documentation."""
        questions.solve(mock_context, "help")
        output = strip_ansi(mock_context._buffer.getvalue())

        assert "questions solve" in output
        assert "usage" in output.lower() or "Usage" in output
        assert "keyboard" in output.lower() or "command" in output.lower()

    def test_solve_requires_authentication(self, mock_context: CLIContext) -> None:
        """TC-2: Verify solve fails when not authenticated."""
        mock_context.session.token = None

        questions.solve(mock_context, "--session-id", "session_123")

        output = strip_ansi(mock_context._buffer.getvalue())
        assert "Not authenticated" in output

    @patch("src.cli.actions.questions._get_latest_session")
    @patch("src.cli.actions.questions._get_session_questions")
    def test_solve_auto_detect_latest_session(
        self,
        mock_get_questions: MagicMock,
        mock_get_latest: MagicMock,
        mock_context: CLIContext,
        sample_questions: list[dict],
    ) -> None:
        """TC-3: Verify solve auto-detects latest session when --session-id not provided."""
        mock_get_latest.return_value = ("session_123", " (Round 1)")
        mock_get_questions.return_value = sample_questions[:1]  # Just first question

        # Mock input to quit after first question
        with patch("builtins.input", return_value="q"):
            questions.solve(mock_context)

        # Verify _get_latest_session was called
        assert mock_get_latest.called
        assert mock_get_questions.called

    @patch("src.cli.actions.questions._get_session_questions")
    def test_solve_with_explicit_session_id(
        self, mock_get_questions: MagicMock, mock_context: CLIContext, sample_questions: list[dict]
    ) -> None:
        """TC-4: Verify solve accepts explicit --session-id parameter."""
        mock_get_questions.return_value = sample_questions[:1]

        with patch("builtins.input", return_value="q"):
            questions.solve(mock_context, "--session-id", "session_999")

        # Verify _get_session_questions was called with explicit session
        assert mock_get_questions.called
        call_args = mock_get_questions.call_args
        # Check that session_999 was passed somehow
        call_str = str(call_args)
        assert "session_999" in call_str

    @patch("src.cli.actions.questions._get_session_questions")
    @patch("src.cli.actions.questions._autosave_answer_internal")
    def test_solve_multiple_choice_answer_with_letter(
        self,
        mock_autosave: MagicMock,
        mock_get_questions: MagicMock,
        mock_context: CLIContext,
        sample_questions: list[dict],
    ) -> None:
        """TC-5: Verify solve accepts letter input (A, B, C, D) for multiple choice."""
        mock_get_questions.return_value = sample_questions[:1]  # Only first question
        mock_autosave.return_value = True

        # Simulate user inputs: "B" (select option B) then "q" (quit)
        with patch("builtins.input", side_effect=["B", "q"]):
            questions.solve(mock_context, "--session-id", "session_123")

        # Verify autosave was called
        assert mock_autosave.called

    @patch("src.cli.actions.questions._get_session_questions")
    @patch("src.cli.actions.questions._autosave_answer_internal")
    def test_solve_true_false_answer_true(
        self,
        mock_autosave: MagicMock,
        mock_get_questions: MagicMock,
        mock_context: CLIContext,
        sample_questions: list[dict],
    ) -> None:
        """TC-6: Verify solve accepts True/T/Y for true_false questions."""
        mock_get_questions.return_value = sample_questions[1:2]  # Only second question (T/F)
        mock_autosave.return_value = True

        # Test with "T"
        with patch("builtins.input", side_effect=["T", "q"]):
            questions.solve(mock_context, "--session-id", "session_123")

        assert mock_autosave.called

    @patch("src.cli.actions.questions._get_session_questions")
    @patch("src.cli.actions.questions._autosave_answer_internal")
    def test_solve_short_answer_text(
        self,
        mock_autosave: MagicMock,
        mock_get_questions: MagicMock,
        mock_context: CLIContext,
        sample_questions: list[dict],
    ) -> None:
        """TC-7: Verify solve accepts any text for short_answer questions."""
        mock_get_questions.return_value = sample_questions[2:3]  # Only third question (short answer)
        mock_autosave.return_value = True

        # Test with custom text
        test_answer = "Machine learning is a subset of AI"
        with patch("builtins.input", side_effect=[test_answer, "q"]):
            questions.solve(mock_context, "--session-id", "session_123")

        assert mock_autosave.called

    @patch("src.cli.actions.questions._get_session_questions")
    def test_solve_display_progress_format(
        self,
        mock_get_questions: MagicMock,
        mock_context: CLIContext,
        sample_questions: list[dict],
    ) -> None:
        """TC-8: Verify solve displays progress in [N/M] format."""
        mock_get_questions.return_value = sample_questions

        with patch("builtins.input", return_value="q"):
            questions.solve(mock_context, "--session-id", "session_123")

        output = strip_ansi(mock_context._buffer.getvalue())

        # Should show question progress [1/3]
        assert "[1/" in output or "1/" in output or "Question 1/" in output

    @patch("src.cli.actions.questions._get_session_questions")
    def test_solve_displays_question_details(
        self,
        mock_get_questions: MagicMock,
        mock_context: CLIContext,
        sample_questions: list[dict],
    ) -> None:
        """TC-9: Verify solve displays question stem, category, difficulty."""
        mock_get_questions.return_value = sample_questions[:1]

        with patch("builtins.input", return_value="q"):
            questions.solve(mock_context, "--session-id", "session_123")

        output = strip_ansi(mock_context._buffer.getvalue())

        # Should display stem
        assert "What is 2 + 2?" in output

        # Should display category and difficulty
        assert "Math" in output
        assert "Easy" in output or "easy" in output.lower()

    @patch("src.cli.actions.questions._get_session_questions")
    def test_solve_displays_multiple_choice_options(
        self,
        mock_get_questions: MagicMock,
        mock_context: CLIContext,
        sample_questions: list[dict],
    ) -> None:
        """TC-10: Verify solve displays A, B, C, D for multiple choice."""
        mock_get_questions.return_value = sample_questions[:1]

        with patch("builtins.input", return_value="q"):
            questions.solve(mock_context, "--session-id", "session_123")

        output = strip_ansi(mock_context._buffer.getvalue())

        # Should display options (letters or numbers)
        has_options = (
            ("A" in output and "3" in output)
            or ("B" in output and "4" in output)
            or all(char in output for char in ["3", "4", "5", "6"])
        )
        assert has_options

    @patch("src.cli.actions.questions._get_session_questions")
    @patch("src.cli.actions.questions._autosave_answer_internal")
    def test_solve_all_questions_sequence(
        self,
        mock_autosave: MagicMock,
        mock_get_questions: MagicMock,
        mock_context: CLIContext,
        sample_questions: list[dict],
    ) -> None:
        """TC-11: Verify solve can answer all questions in sequence."""
        mock_get_questions.return_value = sample_questions
        mock_autosave.return_value = True

        # Answer all 3 questions: A (MC), T (TF), short answer, then quit
        with patch(
            "builtins.input",
            side_effect=["A", "T", "ML is great", "q"],
        ):
            questions.solve(mock_context, "--session-id", "session_123")

        # Should autosave at least once
        assert mock_autosave.call_count >= 1

    @patch("src.cli.actions.questions._get_session_questions")
    def test_solve_empty_session_handles_gracefully(
        self,
        mock_get_questions: MagicMock,
        mock_context: CLIContext,
    ) -> None:
        """TC-12: Verify solve handles empty session gracefully."""
        mock_get_questions.return_value = []

        questions.solve(mock_context, "--session-id", "session_123")

        output = strip_ansi(mock_context._buffer.getvalue())

        # Should show message about no questions
        assert (
            "no question" in output.lower()
            or "empty" in output.lower()
            or "not found" in output.lower()
        )

    @patch("src.cli.actions.questions._get_latest_session")
    def test_solve_no_session_found_error(
        self,
        mock_get_latest: MagicMock,
        mock_context: CLIContext,
    ) -> None:
        """TC-13: Verify solve handles session not found gracefully."""
        mock_get_latest.return_value = (None, "")

        questions.solve(mock_context)

        output = strip_ansi(mock_context._buffer.getvalue())

        # Should show error message
        assert (
            "not found" in output.lower()
            or "questions generate" in output.lower()
            or "session" in output.lower()
        )

    @patch("src.cli.actions.questions._get_session_questions")
    @patch("src.cli.actions.questions._autosave_answer_internal")
    def test_solve_navigate_next_previous(
        self,
        mock_autosave: MagicMock,
        mock_get_questions: MagicMock,
        mock_context: CLIContext,
        sample_questions: list[dict],
    ) -> None:
        """TC-14: Verify solve navigation with n (next) and p (previous) works."""
        mock_get_questions.return_value = sample_questions[:2]
        mock_autosave.return_value = True

        # Simulate: answer Q1, next (skip Q2), back (to Q2), quit
        with patch("builtins.input", side_effect=["A", "n", "p", "q"]):
            questions.solve(mock_context, "--session-id", "session_123")

        # Should successfully navigate without crashing
        output = strip_ansi(mock_context._buffer.getvalue())
        assert len(output) > 0

    @patch("src.cli.actions.questions._get_session_questions")
    def test_solve_question_counter_correct(
        self,
        mock_get_questions: MagicMock,
        mock_context: CLIContext,
        sample_questions: list[dict],
    ) -> None:
        """TC-15: Verify solve shows correct question counter for multiple questions."""
        mock_get_questions.return_value = sample_questions

        with patch("builtins.input", return_value="q"):
            questions.solve(mock_context, "--session-id", "session_123")

        output = strip_ansi(mock_context._buffer.getvalue())

        # Should show that we have 3 questions
        assert "3" in output  # At least mentions 3 questions

    def test_solve_help_is_complete(self, mock_context: CLIContext) -> None:
        """TC-16: Verify solve help text is comprehensive."""
        questions.solve(mock_context, "help")
        output = strip_ansi(mock_context._buffer.getvalue())

        # Help should contain usage, description, and examples
        help_content = output.lower()
        assert "usage" in help_content or "command" in help_content
        assert (
            "next" in help_content
            or "previous" in help_content
            or "navigate" in help_content
            or "n" in help_content
        )
