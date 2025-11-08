"""Tests for Validate Question Quality Tool (REQ-A-Mode1-Tool4).

REQ: REQ-A-Mode1-Tool4
Tests for validate_question_quality() function that validates generated questions.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_multiple_choice_question() -> dict[str, Any]:
    """Generate a valid multiple choice question."""
    return {
        "stem": "What is the main advantage of using RAG in LLM applications?",
        "question_type": "multiple_choice",
        "choices": [
            "Reduces computational cost",
            "Retrieves external knowledge for accurate responses",
            "Simplifies model training",
            "Increases model size",
        ],
        "correct_answer": "Retrieves external knowledge for accurate responses",
    }


@pytest.fixture
def valid_true_false_question() -> dict[str, Any]:
    """Generate a valid true/false question."""
    return {
        "stem": "Transformers use attention mechanisms to process sequences in parallel.",
        "question_type": "true_false",
        "choices": ["True", "False"],
        "correct_answer": "True",
    }


@pytest.fixture
def valid_short_answer_question() -> dict[str, Any]:
    """Generate a valid short answer question."""
    return {
        "stem": "Explain the concept of prompt engineering in LLM applications.",
        "question_type": "short_answer",
        "choices": None,
        "correct_answer": "Designing inputs to get desired outputs from LLM",
    }


@pytest.fixture
def invalid_long_stem_question() -> dict[str, Any]:
    """Generate a question with stem that exceeds length limit."""
    long_stem = "What is " + "the meaning of life? " * 20  # Over 250 chars
    return {
        "stem": long_stem,
        "question_type": "multiple_choice",
        "choices": ["A", "B", "C", "D"],
        "correct_answer": "A",
    }


@pytest.fixture
def invalid_few_choices_question() -> dict[str, Any]:
    """Generate a multiple choice question with too few choices."""
    return {
        "stem": "What is RAG?",
        "question_type": "multiple_choice",
        "choices": ["A", "B"],  # Only 2 choices, need 4-5
        "correct_answer": "A",
    }


@pytest.fixture
def invalid_many_choices_question() -> dict[str, Any]:
    """Generate a multiple choice question with too many choices."""
    return {
        "stem": "What is RAG?",
        "question_type": "multiple_choice",
        "choices": ["A", "B", "C", "D", "E", "F"],  # 6 choices, should be 4-5
        "correct_answer": "A",
    }


@pytest.fixture
def invalid_answer_not_in_choices() -> dict[str, Any]:
    """Generate a multiple choice with answer not in choices."""
    return {
        "stem": "What is RAG?",
        "question_type": "multiple_choice",
        "choices": ["A", "B", "C", "D"],
        "correct_answer": "Z",  # Not in choices
    }


@pytest.fixture
def batch_questions() -> list[dict[str, Any]]:
    """Generate a batch of 5 questions for batch validation."""
    return [
        {
            "stem": "What is machine learning?",
            "question_type": "short_answer",
            "choices": None,
            "correct_answer": "A subset of AI",
        },
        {
            "stem": "Neural networks are inspired by biological neurons.",
            "question_type": "true_false",
            "choices": ["True", "False"],
            "correct_answer": "True",
        },
        {
            "stem": "What is the primary purpose of regularization in ML?",
            "question_type": "multiple_choice",
            "choices": [
                "To reduce overfitting",
                "To increase training speed",
                "To simplify code",
                "To use more memory",
            ],
            "correct_answer": "To reduce overfitting",
        },
        {
            "stem": "What are hyperparameters?",
            "question_type": "short_answer",
            "choices": None,
            "correct_answer": "Parameters set before training",
        },
        {
            "stem": "Cross-validation helps prevent overfitting.",
            "question_type": "true_false",
            "choices": ["True", "False"],
            "correct_answer": "True",
        },
    ]


# ============================================================================
# Input Validation Tests
# ============================================================================


class TestInputValidation:
    """Tests for input parameter validation."""

    def test_validate_question_empty_stem(self) -> None:
        """Test validation fails with empty stem.

        REQ: REQ-A-Mode1-Tool4, AC1

        Given: Empty stem string
        When: validate_question_quality() is called
        Then: Raises ValueError with descriptive message
        """
        from src.agent.tools.validate_question_tool import _validate_question_inputs

        with pytest.raises(ValueError, match="stem cannot be empty"):
            _validate_question_inputs(
                stem="",
                question_type="multiple_choice",
                choices=["A", "B", "C", "D"],
                correct_answer="A",
            )

    def test_validate_question_invalid_question_type(self) -> None:
        """Test validation fails with invalid question type.

        REQ: REQ-A-Mode1-Tool4, AC1

        Given: Invalid question_type
        When: validate_question_quality() is called
        Then: Raises ValueError with descriptive message
        """
        from src.agent.tools.validate_question_tool import _validate_question_inputs

        with pytest.raises(ValueError, match="question_type must be"):
            _validate_question_inputs(
                stem="What is AI?",
                question_type="invalid_type",
                choices=["A", "B", "C", "D"],
                correct_answer="A",
            )

    def test_validate_question_missing_choices_for_multiple_choice(self) -> None:
        """Test validation fails when choices missing for multiple_choice.

        REQ: REQ-A-Mode1-Tool4, AC1

        Given: multiple_choice type but no choices provided
        When: validate_question_quality() is called
        Then: Raises ValueError with descriptive message
        """
        from src.agent.tools.validate_question_tool import _validate_question_inputs

        with pytest.raises(ValueError, match="choices required"):
            _validate_question_inputs(
                stem="What is AI?",
                question_type="multiple_choice",
                choices=None,
                correct_answer="A",
            )

    def test_validate_question_missing_correct_answer(self) -> None:
        """Test validation fails when correct_answer is missing.

        REQ: REQ-A-Mode1-Tool4, AC1

        Given: No correct_answer provided
        When: validate_question_quality() is called
        Then: Raises ValueError with descriptive message
        """
        from src.agent.tools.validate_question_tool import _validate_question_inputs

        with pytest.raises(ValueError, match="correct_answer cannot be empty"):
            _validate_question_inputs(
                stem="What is AI?",
                question_type="short_answer",
                choices=None,
                correct_answer="",
            )


# ============================================================================
# Rule-Based Validation Tests
# ============================================================================


class TestRuleBasedValidation:
    """Tests for rule-based quality checks."""

    def test_rule_validation_stem_length_valid(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test that valid stem length passes rule check.

        REQ: REQ-A-Mode1-Tool4, AC2

        Given: stem <= 250 chars
        When: _check_rule_based_quality() is called
        Then: Returns score > 0 and no length issue in issues list
        """
        from src.agent.tools.validate_question_tool import _check_rule_based_quality

        score, issues = _check_rule_based_quality(
            stem=valid_multiple_choice_question["stem"],
            question_type=valid_multiple_choice_question["question_type"],
            choices=valid_multiple_choice_question["choices"],
            correct_answer=valid_multiple_choice_question["correct_answer"],
        )

        assert score > 0
        assert not any("length" in issue.lower() for issue in issues)

    def test_rule_validation_stem_length_invalid(
        self, invalid_long_stem_question: dict[str, Any]
    ) -> None:
        """Test that long stem fails rule check.

        REQ: REQ-A-Mode1-Tool4, AC2

        Given: stem > 250 chars
        When: _check_rule_based_quality() is called
        Then: Returns lower score and includes length issue
        """
        from src.agent.tools.validate_question_tool import _check_rule_based_quality

        score, issues = _check_rule_based_quality(
            stem=invalid_long_stem_question["stem"],
            question_type=invalid_long_stem_question["question_type"],
            choices=invalid_long_stem_question["choices"],
            correct_answer=invalid_long_stem_question["correct_answer"],
        )

        assert score < 1.0
        assert any("length" in issue.lower() for issue in issues)

    def test_rule_validation_choices_count_valid(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test that valid choice count passes rule check.

        REQ: REQ-A-Mode1-Tool4, AC2

        Given: multiple_choice with 4 choices
        When: _check_rule_based_quality() is called
        Then: Returns score > 0 and no choice count issue
        """
        from src.agent.tools.validate_question_tool import _check_rule_based_quality

        score, issues = _check_rule_based_quality(
            stem=valid_multiple_choice_question["stem"],
            question_type="multiple_choice",
            choices=valid_multiple_choice_question["choices"],
            correct_answer=valid_multiple_choice_question["correct_answer"],
        )

        assert score > 0
        assert not any("choice" in issue.lower() for issue in issues)

    def test_rule_validation_choices_count_too_few(
        self, invalid_few_choices_question: dict[str, Any]
    ) -> None:
        """Test that too few choices fails rule check.

        REQ: REQ-A-Mode1-Tool4, AC2

        Given: multiple_choice with only 2 choices
        When: _check_rule_based_quality() is called
        Then: Returns lower score and includes choice count issue
        """
        from src.agent.tools.validate_question_tool import _check_rule_based_quality

        score, issues = _check_rule_based_quality(
            stem=invalid_few_choices_question["stem"],
            question_type="multiple_choice",
            choices=invalid_few_choices_question["choices"],
            correct_answer=invalid_few_choices_question["correct_answer"],
        )

        assert score < 1.0
        assert any("choice" in issue.lower() for issue in issues)

    def test_rule_validation_choices_count_too_many(
        self, invalid_many_choices_question: dict[str, Any]
    ) -> None:
        """Test that too many choices fails rule check.

        REQ: REQ-A-Mode1-Tool4, AC2

        Given: multiple_choice with 6 choices
        When: _check_rule_based_quality() is called
        Then: Returns lower score and includes choice count issue
        """
        from src.agent.tools.validate_question_tool import _check_rule_based_quality

        score, issues = _check_rule_based_quality(
            stem=invalid_many_choices_question["stem"],
            question_type="multiple_choice",
            choices=invalid_many_choices_question["choices"],
            correct_answer=invalid_many_choices_question["correct_answer"],
        )

        assert score < 1.0
        assert any("choice" in issue.lower() for issue in issues)

    def test_rule_validation_answer_not_in_choices(
        self, invalid_answer_not_in_choices: dict[str, Any]
    ) -> None:
        """Test that answer not in choices fails rule check.

        REQ: REQ-A-Mode1-Tool4, AC2

        Given: correct_answer not in choices list
        When: _check_rule_based_quality() is called
        Then: Returns lower score and includes answer validity issue
        """
        from src.agent.tools.validate_question_tool import _check_rule_based_quality

        score, issues = _check_rule_based_quality(
            stem=invalid_answer_not_in_choices["stem"],
            question_type="multiple_choice",
            choices=invalid_answer_not_in_choices["choices"],
            correct_answer=invalid_answer_not_in_choices["correct_answer"],
        )

        assert score < 1.0
        assert any("answer" in issue.lower() or "valid" in issue.lower() for issue in issues)


# ============================================================================
# Happy Path Tests (Single Validation)
# ============================================================================


class TestSingleValidationHappyPath:
    """Tests for successful single question validation."""

    def test_validate_multiple_choice_high_quality(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test validation of high-quality multiple choice question.

        REQ: REQ-A-Mode1-Tool4, AC1 & AC3

        Given: Valid multiple choice question with correct format
        When: validate_question_quality() is called
        Then: Returns dict with is_valid=True and recommendation="pass"
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.92  # High LLM score

            result = _validate_question_quality_impl(
                stem=valid_multiple_choice_question["stem"],
                question_type=valid_multiple_choice_question["question_type"],
                choices=valid_multiple_choice_question["choices"],
                correct_answer=valid_multiple_choice_question["correct_answer"],
            )

        assert result["is_valid"] is True
        assert result["score"] == 0.92
        assert result["final_score"] >= 0.85
        assert result["recommendation"] == "pass"
        assert result["feedback"] is not None
        assert isinstance(result["issues"], list)

    def test_validate_true_false_high_quality(
        self, valid_true_false_question: dict[str, Any]
    ) -> None:
        """Test validation of high-quality true/false question.

        REQ: REQ-A-Mode1-Tool4, AC1 & AC3

        Given: Valid true/false question
        When: validate_question_quality() is called
        Then: Returns dict with is_valid=True and recommendation="pass"
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.88

            result = _validate_question_quality_impl(
                stem=valid_true_false_question["stem"],
                question_type=valid_true_false_question["question_type"],
                choices=valid_true_false_question["choices"],
                correct_answer=valid_true_false_question["correct_answer"],
            )

        assert result["is_valid"] is True
        assert result["recommendation"] == "pass"

    def test_validate_short_answer_high_quality(
        self, valid_short_answer_question: dict[str, Any]
    ) -> None:
        """Test validation of high-quality short answer question.

        REQ: REQ-A-Mode1-Tool4, AC1 & AC3

        Given: Valid short answer question
        When: validate_question_quality() is called
        Then: Returns dict with is_valid=True and recommendation="pass"
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.90

            result = _validate_question_quality_impl(
                stem=valid_short_answer_question["stem"],
                question_type=valid_short_answer_question["question_type"],
                choices=valid_short_answer_question["choices"],
                correct_answer=valid_short_answer_question["correct_answer"],
            )

        assert result["is_valid"] is True
        assert result["recommendation"] == "pass"


# ============================================================================
# Recommendation Logic Tests
# ============================================================================


class TestRecommendationLogic:
    """Tests for recommendation logic (pass/revise/reject)."""

    def test_recommendation_pass_high_score(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test recommendation is 'pass' when final_score >= 0.85.

        REQ: REQ-A-Mode1-Tool4, AC3

        Given: final_score = 0.87
        When: validate_question_quality() is called
        Then: recommendation = "pass"
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.87

            result = _validate_question_quality_impl(
                stem=valid_multiple_choice_question["stem"],
                question_type=valid_multiple_choice_question["question_type"],
                choices=valid_multiple_choice_question["choices"],
                correct_answer=valid_multiple_choice_question["correct_answer"],
            )

        assert result["final_score"] >= 0.85
        assert result["recommendation"] == "pass"

    def test_recommendation_revise_medium_score(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test recommendation is 'revise' when 0.70 <= final_score < 0.85.

        REQ: REQ-A-Mode1-Tool4, AC3

        Given: final_score = 0.78
        When: validate_question_quality() is called
        Then: recommendation = "revise"
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.78

            result = _validate_question_quality_impl(
                stem=valid_multiple_choice_question["stem"],
                question_type=valid_multiple_choice_question["question_type"],
                choices=valid_multiple_choice_question["choices"],
                correct_answer=valid_multiple_choice_question["correct_answer"],
            )

        assert 0.70 <= result["final_score"] < 0.85
        assert result["recommendation"] == "revise"

    def test_recommendation_reject_low_score(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test recommendation is 'reject' when final_score < 0.70.

        REQ: REQ-A-Mode1-Tool4, AC3

        Given: final_score = 0.65
        When: validate_question_quality() is called
        Then: recommendation = "reject", is_valid = False
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.65

            result = _validate_question_quality_impl(
                stem=valid_multiple_choice_question["stem"],
                question_type=valid_multiple_choice_question["question_type"],
                choices=valid_multiple_choice_question["choices"],
                correct_answer=valid_multiple_choice_question["correct_answer"],
            )

        assert result["final_score"] < 0.70
        assert result["recommendation"] == "reject"
        assert result["is_valid"] is False


# ============================================================================
# Batch Validation Tests
# ============================================================================


class TestBatchValidation:
    """Tests for batch question validation."""

    def test_batch_validation_returns_list(
        self, batch_questions: list[dict[str, Any]]
    ) -> None:
        """Test that batch validation returns list of results.

        REQ: REQ-A-Mode1-Tool4, AC4

        Given: 5 questions for batch validation
        When: validate_question_quality() is called with batch=True
        Then: Returns list with 5 validation results
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.88

            results = _validate_question_quality_impl(
                stem=[q["stem"] for q in batch_questions],
                question_type=[q["question_type"] for q in batch_questions],
                choices=[q.get("choices") for q in batch_questions],
                correct_answer=[q["correct_answer"] for q in batch_questions],
                batch=True,
            )

        assert isinstance(results, list)
        assert len(results) == 5
        assert all(isinstance(r, dict) for r in results)

    def test_batch_validation_each_result_valid(
        self, batch_questions: list[dict[str, Any]]
    ) -> None:
        """Test that each batch result has required fields.

        REQ: REQ-A-Mode1-Tool4, AC4

        Given: Batch of questions
        When: validate_question_quality() is called with batch=True
        Then: Each result contains is_valid, score, rule_score, final_score, recommendation
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.85

            results = _validate_question_quality_impl(
                stem=[q["stem"] for q in batch_questions],
                question_type=[q["question_type"] for q in batch_questions],
                choices=[q.get("choices") for q in batch_questions],
                correct_answer=[q["correct_answer"] for q in batch_questions],
                batch=True,
            )

        for result in results:
            assert "is_valid" in result
            assert "score" in result
            assert "rule_score" in result
            assert "final_score" in result
            assert "recommendation" in result
            assert "feedback" in result
            assert "issues" in result


# ============================================================================
# Edge Cases & Error Handling Tests
# ============================================================================


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    def test_validate_question_with_special_characters(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test validation of question with special characters.

        REQ: REQ-A-Mode1-Tool4

        Given: stem contains special characters (quotes, unicode, etc.)
        When: validate_question_quality() is called
        Then: Validates successfully without errors
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        stem_with_special = 'What is "RAG"? (Retrieval-Augmented Generation) - 생성형 AI?'

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.88

            result = _validate_question_quality_impl(
                stem=stem_with_special,
                question_type="short_answer",
                choices=None,
                correct_answer="A method to enhance LLM responses",
            )

        assert result is not None
        assert "is_valid" in result

    def test_validate_question_llm_call_fails(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test graceful handling when LLM call fails.

        REQ: REQ-A-Mode1-Tool4

        Given: LLM service returns error
        When: validate_question_quality() is called
        Then: Uses default score (0.5) and continues validation
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch("src.agent.tools.validate_question_tool.create_llm") as mock_create_llm:
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.side_effect = Exception("LLM service unavailable")
            mock_create_llm.return_value = mock_llm_instance

            result = _validate_question_quality_impl(
                stem=valid_multiple_choice_question["stem"],
                question_type=valid_multiple_choice_question["question_type"],
                choices=valid_multiple_choice_question["choices"],
                correct_answer=valid_multiple_choice_question["correct_answer"],
            )

        assert result is not None
        assert "is_valid" in result
        # Should use default score
        assert result["score"] == 0.5  # Default fallback score


# ============================================================================
# Response Structure Tests
# ============================================================================


class TestResponseStructure:
    """Tests for response structure and field presence."""

    def test_single_validation_response_structure(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test that single validation response has all required fields.

        REQ: REQ-A-Mode1-Tool4, AC1

        Given: Valid question
        When: validate_question_quality() is called (single)
        Then: Response contains all required fields
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.88

            result = _validate_question_quality_impl(
                stem=valid_multiple_choice_question["stem"],
                question_type=valid_multiple_choice_question["question_type"],
                choices=valid_multiple_choice_question["choices"],
                correct_answer=valid_multiple_choice_question["correct_answer"],
            )

        # Verify all required fields
        required_fields = [
            "is_valid",
            "score",
            "rule_score",
            "final_score",
            "feedback",
            "issues",
            "recommendation",
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Verify field types
        assert isinstance(result["is_valid"], bool)
        assert isinstance(result["score"], (int, float))
        assert isinstance(result["rule_score"], (int, float))
        assert isinstance(result["final_score"], (int, float))
        assert isinstance(result["feedback"], str)
        assert isinstance(result["issues"], list)
        assert result["recommendation"] in ["pass", "revise", "reject"]

    def test_score_values_in_valid_range(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test that all scores are in 0-1 range.

        REQ: REQ-A-Mode1-Tool4

        Given: Valid question
        When: validate_question_quality() is called
        Then: All scores in [0.0, 1.0]
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.88

            result = _validate_question_quality_impl(
                stem=valid_multiple_choice_question["stem"],
                question_type=valid_multiple_choice_question["question_type"],
                choices=valid_multiple_choice_question["choices"],
                correct_answer=valid_multiple_choice_question["correct_answer"],
            )

        assert 0.0 <= result["score"] <= 1.0
        assert 0.0 <= result["rule_score"] <= 1.0
        assert 0.0 <= result["final_score"] <= 1.0

    def test_final_score_is_minimum(
        self, valid_multiple_choice_question: dict[str, Any]
    ) -> None:
        """Test that final_score = min(score, rule_score).

        REQ: REQ-A-Mode1-Tool4, AC2

        Given: LLM score and rule score
        When: validate_question_quality() is called
        Then: final_score = min(LLM_score, rule_score)
        """
        from src.agent.tools.validate_question_tool import _validate_question_quality_impl

        with patch(
            "src.agent.tools.validate_question_tool._call_llm_validation"
        ) as mock_llm:
            mock_llm.return_value = 0.75  # LLM score

            result = _validate_question_quality_impl(
                stem=valid_multiple_choice_question["stem"],
                question_type=valid_multiple_choice_question["question_type"],
                choices=valid_multiple_choice_question["choices"],
                correct_answer=valid_multiple_choice_question["correct_answer"],
            )

        # final_score should be min of LLM and rule scores
        expected_final = min(result["score"], result["rule_score"])
        assert result["final_score"] == expected_final
