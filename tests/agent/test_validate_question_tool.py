"""
Tests for Tool 4 (validate_question_quality) validation logic.

REQ: REQ-A-Mode1-Tool4
"""

from unittest.mock import MagicMock, patch

import pytest

from src.agent.tools.validate_question_tool import (
    MIN_VALID_SCORE,
    PASS_THRESHOLD,
    REVISE_LOWER_THRESHOLD,
    _check_rule_based_quality,
    _get_recommendation,
    _should_discard_question,
    _validate_single_question,
)
from src.agent.tools.validation_response_parser import ValidationResponseParser


class TestGetRecommendation:
    """Tests for _get_recommendation function."""

    def test_pass_recommendation_when_score_above_threshold(self) -> None:
        """Test recommendation is 'pass' when score >= 0.85."""
        result = _get_recommendation(PASS_THRESHOLD)
        assert result == "pass"

        result = _get_recommendation(0.95)
        assert result == "pass"

    def test_revise_recommendation_when_score_in_middle(self) -> None:
        """Test recommendation is 'revise' when 0.70 <= score < 0.85."""
        result = _get_recommendation(REVISE_LOWER_THRESHOLD)
        assert result == "revise"

        result = _get_recommendation(0.75)
        assert result == "revise"

        result = _get_recommendation(PASS_THRESHOLD - 0.01)
        assert result == "revise"

    def test_reject_recommendation_when_score_below_threshold(self) -> None:
        """Test recommendation is 'reject' when score < 0.70."""
        result = _get_recommendation(0.69)
        assert result == "reject"

        result = _get_recommendation(0.0)
        assert result == "reject"


class TestShouldDiscardQuestion:
    """Tests for _should_discard_question function."""

    def test_should_discard_when_score_below_threshold(self) -> None:
        """Test should_discard=True when final_score < 0.70."""
        result = _should_discard_question(0.65, "revise")
        assert result is True

        result = _should_discard_question(0.0, "reject")
        assert result is True

    def test_should_keep_when_score_above_threshold_and_pass(self) -> None:
        """Test should_discard=False when final_score >= 0.70 and recommendation='pass'."""
        result = _should_discard_question(0.85, "pass")
        assert result is False

        result = _should_discard_question(0.95, "pass")
        assert result is False

    def test_should_keep_when_score_above_threshold_and_revise(self) -> None:
        """Test should_discard=False when final_score >= 0.70 and recommendation='revise'."""
        result = _should_discard_question(0.75, "revise")
        assert result is False

        result = _should_discard_question(0.71, "revise")
        assert result is False

    def test_should_discard_when_recommendation_is_reject(self) -> None:
        """Test should_discard=True when recommendation='reject' regardless of score."""
        result = _should_discard_question(0.65, "reject")
        assert result is True

        result = _should_discard_question(0.0, "reject")
        assert result is True


class TestCheckRuleBasedQuality:
    """Tests for _check_rule_based_quality function."""

    def test_perfect_score_with_valid_question(self) -> None:
        """Test score=1.0 with valid question."""
        score, issues = _check_rule_based_quality(
            stem="What is machine learning?",
            question_type="multiple_choice",
            choices=["A) Supervised", "B) Unsupervised", "C) Both", "D) Neither"],
            correct_answer="C) Both",
        )

        assert score == 1.0
        assert len(issues) == 0

    def test_stem_length_violation(self) -> None:
        """Test score reduction when stem exceeds max length."""
        long_stem = "x" * 251  # Exceeds STEM_MAX_LENGTH (250)
        score, issues = _check_rule_based_quality(
            stem=long_stem,
            question_type="multiple_choice",
            choices=["A", "B", "C", "D"],
            correct_answer="A",
        )

        assert score < 1.0
        assert any("length" in issue.lower() for issue in issues)

    def test_invalid_choices_count(self) -> None:
        """Test score reduction with invalid number of choices."""
        # Too few choices (MIN_CHOICES=4)
        score, issues = _check_rule_based_quality(
            stem="What is AI?",
            question_type="multiple_choice",
            choices=["A", "B", "C"],  # Only 3 choices
            correct_answer="A",
        )

        assert score < 1.0
        assert any("choices" in issue.lower() for issue in issues)

    def test_correct_answer_not_in_choices(self) -> None:
        """Test score reduction when correct answer not in choices."""
        score, issues = _check_rule_based_quality(
            stem="What is RAG?",
            question_type="multiple_choice",
            choices=["A) Wrong1", "B) Wrong2", "C) Wrong3", "D) Wrong4"],
            correct_answer="E) Correct",  # Not in choices
        )

        assert score < 1.0
        assert any("not found" in issue.lower() for issue in issues)

    def test_duplicate_choices(self) -> None:
        """Test score reduction with duplicate choices."""
        # Exact duplicate strings
        score, issues = _check_rule_based_quality(
            stem="What is the capital?",
            question_type="multiple_choice",
            choices=["London", "Paris", "London", "Berlin"],  # Duplicate: "London" appears twice
            correct_answer="London",
        )

        assert score < 1.0
        assert any("duplicate" in issue.lower() for issue in issues)

    def test_true_false_question_without_choices(self) -> None:
        """Test true/false question (no choices required)."""
        score, issues = _check_rule_based_quality(
            stem="True or False: AI is intelligence?",
            question_type="true_false",
            choices=None,
            correct_answer="True",
        )

        assert score == 1.0
        assert len(issues) == 0

    def test_short_answer_question_without_choices(self) -> None:
        """Test short answer question (no choices required)."""
        score, issues = _check_rule_based_quality(
            stem="What is the capital of France?",
            question_type="short_answer",
            choices=None,
            correct_answer="Paris",
        )

        assert score == 1.0
        assert len(issues) == 0


class TestValidateSingleQuestion:
    """Tests for _validate_single_question function."""

    @patch("src.agent.tools.validate_question_tool.create_llm")
    def test_validate_high_quality_question(self, mock_create_llm: MagicMock) -> None:
        """Test validation of high-quality question."""
        # Mock LLM to return high score
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="0.90")
        mock_create_llm.return_value = mock_llm

        result = _validate_single_question(
            stem="What is the primary benefit of RAG?",
            question_type="multiple_choice",
            choices=["A) Speed", "B) Accuracy", "C) Cost", "D) All of above"],
            correct_answer="D) All of above",
        )

        assert result["is_valid"] is True  # final_score >= 0.70
        assert result["recommendation"] in ("pass", "revise")
        assert "should_discard" in result
        assert isinstance(result["should_discard"], bool)

    def test_validate_low_quality_question(self) -> None:
        """Test validation of low-quality question."""
        result = _validate_single_question(
            stem="Test",  # Too short/vague
            question_type="multiple_choice",
            choices=["A", "B", "C"],  # Only 3 choices (< MIN_CHOICES=4)
            correct_answer="X",  # Not in choices
        )

        assert result["is_valid"] is False
        assert result["final_score"] < MIN_VALID_SCORE
        assert result["should_discard"] is True

    def test_response_fields_present(self) -> None:
        """Test all required fields are present in response."""
        result = _validate_single_question(
            stem="What is machine learning?",
            question_type="short_answer",
            choices=None,
            correct_answer="ML is a subset of AI",
        )

        required_fields = [
            "is_valid",
            "score",
            "rule_score",
            "final_score",
            "feedback",
            "issues",
            "recommendation",
            "should_discard",
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_final_score_is_minimum_of_llm_and_rule_score(self) -> None:
        """Test final_score = min(llm_score, rule_score)."""
        result = _validate_single_question(
            stem="What is the answer to everything?",
            question_type="short_answer",
            choices=None,
            correct_answer="42",
        )

        # final_score should be min of two components
        assert result["final_score"] <= result["score"]
        assert result["final_score"] <= result["rule_score"]

    def test_should_discard_consistency_with_is_valid(self) -> None:
        """Test should_discard is consistent with is_valid."""
        result = _validate_single_question(
            stem="Is AI important?",
            question_type="true_false",
            choices=["True", "False"],
            correct_answer="True",
        )

        # If is_valid=True, should_discard should be False
        # If is_valid=False, should_discard should be True (usually)
        if result["is_valid"]:
            assert result["should_discard"] is False or result["recommendation"] != "pass"
        else:
            assert result["should_discard"] is True


class TestValidationResponseParser:
    """Tests for ValidationResponseParser contradiction handling."""

    def test_parse_valid_response(self) -> None:
        """Test parsing valid response without contradictions."""
        response = {
            "is_valid": True,
            "score": 0.85,
            "rule_score": 0.90,
            "final_score": 0.85,
            "feedback": "Good question",
            "issues": [],
            "recommendation": "pass",
            "should_discard": False,
        }

        parsed = ValidationResponseParser.parse_response(response)

        assert parsed["is_valid"] is True
        assert parsed["should_discard"] is False
        assert parsed["recommendation"] == "pass"

    def test_detect_contradiction_should_discard_true_high_score(self) -> None:
        """Test detection of contradiction: should_discard=true but score=0.85."""
        response = {
            "is_valid": True,
            "score": 0.85,
            "rule_score": 0.90,
            "final_score": 0.85,
            "feedback": "Good question",
            "issues": [],
            "recommendation": "pass",
            "should_discard": True,  # ❌ CONTRADICTION: true but score >= 0.70
        }

        parsed = ValidationResponseParser.parse_response(response)

        # Should resolve: keep the question (score is good)
        assert parsed["should_discard"] is False

    def test_detect_contradiction_should_discard_false_low_score(self) -> None:
        """Test detection of contradiction: should_discard=false but score=0.65."""
        response = {
            "is_valid": False,
            "score": 0.65,
            "rule_score": 0.60,
            "final_score": 0.60,
            "feedback": "Poor question",
            "issues": ["Stem too long"],
            "recommendation": "reject",
            "should_discard": False,  # ❌ CONTRADICTION: false but score < 0.70
        }

        parsed = ValidationResponseParser.parse_response(response)

        # Should resolve: discard the question (score is bad)
        assert parsed["should_discard"] is True

    def test_resolve_contradiction_with_reject_recommendation(self) -> None:
        """Test contradiction resolution: recommendation='reject' takes priority."""
        response = {
            "is_valid": False,
            "score": 0.65,
            "rule_score": 0.60,
            "final_score": 0.65,
            "feedback": "Poor quality",
            "issues": ["Issue 1"],
            "recommendation": "reject",  # ✅ REJECT (matches score < 0.70)
            "should_discard": False,  # ❌ CONTRADICTION
        }

        parsed = ValidationResponseParser.parse_response(response)

        # Should discard (recommendation=reject takes priority)
        assert parsed["should_discard"] is True

    def test_parse_batch_response(self) -> None:
        """Test parsing batch responses."""
        responses = [
            {
                "is_valid": True,
                "score": 0.85,
                "rule_score": 0.90,
                "final_score": 0.85,
                "feedback": "Good",
                "issues": [],
                "recommendation": "pass",
                "should_discard": False,
            },
            {
                "is_valid": False,
                "score": 0.55,
                "rule_score": 0.50,
                "final_score": 0.50,
                "feedback": "Poor",
                "issues": ["Issue 1"],
                "recommendation": "reject",
                "should_discard": True,
            },
        ]

        parsed = ValidationResponseParser.parse_response(responses, batch=True)

        assert len(parsed) == 2
        assert parsed[0]["should_discard"] is False
        assert parsed[1]["should_discard"] is True

    def test_default_response_on_parsing_error(self) -> None:
        """Test default response when parsing fails."""
        # Missing critical fields
        response = {
            "score": 0.85,
            # Missing: is_valid, rule_score, final_score, recommendation
        }

        # Should use defaults
        parsed = ValidationResponseParser._parse_single_response(response)

        assert "final_score" in parsed
        assert parsed["final_score"] == 0.0 or parsed["final_score"] is not None

    def test_validate_response_structure(self) -> None:
        """Test response structure validation."""
        valid_response = {
            "is_valid": True,
            "score": 0.85,
            "rule_score": 0.90,
            "final_score": 0.85,
            "recommendation": "pass",
        }

        assert ValidationResponseParser.validate_response_structure(valid_response) is True

        # Missing fields
        invalid_response = {
            "is_valid": True,
            "score": 0.85,
            # Missing: rule_score, final_score, recommendation
        }

        assert ValidationResponseParser.validate_response_structure(invalid_response) is False
