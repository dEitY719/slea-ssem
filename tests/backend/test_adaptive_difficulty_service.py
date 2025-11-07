"""
Tests for adaptive difficulty service.

REQ: REQ-B-B2-Adapt-2, REQ-B-B2-Adapt-3
"""

import pytest
from sqlalchemy.orm import Session

from src.backend.models.test_result import TestResult
from src.backend.models.test_session import TestSession
from src.backend.services.adaptive_difficulty_service import AdaptiveDifficultyService


class TestDifficultyTierMapping:
    """REQ-B-B2-Adapt-2: Difficulty tier mapping based on score."""

    def test_score_0_to_40_is_low_tier(self, db_session: Session) -> None:
        """Score 0-40% → low tier (decrease difficulty)."""
        service = AdaptiveDifficultyService(db_session)

        assert service.get_difficulty_tier(0.0) == "low"
        assert service.get_difficulty_tier(20.0) == "low"
        assert service.get_difficulty_tier(39.9) == "low"

    def test_score_40_to_70_is_medium_tier(self, db_session: Session) -> None:
        """Score 40-70% → medium tier (maintain or slight increase)."""
        service = AdaptiveDifficultyService(db_session)

        assert service.get_difficulty_tier(40.0) == "medium"
        assert service.get_difficulty_tier(55.0) == "medium"
        assert service.get_difficulty_tier(69.9) == "medium"

    def test_score_70_plus_is_high_tier(self, db_session: Session) -> None:
        """Score 70%+ → high tier (increase difficulty)."""
        service = AdaptiveDifficultyService(db_session)

        assert service.get_difficulty_tier(70.0) == "high"
        assert service.get_difficulty_tier(85.0) == "high"
        assert service.get_difficulty_tier(100.0) == "high"

    def test_invalid_score_below_zero_raises_error(self, db_session: Session) -> None:
        """Invalid score below 0% raises ValueError."""
        service = AdaptiveDifficultyService(db_session)

        with pytest.raises(ValueError, match="Invalid score"):
            service.get_difficulty_tier(-1.0)

    def test_invalid_score_above_100_raises_error(self, db_session: Session) -> None:
        """Invalid score above 100% raises ValueError."""
        service = AdaptiveDifficultyService(db_session)

        with pytest.raises(ValueError, match="Invalid score"):
            service.get_difficulty_tier(101.0)


class TestDifficultyAdjustment:
    """REQ-B-B2-Adapt-2: Calculate adjusted difficulty for Round 2."""

    def test_low_tier_decreases_difficulty(self, db_session: Session) -> None:
        """Low tier (0-40%): avg_difficulty - 1."""
        service = AdaptiveDifficultyService(db_session)

        # Round 1 avg difficulty: 6, score: 30%
        adjusted = service.calculate_round2_difficulty(6.0, 30.0)

        # Should be 6 - 1 = 5
        assert adjusted == 5.0

    def test_low_tier_clamps_to_minimum(self, db_session: Session) -> None:
        """Low tier: minimum difficulty is 1.0 (cannot go below)."""
        service = AdaptiveDifficultyService(db_session)

        # Round 1 avg difficulty: 2, score: 30%
        adjusted = service.calculate_round2_difficulty(2.0, 30.0)

        # Should be clamped to 1.0 (2 - 1 = 1)
        assert adjusted == 1.0

    def test_medium_tier_slight_increase(self, db_session: Session) -> None:
        """Medium tier (40-70%): avg_difficulty + 0.5."""
        service = AdaptiveDifficultyService(db_session)

        # Round 1 avg difficulty: 5, score: 55%
        adjusted = service.calculate_round2_difficulty(5.0, 55.0)

        # Should be 5 + 0.5 = 5.5
        assert adjusted == 5.5

    def test_high_tier_increases_difficulty(self, db_session: Session) -> None:
        """High tier (70%+): avg_difficulty + 2."""
        service = AdaptiveDifficultyService(db_session)

        # Round 1 avg difficulty: 4, score: 80%
        adjusted = service.calculate_round2_difficulty(4.0, 80.0)

        # Should be 4 + 2 = 6
        assert adjusted == 6.0

    def test_high_tier_clamps_to_maximum(self, db_session: Session) -> None:
        """High tier: maximum difficulty is 10.0 (cannot exceed)."""
        service = AdaptiveDifficultyService(db_session)

        # Round 1 avg difficulty: 9, score: 90%
        adjusted = service.calculate_round2_difficulty(9.0, 90.0)

        # Should be clamped to 10.0 (9 + 2 = 11 → 10)
        assert adjusted == 10.0


class TestWeakCategoryExtraction:
    """REQ-B-B2-Adapt-3: Extract weak categories from Round 1 results."""

    def test_get_weak_categories_single(
        self, db_session: Session, test_session_round1_fixture: "Session"
    ) -> None:  # noqa: ANN001
        """Get weak categories when user has weak areas."""
        # Create test result with weak categories
        result = TestResult(
            session_id=test_session_round1_fixture.id,
            round=1,
            score=50.0,
            total_points=50,
            correct_count=3,
            total_count=5,
            wrong_categories={"RAG": 2},
        )
        db_session.add(result)
        db_session.commit()

        service = AdaptiveDifficultyService(db_session)
        weak_cats = service.get_weak_categories(test_session_round1_fixture.id)

        assert weak_cats == {"RAG": 2}

    def test_get_weak_categories_multiple(self, db_session: Session, test_session_round1_fixture: TestSession) -> None:
        """Get multiple weak categories."""
        result = TestResult(
            session_id=test_session_round1_fixture.id,
            round=1,
            score=40.0,
            total_points=40,
            correct_count=2,
            total_count=5,
            wrong_categories={"RAG": 2, "Robotics": 1},
        )
        db_session.add(result)
        db_session.commit()

        service = AdaptiveDifficultyService(db_session)
        weak_cats = service.get_weak_categories(test_session_round1_fixture.id)

        assert weak_cats == {"RAG": 2, "Robotics": 1}

    def test_get_weak_categories_none(self, db_session: Session, test_session_round1_fixture: TestSession) -> None:
        """No weak categories when user got all correct."""
        result = TestResult(
            session_id=test_session_round1_fixture.id,
            round=1,
            score=100.0,
            total_points=500,
            correct_count=5,
            total_count=5,
            wrong_categories=None,
        )
        db_session.add(result)
        db_session.commit()

        service = AdaptiveDifficultyService(db_session)
        weak_cats = service.get_weak_categories(test_session_round1_fixture.id)

        assert weak_cats == {}

    def test_missing_round1_result_raises_error(self, db_session: Session) -> None:
        """Missing Round 1 result raises ValueError."""
        service = AdaptiveDifficultyService(db_session)

        with pytest.raises(ValueError, match="Round 1 result not found"):
            service.get_weak_categories("non_existent_session_id")


class TestCategoryPrioritization:
    """REQ-B-B2-Adapt-3: Calculate category prioritization ratio."""

    def test_single_weak_category_60_percent(self, db_session: Session) -> None:
        """Single weak category gets ≥50% (3 of 5 questions)."""
        service = AdaptiveDifficultyService(db_session)

        weak_cats = {"RAG": 2}
        ratio = service.get_category_priority_ratio(weak_cats, total_questions=5)

        assert "RAG" in ratio
        assert ratio["RAG"] >= 3  # ≥50% of 5 questions

    def test_multiple_weak_categories_distribution(self, db_session: Session) -> None:
        """Multiple weak categories distributed fairly."""
        service = AdaptiveDifficultyService(db_session)

        weak_cats = {"RAG": 2, "Robotics": 1}
        ratio = service.get_category_priority_ratio(weak_cats, total_questions=5)

        # Total from weak categories should be ≥3 (≥50%)
        total_weak = sum(ratio.values())
        assert total_weak >= 3

    def test_no_weak_categories_empty_ratio(self, db_session: Session) -> None:
        """No weak categories returns empty ratio."""
        service = AdaptiveDifficultyService(db_session)

        weak_cats = {}
        ratio = service.get_category_priority_ratio(weak_cats, total_questions=5)

        assert ratio == {}

    def test_priority_ratio_sums_correctly(self, db_session: Session) -> None:
        """Priority ratio doesn't exceed total questions."""
        service = AdaptiveDifficultyService(db_session)

        weak_cats = {"RAG": 2}
        ratio = service.get_category_priority_ratio(weak_cats, total_questions=5)

        assert sum(ratio.values()) <= 5


class TestAdaptiveParametersIntegration:
    """REQ-B-B2-Adapt-1, 2, 3: Get all adaptive parameters together."""

    def test_get_adaptive_params_with_weak_categories(
        self, db_session: Session, test_result_low_score: TestResult
    ) -> None:
        """Get all adaptive parameters for low score with weak categories."""
        service = AdaptiveDifficultyService(db_session)

        params = service.get_adaptive_generation_params(test_result_low_score.session_id)

        assert params["difficulty_tier"] == "low"
        assert params["adjusted_difficulty"] <= 5.0  # Decreased
        assert len(params["weak_categories"]) > 0
        assert len(params["priority_ratio"]) > 0

    def test_get_adaptive_params_medium_score(self, db_session: Session, test_result_medium_score: TestResult) -> None:
        """Get adaptive parameters for medium score."""
        service = AdaptiveDifficultyService(db_session)

        params = service.get_adaptive_generation_params(test_result_medium_score.session_id)

        assert params["difficulty_tier"] == "medium"
        assert 5.0 <= params["adjusted_difficulty"] <= 6.0
        assert "RAG" in params["weak_categories"]

    def test_get_adaptive_params_high_score(self, db_session: Session, test_result_high_score: TestResult) -> None:
        """Get adaptive parameters for high score."""
        service = AdaptiveDifficultyService(db_session)

        params = service.get_adaptive_generation_params(test_result_high_score.session_id)

        assert params["difficulty_tier"] == "high"
        assert params["adjusted_difficulty"] >= 6.0  # Increased
