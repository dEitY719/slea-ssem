"""Tests for Save Generated Question Tool (REQ-A-Mode1-Tool5).

REQ: REQ-A-Mode1-Tool5
Tests for save_generated_question() function that saves validated questions to database.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_multiple_choice_question() -> dict[str, Any]:
    """Generate a valid multiple choice question."""
    return {
        "item_type": "multiple_choice",
        "stem": "What is the main advantage of RAG in LLM applications?",
        "choices": [
            "Reduces computational cost",
            "Retrieves external knowledge for accurate responses",
            "Simplifies model training",
            "Increases model size",
        ],
        "correct_key": "Retrieves external knowledge for accurate responses",
        "correct_keywords": None,
        "difficulty": 7,
        "categories": ["LLM", "RAG"],
        "round_id": "sess_123_1_2025-11-09T10:30:00Z",
        "validation_score": 0.92,
        "explanation": "RAG (Retrieval-Augmented Generation) enhances LLM by combining retrieval with generation.",
    }


@pytest.fixture
def valid_true_false_question() -> dict[str, Any]:
    """Generate a valid true/false question."""
    return {
        "item_type": "true_false",
        "stem": "Transformers use attention mechanisms to process sequences in parallel.",
        "choices": ["True", "False"],
        "correct_key": "True",
        "correct_keywords": None,
        "difficulty": 6,
        "categories": ["LLM", "Transformer"],
        "round_id": "sess_123_1_2025-11-09T10:30:00Z",
        "validation_score": 0.88,
        "explanation": "Transformers' multi-head attention mechanism allows parallel processing.",
    }


@pytest.fixture
def valid_short_answer_question() -> dict[str, Any]:
    """Generate a valid short answer question."""
    return {
        "item_type": "short_answer",
        "stem": "Explain the concept of prompt engineering in LLM applications.",
        "choices": None,
        "correct_key": None,
        "correct_keywords": ["prompt", "input", "design", "LLM", "output"],
        "difficulty": 5,
        "categories": ["LLM", "Prompt Engineering"],
        "round_id": "sess_123_1_2025-11-09T10:30:00Z",
        "validation_score": 0.85,
        "explanation": "Prompt engineering is designing inputs to elicit desired outputs from LLMs.",
    }


@pytest.fixture
def mock_db() -> MagicMock:
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_question() -> MagicMock:
    """Create a mock Question instance."""
    question = MagicMock()
    question.id = "q_550e8400_e29b_41d4_a716_446655440000"
    question.session_id = "sess_123"
    question.item_type = "multiple_choice"
    question.stem = "What is RAG?"
    question.difficulty = 7
    question.category = "RAG"
    question.round = 1
    question.created_at = datetime.fromisoformat("2025-11-09T10:30:00+00:00")
    return question


# ============================================================================
# Input Validation Tests
# ============================================================================


class TestInputValidation:
    """Tests for input parameter validation."""

    def test_save_question_empty_stem(self) -> None:
        """Test validation fails with empty stem.

        REQ: REQ-A-Mode1-Tool5, AC1

        Given: Empty stem string
        When: save_generated_question() is called
        Then: Raises ValueError with descriptive message
        """
        from src.agent.tools.save_question_tool import _validate_save_question_inputs

        with pytest.raises(ValueError, match="stem cannot be empty"):
            _validate_save_question_inputs(
                item_type="multiple_choice",
                stem="",
                choices=["A", "B", "C", "D"],
                correct_key="A",
                correct_keywords=None,
                difficulty=5,
                categories=["LLM"],
                round_id="sess_123_1_2025-11-09T10:30:00Z",
            )

    def test_save_question_invalid_item_type(self) -> None:
        """Test validation fails with invalid item_type.

        REQ: REQ-A-Mode1-Tool5, AC1

        Given: Invalid item_type
        When: save_generated_question() is called
        Then: Raises ValueError with descriptive message
        """
        from src.agent.tools.save_question_tool import _validate_save_question_inputs

        with pytest.raises(ValueError, match="item_type must be"):
            _validate_save_question_inputs(
                item_type="invalid_type",
                stem="What is AI?",
                choices=["A", "B", "C", "D"],
                correct_key="A",
                correct_keywords=None,
                difficulty=5,
                categories=["LLM"],
                round_id="sess_123_1_2025-11-09T10:30:00Z",
            )

    def test_save_question_invalid_difficulty(self) -> None:
        """Test validation fails with invalid difficulty.

        REQ: REQ-A-Mode1-Tool5, AC1

        Given: Difficulty outside 1-10 range
        When: save_generated_question() is called
        Then: Raises ValueError with descriptive message
        """
        from src.agent.tools.save_question_tool import _validate_save_question_inputs

        with pytest.raises(ValueError, match="difficulty must be"):
            _validate_save_question_inputs(
                item_type="multiple_choice",
                stem="What is AI?",
                choices=["A", "B", "C", "D"],
                correct_key="A",
                correct_keywords=None,
                difficulty=15,  # Out of range
                categories=["LLM"],
                round_id="sess_123_1_2025-11-09T10:30:00Z",
            )

    def test_save_question_empty_categories(self) -> None:
        """Test validation fails with empty categories.

        REQ: REQ-A-Mode1-Tool5, AC1

        Given: Empty categories list
        When: save_generated_question() is called
        Then: Raises ValueError with descriptive message
        """
        from src.agent.tools.save_question_tool import _validate_save_question_inputs

        with pytest.raises(ValueError, match="categories cannot be empty"):
            _validate_save_question_inputs(
                item_type="multiple_choice",
                stem="What is AI?",
                choices=["A", "B", "C", "D"],
                correct_key="A",
                correct_keywords=None,
                difficulty=5,
                categories=[],  # Empty
                round_id="sess_123_1_2025-11-09T10:30:00Z",
            )

    def test_save_question_empty_round_id(self) -> None:
        """Test validation fails with empty round_id.

        REQ: REQ-A-Mode1-Tool5, AC1

        Given: Empty round_id string
        When: save_generated_question() is called
        Then: Raises ValueError with descriptive message
        """
        from src.agent.tools.save_question_tool import _validate_save_question_inputs

        with pytest.raises(ValueError, match="round_id cannot be empty"):
            _validate_save_question_inputs(
                item_type="multiple_choice",
                stem="What is AI?",
                choices=["A", "B", "C", "D"],
                correct_key="A",
                correct_keywords=None,
                difficulty=5,
                categories=["LLM"],
                round_id="",  # Empty
            )


# ============================================================================
# Answer Schema Validation Tests
# ============================================================================


class TestAnswerSchemaValidation:
    """Tests for answer schema construction."""

    def test_answer_schema_multiple_choice(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test answer schema for multiple choice.

        REQ: REQ-A-Mode1-Tool5, AC2

        Given: Multiple choice question with correct_key
        When: _build_answer_schema() is called
        Then: Returns schema with correct_key, validation_score, explanation
        """
        from src.agent.tools.save_question_tool import _build_answer_schema

        schema = _build_answer_schema(
            item_type=valid_multiple_choice_question["item_type"],
            correct_key=valid_multiple_choice_question["correct_key"],
            correct_keywords=valid_multiple_choice_question["correct_keywords"],
            validation_score=valid_multiple_choice_question["validation_score"],
            explanation=valid_multiple_choice_question["explanation"],
        )

        assert "correct_key" in schema
        assert schema["correct_key"] == valid_multiple_choice_question["correct_key"]
        assert "validation_score" in schema
        assert schema["validation_score"] == valid_multiple_choice_question["validation_score"]
        assert "explanation" in schema

    def test_answer_schema_short_answer(
        self, valid_short_answer_question: dict[str, Any]
    ) -> None:
        """Test answer schema for short answer.

        REQ: REQ-A-Mode1-Tool5, AC2

        Given: Short answer question with correct_keywords
        When: _build_answer_schema() is called
        Then: Returns schema with correct_keywords, validation_score
        """
        from src.agent.tools.save_question_tool import _build_answer_schema

        schema = _build_answer_schema(
            item_type=valid_short_answer_question["item_type"],
            correct_key=valid_short_answer_question["correct_key"],
            correct_keywords=valid_short_answer_question["correct_keywords"],
            validation_score=valid_short_answer_question["validation_score"],
            explanation=valid_short_answer_question["explanation"],
        )

        assert "correct_keywords" in schema
        assert set(schema["correct_keywords"]) == set(valid_short_answer_question["correct_keywords"])
        assert "validation_score" in schema


# ============================================================================
# Happy Path Tests (Database Saves)
# ============================================================================


class TestSaveQuestionHappyPath:
    """Tests for successful question saves."""

    def test_save_multiple_choice_question(
        self, valid_multiple_choice_question: dict[str, Any], mock_db: MagicMock
    ) -> None:
        """Test saving a multiple choice question.

        REQ: REQ-A-Mode1-Tool5, AC1 & AC3

        Given: Valid multiple choice question
        When: save_generated_question() is called
        Then: Returns dict with question_id, round_id, saved_at, success
        """
        from src.agent.tools.save_question_tool import _save_generated_question_impl

        with patch("src.agent.tools.save_question_tool.get_db", return_value=iter([mock_db])):
            # Mock add and commit
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

            # Mock the Question model
            with patch(
                "src.agent.tools.save_question_tool.Question"
            ) as mock_question_class:
                mock_instance = MagicMock()
                mock_instance.id = "q_test_001"
                mock_instance.created_at = datetime.fromisoformat(
                    "2025-11-09T10:30:00+00:00"
                )
                mock_question_class.return_value = mock_instance

                result = _save_generated_question_impl(
                    item_type=valid_multiple_choice_question["item_type"],
                    stem=valid_multiple_choice_question["stem"],
                    choices=valid_multiple_choice_question["choices"],
                    correct_key=valid_multiple_choice_question["correct_key"],
                    correct_keywords=valid_multiple_choice_question["correct_keywords"],
                    difficulty=valid_multiple_choice_question["difficulty"],
                    categories=valid_multiple_choice_question["categories"],
                    round_id=valid_multiple_choice_question["round_id"],
                    validation_score=valid_multiple_choice_question["validation_score"],
                    explanation=valid_multiple_choice_question["explanation"],
                )

        assert result is not None
        assert "question_id" in result
        assert result["success"] is True
        assert "saved_at" in result
        assert result["round_id"] == valid_multiple_choice_question["round_id"]

    def test_save_true_false_question(
        self, valid_true_false_question: dict[str, Any], mock_db: MagicMock
    ) -> None:
        """Test saving a true/false question.

        REQ: REQ-A-Mode1-Tool5, AC1

        Given: Valid true/false question
        When: save_generated_question() is called
        Then: Returns success dict with question_id
        """
        from src.agent.tools.save_question_tool import _save_generated_question_impl

        with patch("src.agent.tools.save_question_tool.get_db", return_value=iter([mock_db])):
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

            with patch(
                "src.agent.tools.save_question_tool.Question"
            ) as mock_question_class:
                mock_instance = MagicMock()
                mock_instance.id = "q_test_002"
                mock_instance.created_at = datetime.fromisoformat(
                    "2025-11-09T10:30:00+00:00"
                )
                mock_question_class.return_value = mock_instance

                result = _save_generated_question_impl(
                    item_type=valid_true_false_question["item_type"],
                    stem=valid_true_false_question["stem"],
                    choices=valid_true_false_question["choices"],
                    correct_key=valid_true_false_question["correct_key"],
                    correct_keywords=valid_true_false_question["correct_keywords"],
                    difficulty=valid_true_false_question["difficulty"],
                    categories=valid_true_false_question["categories"],
                    round_id=valid_true_false_question["round_id"],
                    validation_score=valid_true_false_question["validation_score"],
                    explanation=valid_true_false_question["explanation"],
                )

        assert result["success"] is True

    def test_save_short_answer_question(
        self, valid_short_answer_question: dict[str, Any], mock_db: MagicMock
    ) -> None:
        """Test saving a short answer question.

        REQ: REQ-A-Mode1-Tool5, AC1

        Given: Valid short answer question
        When: save_generated_question() is called
        Then: Returns success dict with question_id
        """
        from src.agent.tools.save_question_tool import _save_generated_question_impl

        with patch("src.agent.tools.save_question_tool.get_db", return_value=iter([mock_db])):
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

            with patch(
                "src.agent.tools.save_question_tool.Question"
            ) as mock_question_class:
                mock_instance = MagicMock()
                mock_instance.id = "q_test_003"
                mock_instance.created_at = datetime.fromisoformat(
                    "2025-11-09T10:30:00+00:00"
                )
                mock_question_class.return_value = mock_instance

                result = _save_generated_question_impl(
                    item_type=valid_short_answer_question["item_type"],
                    stem=valid_short_answer_question["stem"],
                    choices=valid_short_answer_question["choices"],
                    correct_key=valid_short_answer_question["correct_key"],
                    correct_keywords=valid_short_answer_question["correct_keywords"],
                    difficulty=valid_short_answer_question["difficulty"],
                    categories=valid_short_answer_question["categories"],
                    round_id=valid_short_answer_question["round_id"],
                    validation_score=valid_short_answer_question["validation_score"],
                    explanation=valid_short_answer_question["explanation"],
                )

        assert result["success"] is True


# ============================================================================
# Response Structure Tests
# ============================================================================


class TestResponseStructure:
    """Tests for response structure and field presence."""

    def test_save_response_has_required_fields(
        self, valid_multiple_choice_question: dict[str, Any], mock_db: MagicMock
    ) -> None:
        """Test that response has all required fields.

        REQ: REQ-A-Mode1-Tool5, AC3

        Given: Valid question
        When: save_generated_question() is called
        Then: Response contains question_id, round_id, saved_at, success
        """
        from src.agent.tools.save_question_tool import _save_generated_question_impl

        with patch("src.agent.tools.save_question_tool.get_db", return_value=iter([mock_db])):
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

            with patch(
                "src.agent.tools.save_question_tool.Question"
            ) as mock_question_class:
                mock_instance = MagicMock()
                mock_instance.id = "q_test_001"
                mock_instance.created_at = datetime.fromisoformat(
                    "2025-11-09T10:30:00+00:00"
                )
                mock_question_class.return_value = mock_instance

                result = _save_generated_question_impl(
                    item_type=valid_multiple_choice_question["item_type"],
                    stem=valid_multiple_choice_question["stem"],
                    choices=valid_multiple_choice_question["choices"],
                    correct_key=valid_multiple_choice_question["correct_key"],
                    correct_keywords=valid_multiple_choice_question["correct_keywords"],
                    difficulty=valid_multiple_choice_question["difficulty"],
                    categories=valid_multiple_choice_question["categories"],
                    round_id=valid_multiple_choice_question["round_id"],
                    validation_score=valid_multiple_choice_question["validation_score"],
                    explanation=valid_multiple_choice_question["explanation"],
                )

        # Check required fields
        required_fields = ["question_id", "round_id", "saved_at", "success"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Check field types
        assert isinstance(result["question_id"], str)
        assert isinstance(result["round_id"], str)
        assert isinstance(result["saved_at"], str)
        assert isinstance(result["success"], bool)

    def test_save_response_round_id_matches_input(
        self, valid_multiple_choice_question: dict[str, Any], mock_db: MagicMock
    ) -> None:
        """Test that returned round_id matches input round_id.

        REQ: REQ-A-Mode1-Tool5, AC3

        Given: Input with specific round_id
        When: save_generated_question() is called
        Then: Response round_id equals input round_id
        """
        from src.agent.tools.save_question_tool import _save_generated_question_impl

        input_round_id = "sess_test_1_2025-11-09T10:30:00Z"

        with patch("src.agent.tools.save_question_tool.get_db", return_value=iter([mock_db])):
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

            with patch(
                "src.agent.tools.save_question_tool.Question"
            ) as mock_question_class:
                mock_instance = MagicMock()
                mock_instance.id = "q_test_001"
                mock_instance.created_at = datetime.fromisoformat(
                    "2025-11-09T10:30:00+00:00"
                )
                mock_question_class.return_value = mock_instance

                result = _save_generated_question_impl(
                    item_type=valid_multiple_choice_question["item_type"],
                    stem=valid_multiple_choice_question["stem"],
                    choices=valid_multiple_choice_question["choices"],
                    correct_key=valid_multiple_choice_question["correct_key"],
                    correct_keywords=valid_multiple_choice_question["correct_keywords"],
                    difficulty=valid_multiple_choice_question["difficulty"],
                    categories=valid_multiple_choice_question["categories"],
                    round_id=input_round_id,
                    validation_score=valid_multiple_choice_question["validation_score"],
                    explanation=valid_multiple_choice_question["explanation"],
                )

        assert result["round_id"] == input_round_id


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling and recovery."""

    def test_database_error_fallback_to_queue(
        self, valid_multiple_choice_question: dict[str, Any], mock_db: MagicMock
    ) -> None:
        """Test graceful handling when database save fails.

        REQ: REQ-A-Mode1-Tool5, AC4

        Given: Database commit raises error
        When: save_generated_question() is called
        Then: Question added to memory queue, returns success=False initially
        """
        from src.agent.tools.save_question_tool import _save_generated_question_impl

        with patch("src.agent.tools.save_question_tool.get_db", return_value=iter([mock_db])):
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock(side_effect=Exception("Database connection error"))
            mock_db.rollback = MagicMock()

            with patch(
                "src.agent.tools.save_question_tool.Question"
            ) as mock_question_class:
                mock_instance = MagicMock()
                mock_instance.id = "q_test_001"
                mock_instance.created_at = datetime.fromisoformat(
                    "2025-11-09T10:30:00+00:00"
                )
                mock_question_class.return_value = mock_instance

                result = _save_generated_question_impl(
                    item_type=valid_multiple_choice_question["item_type"],
                    stem=valid_multiple_choice_question["stem"],
                    choices=valid_multiple_choice_question["choices"],
                    correct_key=valid_multiple_choice_question["correct_key"],
                    correct_keywords=valid_multiple_choice_question["correct_keywords"],
                    difficulty=valid_multiple_choice_question["difficulty"],
                    categories=valid_multiple_choice_question["categories"],
                    round_id=valid_multiple_choice_question["round_id"],
                    validation_score=valid_multiple_choice_question["validation_score"],
                    explanation=valid_multiple_choice_question["explanation"],
                )

        # Should still return a result with success=False
        assert result is not None
        assert "success" in result


# ============================================================================
# Metadata Storage Tests
# ============================================================================


class TestMetadataStorage:
    """Tests for metadata storage in answer_schema."""

    def test_validation_score_stored(
        self, valid_multiple_choice_question: dict[str, Any], mock_db: MagicMock
    ) -> None:
        """Test that validation_score is stored in answer_schema.

        REQ: REQ-A-Mode1-Tool5, AC2

        Given: Question with validation_score
        When: save_generated_question() is called
        Then: validation_score stored in answer_schema
        """
        from src.agent.tools.save_question_tool import _save_generated_question_impl

        with patch("src.agent.tools.save_question_tool.get_db", return_value=iter([mock_db])):
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

            with patch(
                "src.agent.tools.save_question_tool.Question"
            ) as mock_question_class:
                mock_instance = MagicMock()
                mock_instance.id = "q_test_001"
                mock_instance.created_at = datetime.fromisoformat(
                    "2025-11-09T10:30:00+00:00"
                )
                mock_question_class.return_value = mock_instance

                _save_generated_question_impl(
                    item_type=valid_multiple_choice_question["item_type"],
                    stem=valid_multiple_choice_question["stem"],
                    choices=valid_multiple_choice_question["choices"],
                    correct_key=valid_multiple_choice_question["correct_key"],
                    correct_keywords=valid_multiple_choice_question["correct_keywords"],
                    difficulty=valid_multiple_choice_question["difficulty"],
                    categories=valid_multiple_choice_question["categories"],
                    round_id=valid_multiple_choice_question["round_id"],
                    validation_score=valid_multiple_choice_question["validation_score"],
                    explanation=valid_multiple_choice_question["explanation"],
                )

                # Verify Question was called with correct answer_schema
                call_kwargs = mock_question_class.call_args[1]
                answer_schema = call_kwargs["answer_schema"]
                assert "validation_score" in answer_schema
                assert answer_schema["validation_score"] == valid_multiple_choice_question["validation_score"]

    def test_explanation_stored(
        self, valid_short_answer_question: dict[str, Any], mock_db: MagicMock
    ) -> None:
        """Test that explanation is stored in answer_schema.

        REQ: REQ-A-Mode1-Tool5, AC2

        Given: Question with explanation
        When: save_generated_question() is called
        Then: Explanation stored in answer_schema
        """
        from src.agent.tools.save_question_tool import _save_generated_question_impl

        with patch("src.agent.tools.save_question_tool.get_db", return_value=iter([mock_db])):
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

            with patch(
                "src.agent.tools.save_question_tool.Question"
            ) as mock_question_class:
                mock_instance = MagicMock()
                mock_instance.id = "q_test_003"
                mock_instance.created_at = datetime.fromisoformat(
                    "2025-11-09T10:30:00+00:00"
                )
                mock_question_class.return_value = mock_instance

                _save_generated_question_impl(
                    item_type=valid_short_answer_question["item_type"],
                    stem=valid_short_answer_question["stem"],
                    choices=valid_short_answer_question["choices"],
                    correct_key=valid_short_answer_question["correct_key"],
                    correct_keywords=valid_short_answer_question["correct_keywords"],
                    difficulty=valid_short_answer_question["difficulty"],
                    categories=valid_short_answer_question["categories"],
                    round_id=valid_short_answer_question["round_id"],
                    validation_score=valid_short_answer_question["validation_score"],
                    explanation=valid_short_answer_question["explanation"],
                )

                # Verify explanation stored
                call_kwargs = mock_question_class.call_args[1]
                answer_schema = call_kwargs["answer_schema"]
                assert "explanation" in answer_schema
