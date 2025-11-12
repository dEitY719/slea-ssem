"""
Tests for agent batch-score command (REQ-CLI-Agent-4).

Tests parallel batch scoring using Tool 6 with batch JSON file input.

REQ: REQ-CLI-Agent-4
"""

import json
import re
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console

from src.cli.actions.agent import batch_score
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


@pytest.fixture
def mock_score_response_correct() -> MagicMock:
    """Create mock correct score response."""
    response = MagicMock()
    response.correct = True
    response.score = 100
    response.explanation = "Correct answer provided."
    response.keyword_matches = ["key1", "key2"]
    response.confidence = 0.95
    return response


@pytest.fixture
def mock_score_response_partial() -> MagicMock:
    """Create mock partial score response."""
    response = MagicMock()
    response.correct = False
    response.score = 65
    response.explanation = "Partially correct with missing details."
    response.keyword_matches = ["key1"]
    response.confidence = 0.70
    return response


@pytest.fixture
def mock_score_response_incorrect() -> MagicMock:
    """Create mock incorrect score response."""
    response = MagicMock()
    response.correct = False
    response.score = 0
    response.explanation = "Incorrect answer."
    response.keyword_matches = []
    response.confidence = 0.10
    return response


class TestBatchScoreHelpAndErrors:
    """Tests for help and error handling."""

    def test_help_command(self, mock_context: CLIContext) -> None:
        """TC-1: Verify --help displays command usage."""
        batch_score(mock_context, "--help")

        output = mock_context._buffer.getvalue()
        assert "agent batch-score" in output
        assert "--batch-file" in output
        assert "--parallel" in output
        assert "--output" in output

    def test_missing_batch_file(self, mock_context: CLIContext) -> None:
        """TC-2: Verify error when --batch-file missing."""
        batch_score(mock_context)

        output = mock_context._buffer.getvalue()
        assert "Error" in output
        assert "--batch-file is required" in output

    def test_batch_file_not_found(self, mock_context: CLIContext) -> None:
        """TC-3: Verify error for non-existent file."""
        batch_score(mock_context, "--batch-file", "/nonexistent/path/batch.json")

        output = mock_context._buffer.getvalue()
        assert "Error" in output
        assert "not found" in output.lower()

    def test_invalid_json_format(self, mock_context: CLIContext) -> None:
        """TC-4: Verify error for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json")
            temp_file = f.name

        try:
            batch_score(mock_context, "--batch-file", temp_file)

            output = mock_context._buffer.getvalue()
            assert "Error" in output
            assert "Invalid JSON" in output or "invalid" in output.lower()
        finally:
            Path(temp_file).unlink()

    def test_empty_batch_array(self, mock_context: CLIContext) -> None:
        """TC-5: Verify error for empty batch."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            temp_file = f.name

        try:
            batch_score(mock_context, "--batch-file", temp_file)

            output = mock_context._buffer.getvalue()
            assert "Error" in output
            assert "empty" in output.lower()
        finally:
            Path(temp_file).unlink()

    def test_missing_required_fields(self, mock_context: CLIContext) -> None:
        """TC-6: Verify error for incomplete item."""
        batch_data = [
            {
                "question_id": "q_001",
                "question": "What is X?",
                # Missing: answer_type, user_answer, correct_answer
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(batch_data, f)
            temp_file = f.name

        try:
            batch_score(mock_context, "--batch-file", temp_file)

            output = mock_context._buffer.getvalue()
            assert "Error" in output
            assert "missing" in output.lower() or "required" in output.lower()
        finally:
            Path(temp_file).unlink()

    def test_invalid_answer_type(self, mock_context: CLIContext) -> None:
        """Test error for invalid answer_type."""
        batch_data = [
            {
                "question_id": "q_001",
                "question": "What is X?",
                "answer_type": "invalid_type",
                "user_answer": "My answer",
                "correct_answer": "Correct answer",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(batch_data, f)
            temp_file = f.name

        try:
            batch_score(mock_context, "--batch-file", temp_file)

            output = mock_context._buffer.getvalue()
            assert "Error" in output
            assert "invalid answer_type" in output.lower() or "must be one of" in output.lower()
        finally:
            Path(temp_file).unlink()

    def test_invalid_parallel_workers(self, mock_context: CLIContext) -> None:
        """Test error for invalid parallel worker count."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"question_id": "q1", "question": "Q", "answer_type": "true_false", "user_answer": "T", "correct_answer": "T"}], f)
            temp_file = f.name

        try:
            batch_score(mock_context, "--batch-file", temp_file, "--parallel", "15")

            output = mock_context._buffer.getvalue()
            assert "Error" in output
            assert "1-10" in output or "between" in output.lower()
        finally:
            Path(temp_file).unlink()

    def test_agent_initialization_failure(self, mock_context: CLIContext) -> None:
        """Test error when agent initialization fails."""
        batch_data = [
            {
                "question_id": "q_001",
                "question": "What is X?",
                "answer_type": "multiple_choice",
                "user_answer": "Option A",
                "correct_answer": "Option A",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(batch_data, f)
            temp_file = f.name

        try:
            with patch("src.cli.actions.agent.ItemGenAgent", side_effect=Exception("GEMINI_API_KEY not found")):
                batch_score(mock_context, "--batch-file", temp_file)

                output = mock_context._buffer.getvalue()
                assert "Error" in output
                assert "Agent initialization failed" in output
        finally:
            Path(temp_file).unlink()


class TestBatchScoreSuccess:
    """Tests for successful batch scoring."""

    def test_successful_batch_scoring(
        self,
        mock_context: CLIContext,
        mock_score_response_correct: MagicMock,
        mock_score_response_partial: MagicMock,
    ) -> None:
        """TC-7: Verify successful batch scoring with multiple items."""
        batch_data = [
            {
                "question_id": "q_001",
                "question": "Question 1?",
                "answer_type": "multiple_choice",
                "user_answer": "Option A",
                "correct_answer": "Option A",
            },
            {
                "question_id": "q_002",
                "question": "Question 2?",
                "answer_type": "short_answer",
                "user_answer": "My answer",
                "correct_answer": "Complete answer",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(batch_data, f)
            temp_file = f.name

        try:
            mock_agent = AsyncMock()
            mock_agent.score_answer = AsyncMock(
                side_effect=[mock_score_response_correct, mock_score_response_partial]
            )

            with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
                batch_score(mock_context, "--batch-file", temp_file)

                output = strip_ansi(mock_context._buffer.getvalue())
                assert "Batch Scoring Complete" in output
                assert "Total: 2 items" in output
                assert "Average Score:" in output
        finally:
            Path(temp_file).unlink()

    def test_partial_success_batch(
        self,
        mock_context: CLIContext,
        mock_score_response_correct: MagicMock,
        mock_score_response_incorrect: MagicMock,
    ) -> None:
        """TC-8: Verify handling of partial failures."""
        batch_data = [
            {
                "question_id": "q_001",
                "question": "Q1?",
                "answer_type": "true_false",
                "user_answer": "True",
                "correct_answer": "True",
            },
            {
                "question_id": "q_002",
                "question": "Q2?",
                "answer_type": "short_answer",
                "user_answer": "Wrong",
                "correct_answer": "Right",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(batch_data, f)
            temp_file = f.name

        try:
            mock_agent = AsyncMock()
            mock_agent.score_answer = AsyncMock(
                side_effect=[mock_score_response_correct, mock_score_response_incorrect]
            )

            with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
                batch_score(mock_context, "--batch-file", temp_file)

                output = strip_ansi(mock_context._buffer.getvalue())
                assert "Batch Scoring Complete" in output
                assert "Passed (100): 1" in output
                assert "Failed (0): 1" in output
        finally:
            Path(temp_file).unlink()

    def test_custom_parallel_workers(
        self,
        mock_context: CLIContext,
        mock_score_response_correct: MagicMock,
    ) -> None:
        """TC-9: Verify custom worker count."""
        batch_data = [
            {
                "question_id": "q_001",
                "question": "Q?",
                "answer_type": "multiple_choice",
                "user_answer": "A",
                "correct_answer": "A",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(batch_data, f)
            temp_file = f.name

        try:
            mock_agent = AsyncMock()
            mock_agent.score_answer = AsyncMock(return_value=mock_score_response_correct)

            with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
                batch_score(mock_context, "--batch-file", temp_file, "--parallel", "5")

                output = mock_context._buffer.getvalue()
                assert "Workers: 5" in output or "workers" in output.lower()
        finally:
            Path(temp_file).unlink()

    def test_output_file_export(
        self,
        mock_context: CLIContext,
        mock_score_response_correct: MagicMock,
    ) -> None:
        """TC-10: Verify results saved to file."""
        batch_data = [
            {
                "question_id": "q_001",
                "question": "Q?",
                "answer_type": "multiple_choice",
                "user_answer": "A",
                "correct_answer": "A",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(batch_data, f)
            batch_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            mock_agent = AsyncMock()
            mock_agent.score_answer = AsyncMock(return_value=mock_score_response_correct)

            with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
                batch_score(mock_context, "--batch-file", batch_file, "--output", output_file)

                output = mock_context._buffer.getvalue()
                assert "Results saved" in output or "saved to" in output.lower()

                # Verify output file is valid JSON
                with open(output_file) as f:
                    results = json.load(f)
                    assert "metadata" in results
                    assert "results" in results
                    assert results["metadata"]["total_items"] == 1
                    assert results["metadata"]["passed_count"] == 1
        finally:
            Path(batch_file).unlink()
            Path(output_file).unlink()

    def test_results_table_display(
        self,
        mock_context: CLIContext,
        mock_score_response_correct: MagicMock,
        mock_score_response_partial: MagicMock,
        mock_score_response_incorrect: MagicMock,
    ) -> None:
        """TC-11: Verify results table with all status types."""
        batch_data = [
            {
                "question_id": "q_001",
                "question": "Q1?",
                "answer_type": "multiple_choice",
                "user_answer": "A",
                "correct_answer": "A",
            },
            {
                "question_id": "q_002",
                "question": "Q2?",
                "answer_type": "short_answer",
                "user_answer": "Partial",
                "correct_answer": "Full answer",
            },
            {
                "question_id": "q_003",
                "question": "Q3?",
                "answer_type": "true_false",
                "user_answer": "False",
                "correct_answer": "True",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(batch_data, f)
            temp_file = f.name

        try:
            mock_agent = AsyncMock()
            mock_agent.score_answer = AsyncMock(
                side_effect=[
                    mock_score_response_correct,
                    mock_score_response_partial,
                    mock_score_response_incorrect,
                ]
            )

            with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
                batch_score(mock_context, "--batch-file", temp_file)

                output = mock_context._buffer.getvalue()
                # Check for table title
                assert "Batch Results" in output or "Batch Scoring Results" in output
                # Check for status indicators
                assert "✅" in output  # Correct
                assert "⚠️" in output or "WARNING" in output.upper()  # Partial
                assert "❌" in output  # Incorrect
        finally:
            Path(temp_file).unlink()

    def test_batch_ignores_optional_context(
        self,
        mock_context: CLIContext,
        mock_score_response_correct: MagicMock,
    ) -> None:
        """Test batch ignores optional context field."""
        batch_data = [
            {
                "question_id": "q_001",
                "question": "Q?",
                "answer_type": "short_answer",
                "user_answer": "Answer",
                "correct_answer": "Answer",
                "context": "Background context",  # This field is ignored
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(batch_data, f)
            temp_file = f.name

        try:
            mock_agent = AsyncMock()
            mock_agent.score_answer = AsyncMock(return_value=mock_score_response_correct)

            with patch("src.cli.actions.agent.ItemGenAgent", return_value=mock_agent):
                batch_score(mock_context, "--batch-file", temp_file)

                # Verify agent was called successfully
                call_args = mock_agent.score_answer.call_args
                assert call_args is not None
                request = call_args[0][0]
                # Verify request has required fields
                assert request.user_answer == "Answer"
                assert request.correct_answer == "Answer"
        finally:
            Path(temp_file).unlink()
