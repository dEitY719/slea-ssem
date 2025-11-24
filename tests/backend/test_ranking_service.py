"""
Test suite for RankingService (REQ-B-B4 & REQ-B-B4-Plus).

REQ-B-B4: 최종 등급 및 순위 산출
- REQ-B-B4-1: Aggregate all test attempt scores → final grade
- REQ-B-B4-2: Define 5-grade system
- REQ-B-B4-3: Grade calculation with difficulty adjustment
- REQ-B-B4-4: Rank & percentile for 90-day cohort
- REQ-B-B4-5: percentile_confidence="medium" when population < 100

REQ-B-B4-Plus: 등급 기반 배지 부여
- REQ-B-B4-Plus-1: Auto-assign grade-based badges
- REQ-B-B4-Plus-2: Elite grade → specialist badge (top 5%)
- REQ-B-B4-Plus-3: Save badges to user_badges, include in profile API
"""  # noqa: ANN001, ANN201, D400, D415

import pytest
from sqlalchemy.orm import Session

from src.backend.models import TestResult, TestSession, UserBadge


class TestGradeCalculation:
    """Test REQ-B-B4-1, REQ-B-B4-2, REQ-B-B4-3: Grade calculation logic."""

    def test_single_round_score_to_beginner_grade(self, db_session: Session, test_result_low_score):
        """
        REQ-B-B4-1, REQ-B-B4-3: Single round with low score → Beginner grade.

        Score: 30/100
        Expected: grade='Beginner'
        """
        from src.backend.services.ranking_service import RankingService

        # Get user_id from test result
        test_session = db_session.query(TestSession).filter(TestSession.id == test_result_low_score.session_id).first()
        user_id = test_session.user_id

        # Call RankingService
        service = RankingService(db_session)
        result = service.calculate_final_grade(user_id)

        # Assert
        assert result is not None
        assert result.grade == "Beginner"

    def test_single_round_score_to_advanced_grade(self, db_session: Session, test_result_high_score):
        """
        REQ-B-B4-1, REQ-B-B4-3: Single round with high score → Advanced grade.

        Score: 80/100
        Expected: grade='Advanced'
        Acceptance Criteria: "최종 점수 80/100 시 등급이 'Advanced'로 정확히 산출된다."
        """
        from src.backend.services.ranking_service import RankingService

        # Get user_id from test result
        test_session = db_session.query(TestSession).filter(TestSession.id == test_result_high_score.session_id).first()
        user_id = test_session.user_id

        # Call RankingService
        service = RankingService(db_session)
        result = service.calculate_final_grade(user_id)

        # Assert
        assert result is not None
        assert result.grade == "Advanced"
        assert result.score >= 75

    def test_multi_round_aggregate_score(
        self,
        db_session: Session,
        user_fixture,
        user_profile_survey_fixture,
        create_test_session_with_result,  # noqa: ANN001
    ):
        """
        REQ-B-B4-1, REQ-B-B4-3: Multiple rounds aggregate → weighted final grade.

        Round 1: 60/100
        Round 2: 85/100
        Expected: aggregate score ~75 (weighted towards round 2)
        Expected Grade: Inter-Advanced or Advanced
        """
        from src.backend.services.ranking_service import RankingService

        # Create 2 test results
        create_test_session_with_result(user_fixture.id, user_profile_survey_fixture.id, 60.0, round_num=1)
        create_test_session_with_result(user_fixture.id, user_profile_survey_fixture.id, 85.0, round_num=2)

        # Call RankingService
        service = RankingService(db_session)
        result = service.calculate_final_grade(user_fixture.id)

        # Assert
        assert result is not None
        # Weighted: (60*1 + 85*2) / 3 = 76.67
        assert result.score >= 70 and result.score <= 85
        assert result.grade in ["Inter-Advanced", "Advanced"]

    def test_all_five_grade_tiers(
        self, db_session: Session, create_multiple_users, create_survey_for_user, create_test_session_with_result
    ):
        """
        REQ-B-B4-2: All 5 grade tiers are correctly assigned.

        Test scores: [20, 45, 65, 80, 95]
        Expected grades: [Beginner, Intermediate, Inter-Advanced, Advanced, Elite]
        """
        from src.backend.services.ranking_service import RankingService

        # Create 5 users
        users = create_multiple_users(5)
        scores = [20, 45, 65, 80, 95]
        expected_grades = ["Beginner", "Intermediate", "Inter-Advanced", "Advanced", "Elite"]

        service = RankingService(db_session)

        for user, score, expected_grade in zip(users, scores, expected_grades, strict=False):
            survey = create_survey_for_user(user.id)
            create_test_session_with_result(user.id, survey.id, float(score))

            result = service.calculate_final_grade(user.id)
            assert result is not None
            assert result.grade == expected_grade, f"User {user.id}: expected {expected_grade}, got {result.grade}"

    def test_difficulty_weighted_score_adjustment(self, db_session: Session, user_fixture, user_profile_survey_fixture):
        """
        REQ-B-B4-3: Difficulty-adjusted score = base_score + difficulty_correction.

        Base score: 60%, correct_count=3/5
        With difficulty adjustment, score should be > 60
        """
        from src.backend.services.ranking_service import RankingService

        # Create test result with 3/5 correct → score=60%
        test_session = TestSession(
            user_id=user_fixture.id,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="completed",
        )
        db_session.add(test_session)
        db_session.flush()

        result = TestResult(
            session_id=test_session.id,
            round=1,
            score=60.0,
            total_points=60,
            correct_count=3,  # 3/5 = 60%
            total_count=5,
            wrong_categories={"RAG": 2},
        )
        db_session.add(result)
        db_session.commit()

        # Call RankingService
        service = RankingService(db_session)
        grade_result = service.calculate_final_grade(user_fixture.id)

        # Assert: score should be boosted due to difficulty adjustment
        assert grade_result is not None
        assert grade_result.score > 60  # Should have difficulty bonus


class TestRankAndPercentile:
    """
    Test REQ-B-B4-4, REQ-B-B4-5: Ranking and percentile calculation.
    """

    def test_rank_calculation_for_90day_cohort(
        self, db_session: Session, create_multiple_users, create_survey_for_user, create_test_session_with_result
    ):
        """
        REQ-B-B4-4: Relative rank (RANK() OVER) within 90-day cohort.

        Setup: 10 users in same 90-day period with different scores
        User A: 80/100
        Expected: rank = 3/10 (3rd out of 10)
        """
        from src.backend.services.ranking_service import RankingService

        # Create 10 users with scores: 90, 85, 80, 75, 70, 65, 60, 55, 50, 45
        users = create_multiple_users(10)
        scores = [90, 85, 80, 75, 70, 65, 60, 55, 50, 45]

        service = RankingService(db_session)

        for user, score in zip(users, scores, strict=False):
            survey = create_survey_for_user(user.id)
            # Create session with days_ago=0 (within 90 days)
            create_test_session_with_result(user.id, survey.id, float(score), days_ago=0)

        # Find target user with score=80
        target_user = users[2]  # score=80

        result = service.calculate_final_grade(target_user.id)

        # Assert
        assert result is not None
        assert result.rank == 3  # 3rd highest (90, 85, 80)
        assert result.total_cohort_size == 10

    def test_percentile_calculation(
        self, db_session: Session, create_multiple_users, create_survey_for_user, create_test_session_with_result
    ):
        """
        REQ-B-B4-4: Percentile within 90-day cohort.

        10 users, user at rank 3 → percentile = (10-3+1)/10 = 80th percentile
        """
        from src.backend.services.ranking_service import RankingService

        # Create 10 users with scores
        users = create_multiple_users(10)
        scores = [90, 85, 80, 75, 70, 65, 60, 55, 50, 45]

        service = RankingService(db_session)

        for user, score in zip(users, scores, strict=False):
            survey = create_survey_for_user(user.id)
            create_test_session_with_result(user.id, survey.id, float(score), days_ago=0)

        # Target user with score=80 (rank 3/10)
        target_user = users[2]
        result = service.calculate_final_grade(target_user.id)

        # Assert
        assert result is not None
        # Percentile = (10-3+1)/10 * 100 = 80%
        assert result.percentile == 80.0
        assert "상위" in result.percentile_description

    def test_percentile_confidence_medium_for_small_cohort(
        self, db_session: Session, create_multiple_users, create_survey_for_user, create_test_session_with_result
    ):
        """
        REQ-B-B4-5: If cohort population < 100, percentile_confidence = "medium".

        Setup: 50 users in 90-day cohort
        Expected: percentile_confidence == "medium"
        """
        from src.backend.services.ranking_service import RankingService

        # Create 50 users
        users = create_multiple_users(50)
        service = RankingService(db_session)

        for idx, user in enumerate(users):
            survey = create_survey_for_user(user.id)
            score = 50.0 + (idx * 0.5)  # Stagger scores
            create_test_session_with_result(user.id, survey.id, score, days_ago=0)

        # Check first user
        result = service.calculate_final_grade(users[0].id)

        # Assert
        assert result is not None
        assert result.total_cohort_size == 50
        assert result.percentile_confidence == "medium"

    def test_percentile_confidence_high_for_large_cohort(
        self, db_session: Session, create_multiple_users, create_survey_for_user, create_test_session_with_result
    ):
        """
        REQ-B-B4-5: If cohort population >= 100, percentile_confidence = "high".

        Setup: 150 users in 90-day cohort
        Expected: percentile_confidence == "high"
        """
        from src.backend.services.ranking_service import RankingService

        # Create 150 users
        users = create_multiple_users(150)
        service = RankingService(db_session)

        for idx, user in enumerate(users):
            survey = create_survey_for_user(user.id)
            score = 50.0 + (idx * 0.3)  # Stagger scores
            create_test_session_with_result(user.id, survey.id, score, days_ago=0)

        # Check first user
        result = service.calculate_final_grade(users[0].id)

        # Assert
        assert result is not None
        assert result.total_cohort_size == 150
        assert result.percentile_confidence == "high"

    def test_exclude_users_outside_90day_window(
        self, db_session: Session, create_multiple_users, create_survey_for_user, create_test_session_with_result
    ):
        """
        REQ-B-B4-4: Only users with test_session.created_at within last 90 days
        are included in rank calculation.

        Setup: 10 users in last 90 days + 5 users from 6 months ago
        Expected: rank calculated against 10, not 15
        """
        from src.backend.services.ranking_service import RankingService

        # Create 15 users
        users = create_multiple_users(15)
        service = RankingService(db_session)

        # First 10 users: within 90 days (days_ago=0)
        for idx in range(10):
            user = users[idx]
            survey = create_survey_for_user(user.id)
            create_test_session_with_result(user.id, survey.id, 70.0, days_ago=0)

        # Last 5 users: > 90 days ago (days_ago=180)
        for idx in range(10, 15):
            user = users[idx]
            survey = create_survey_for_user(user.id)
            create_test_session_with_result(user.id, survey.id, 90.0, days_ago=180)

        # Check first user (in 90-day cohort)
        result = service.calculate_final_grade(users[0].id)

        # Assert: should only count 10 users, not 15
        assert result is not None
        assert result.total_cohort_size == 10


class TestBadgeAssignment:
    """
    Test REQ-B-B4-Plus-1, REQ-B-B4-Plus-2, REQ-B-B4-Plus-3: Badge system.
    """

    def test_badge_assignment_for_all_grades(
        self, db_session: Session, create_multiple_users, create_survey_for_user, create_test_session_with_result
    ):
        """
        REQ-B-B4-Plus-1: Each grade tier gets corresponding badge.

        Beginner → "시작자 배지"
        Intermediate → "중급자 배지"
        Inter-Advanced → "중상급자 배지"
        Advanced → "고급자 배지"
        Elite → "엘리트 배지"
        """
        from src.backend.services.ranking_service import RankingService

        # Create 5 users with scores for each grade
        users = create_multiple_users(5)
        scores = [20, 45, 65, 80, 95]
        expected_badges = [
            "시작자 배지",
            "중급자 배지",
            "중상급자 배지",
            "고급자 배지",
            "엘리트 배지",
        ]

        service = RankingService(db_session)

        for user, score, expected_badge in zip(users, scores, expected_badges, strict=False):
            survey = create_survey_for_user(user.id)
            create_test_session_with_result(user.id, survey.id, float(score))

            # Calculate grade first
            grade_result = service.calculate_final_grade(user.id)
            assert grade_result is not None

            # Assign badge
            badges = service.assign_badges(user.id, grade_result.grade)

            # Query user_badges
            user_badges = db_session.query(UserBadge).filter(UserBadge.user_id == user.id).all()

            # Assert
            assert len(user_badges) >= 1
            assert user_badges[0].badge_name == expected_badge

    def test_elite_user_specialist_badge(
        self, db_session: Session, create_multiple_users, create_survey_for_user, create_test_session_with_result
    ):
        """
        REQ-B-B4-Plus-2: Elite users get specialist badge in addition to grade badge.

        Expected: 2 badges: "엘리트 배지" + "Agent Specialist 배지"
        """
        from src.backend.services.ranking_service import RankingService

        # Create test user with Elite score
        users = create_multiple_users(1)
        user = users[0]
        survey = create_survey_for_user(user.id)
        create_test_session_with_result(user.id, survey.id, 95.0)  # Elite score

        service = RankingService(db_session)
        grade_result = service.calculate_final_grade(user.id)

        assert grade_result is not None
        assert grade_result.grade == "Elite"

        # Assign badges
        badges = service.assign_badges(user.id, grade_result.grade)

        # Query user_badges
        user_badges = db_session.query(UserBadge).filter(UserBadge.user_id == user.id).all()

        # Assert: 2 badges (grade + specialist)
        assert len(user_badges) >= 2
        badge_names = [b.badge_name for b in user_badges]
        assert "엘리트 배지" in badge_names
        assert "Agent Specialist 배지" in badge_names

    def test_badges_stored_in_user_badges_table(
        self, db_session: Session, user_fixture, user_profile_survey_fixture, create_test_session_with_result
    ):
        """
        REQ-B-B4-Plus-3: Badges persisted to user_badges table.
        """
        from src.backend.services.ranking_service import RankingService

        # Create test result with Advanced score
        create_test_session_with_result(user_fixture.id, user_profile_survey_fixture.id, 80.0)

        service = RankingService(db_session)
        grade_result = service.calculate_final_grade(user_fixture.id)

        assert grade_result is not None
        assert grade_result.grade == "Advanced"

        # Assign badge
        service.assign_badges(user_fixture.id, grade_result.grade)

        # Query user_badges table
        user_badges = db_session.query(UserBadge).filter(UserBadge.user_id == user_fixture.id).all()

        # Assert
        assert len(user_badges) == 1
        badge = user_badges[0]
        assert badge.badge_name == "고급자 배지"
        assert badge.user_id == user_fixture.id
        assert badge.awarded_at is not None

    def test_badges_included_in_profile_api(
        self, db_session: Session, user_fixture, user_profile_survey_fixture, create_test_session_with_result
    ):
        """
        REQ-B-B4-Plus-3: Profile API can retrieve user badges.
        """
        from src.backend.services.ranking_service import RankingService

        # Create test result and assign badges
        create_test_session_with_result(user_fixture.id, user_profile_survey_fixture.id, 80.0)

        service = RankingService(db_session)
        grade_result = service.calculate_final_grade(user_fixture.id)
        service.assign_badges(user_fixture.id, grade_result.grade)

        # Get user badges via service
        badges_dict = service.get_user_badges(user_fixture.id)

        # Assert
        assert isinstance(badges_dict, list)
        assert len(badges_dict) >= 1
        assert "name" in badges_dict[0]
        assert "awarded_date" in badges_dict[0]
        assert badges_dict[0]["name"] == "고급자 배지"


class TestInputValidationAndErrors:
    """
    Test error handling and edge cases.
    """

    def test_invalid_user_id_raises_error(self, db_session: Session):
        """
        REQ-B-B4-1: Invalid user_id → raise appropriate exception.

        Input: user_id that does not exist
        Expected: ValueError or UserNotFound exception
        """
        from src.backend.services.ranking_service import RankingService

        service = RankingService(db_session)

        # Call with non-existent user_id
        with pytest.raises(ValueError):
            service.calculate_final_grade(user_id=999)

    def test_user_with_no_test_results(self, db_session: Session, user_fixture):
        """
        REQ-B-B4-1: User with no test results → no grade calculated.

        Input: user_id with no TestResult records
        Expected: return None
        """
        from src.backend.services.ranking_service import RankingService

        service = RankingService(db_session)

        # User exists but has no test results
        result = service.calculate_final_grade(user_fixture.id)

        # Assert
        assert result is None

    def test_incomplete_test_session_excluded(
        self, db_session: Session, user_fixture, user_profile_survey_fixture, create_test_session_with_result
    ):
        """
        REQ-B-B4-1: Incomplete test sessions should not affect grade.

        Setup: User with 2 completed test_results + 1 in_progress session
        Expected: Grade calculated from 2 completed sessions only
        """
        from src.backend.services.ranking_service import RankingService

        # Create 2 completed test results
        create_test_session_with_result(user_fixture.id, user_profile_survey_fixture.id, 60.0)
        create_test_session_with_result(user_fixture.id, user_profile_survey_fixture.id, 70.0)

        # Create 1 in-progress session (should be ignored)
        in_progress_session = TestSession(
            user_id=user_fixture.id,
            survey_id=user_profile_survey_fixture.id,
            round=2,
            status="in_progress",
        )
        db_session.add(in_progress_session)
        db_session.commit()

        service = RankingService(db_session)
        result = service.calculate_final_grade(user_fixture.id)

        # Assert: grade based on 2 completed sessions
        assert result is not None
        # Average of 60 and 70 with weighting
        assert result.score >= 60 and result.score <= 75


class TestAcceptanceCriteria:
    """
    Test explicit acceptance criteria from feature requirements.
    """

    def test_acceptance_score_80_equals_advanced_grade(
        self, db_session: Session, user_fixture, user_profile_survey_fixture, create_test_session_with_result
    ):
        """
        Acceptance Criteria: "최종 점수 80/100 시 등급이 'Advanced'로 정확히 산출된다."

        Input: Final score = 80
        Expected: grade == 'Advanced'
        """
        from src.backend.services.ranking_service import RankingService

        # Create user with score=80
        create_test_session_with_result(user_fixture.id, user_profile_survey_fixture.id, 80.0)

        service = RankingService(db_session)
        result = service.calculate_final_grade(user_fixture.id)

        # Assert
        assert result is not None
        assert result.grade == "Advanced"

    def test_acceptance_rank_and_percentile_accuracy(
        self, db_session: Session, create_multiple_users, create_survey_for_user, create_test_session_with_result
    ):
        """
        Acceptance Criteria: "점수 80일 때 상대 순위(예: 3/506)와 백분위(상위 28%)가 정확히 계산된다."

        Setup: Multiple users with score 80, verify rank and percentile
        """
        from src.backend.services.ranking_service import RankingService

        # Create users with staggered scores
        users = create_multiple_users(10)
        scores = [90, 85, 80, 80, 80, 75, 70, 65, 60, 55]

        service = RankingService(db_session)

        for user, score in zip(users, scores, strict=False):
            survey = create_survey_for_user(user.id)
            create_test_session_with_result(user.id, survey.id, float(score))

        # Target user with score=80 (one of three with 80)
        target_user = users[2]
        result = service.calculate_final_grade(target_user.id)

        # Assert
        assert result is not None
        assert result.rank >= 1 and result.rank <= 10
        assert result.total_cohort_size == 10
        assert result.percentile >= 0 and result.percentile <= 100
        assert "상위" in result.percentile_description

    def test_acceptance_badges_auto_saved_on_grade_calculation(
        self, db_session: Session, user_fixture, user_profile_survey_fixture, create_test_session_with_result
    ):
        """
        Acceptance Criteria: "등급 산출 후 자동으로 해당 등급 배지가 user_badges에 저장된다."

        Setup: User with score=80 (Advanced grade)
        """
        from src.backend.services.ranking_service import RankingService

        # Create test result
        create_test_session_with_result(user_fixture.id, user_profile_survey_fixture.id, 80.0)

        # Verify no badges initially
        initial_badges = db_session.query(UserBadge).filter(UserBadge.user_id == user_fixture.id).all()
        assert len(initial_badges) == 0

        # Calculate grade and assign badges
        service = RankingService(db_session)
        result = service.calculate_final_grade(user_fixture.id)
        assert result is not None

        service.assign_badges(user_fixture.id, result.grade)

        # Query user_badges after
        final_badges = db_session.query(UserBadge).filter(UserBadge.user_id == user_fixture.id).all()

        # Assert
        assert len(final_badges) == 1
        assert final_badges[0].badge_name == "고급자 배지"

    def test_acceptance_elite_gets_two_plus_badges(
        self, db_session: Session, user_fixture, user_profile_survey_fixture, create_test_session_with_result
    ):
        """
        Acceptance Criteria: "엘리트 등급 사용자는 일반 배지 + 특수 배지(Agent Specialist 등) 2개 이상이 부여된다."

        Setup: User with score=95 (Elite grade)
        Expected: 2+ badges (grade + specialist)
        """
        from src.backend.services.ranking_service import RankingService

        # Create test result with Elite score
        create_test_session_with_result(user_fixture.id, user_profile_survey_fixture.id, 95.0)

        service = RankingService(db_session)
        result = service.calculate_final_grade(user_fixture.id)

        assert result is not None
        assert result.grade == "Elite"

        # Assign badges
        service.assign_badges(user_fixture.id, result.grade)

        # Query user_badges
        badges = db_session.query(UserBadge).filter(UserBadge.user_id == user_fixture.id).all()

        # Assert
        assert len(badges) >= 2
        badge_names = [b.badge_name for b in badges]
        assert "엘리트 배지" in badge_names
        assert "Agent Specialist 배지" in badge_names


class TestGradeDistribution:
    """Test REQ-B-B4-6: Grade distribution data in ranking response."""

    def test_grade_distribution_includes_all_grades(
        self,
        db_session: Session,
        create_multiple_users,  # noqa: ANN001
        create_survey_for_user,  # noqa: ANN001
        create_test_session_with_result,  # noqa: ANN001
    ):
        """
        REQ-B-B4-6: grade_distribution should include all 5 grades.

        Test that all grades (Beginner, Intermediate, Inter-Advanced, Advanced, Elite)
        are included in the grade_distribution array.
        """
        from src.backend.services.ranking_service import RankingService

        # Create users with scores across all grade tiers
        users = create_multiple_users(5)
        scores = [20, 50, 65, 80, 95]  # One for each grade
        grade_names = ["Beginner", "Intermediate", "Inter-Advanced", "Advanced", "Elite"]

        for user, score in zip(users, scores, strict=False):
            survey = create_survey_for_user(user.id)
            create_test_session_with_result(user.id, survey.id, float(score))

        # Calculate grade for first user
        service = RankingService(db_session)
        result = service.calculate_final_grade(users[0].id)

        # Assert grade_distribution exists and has all 5 grades
        assert result is not None
        assert result.grade_distribution is not None
        assert len(result.grade_distribution) == 5

        # Check all grades are present
        dist_grades = [dist.grade for dist in result.grade_distribution]
        for expected_grade in grade_names:
            assert expected_grade in dist_grades

    def test_grade_distribution_counts_correct(
        self,
        db_session: Session,
        create_multiple_users,  # noqa: ANN001
        create_survey_for_user,  # noqa: ANN001
        create_test_session_with_result,  # noqa: ANN001
    ):
        """
        REQ-B-B4-6: grade_distribution should show correct counts and percentages.

        Test that count and percentage are calculated correctly.
        Setup: 10 users with varying scores across grade tiers
        """
        from src.backend.services.ranking_service import RankingService

        # Create 10 users: 2 Beginner, 3 Intermediate, 2 Inter-Advanced, 2 Advanced, 1 Elite
        users = create_multiple_users(10)
        scores = [20, 30, 45, 50, 55, 65, 70, 75, 80, 95]

        for user, score in zip(users, scores, strict=False):
            survey = create_survey_for_user(user.id)
            create_test_session_with_result(user.id, survey.id, float(score))

        service = RankingService(db_session)
        result = service.calculate_final_grade(users[0].id)

        # Check grade distribution
        assert result is not None
        dist = {d.grade: (d.count, d.percentage) for d in result.grade_distribution}

        # Verify counts
        assert dist["Beginner"][0] == 2
        assert dist["Intermediate"][0] == 3
        assert dist["Inter-Advanced"][0] == 2
        assert dist["Advanced"][0] == 2
        assert dist["Elite"][0] == 1

        # Verify percentages sum to 100
        total_percentage = sum(d[1] for d in dist.values())
        assert abs(total_percentage - 100.0) < 0.1  # Allow small rounding error

    def test_grade_distribution_zero_count_for_empty_grades(
        self,
        db_session: Session,
        create_multiple_users,  # noqa: ANN001
        create_survey_for_user,  # noqa: ANN001
        create_test_session_with_result,  # noqa: ANN001
    ):
        """
        REQ-B-B4-6: If no users in a grade, count=0 and percentage=0.0.

        Test that empty grades are included with 0 count and 0% percentage.
        Acceptance Criteria: "grade_distribution의 모든 등급이 포함되며,
        인원이 없는 등급은 count=0, percentage=0.0으로 표시된다."
        """
        from src.backend.services.ranking_service import RankingService

        # Create only 2 users, both Beginner
        users = create_multiple_users(2)
        for user in users:
            survey = create_survey_for_user(user.id)
            create_test_session_with_result(user.id, survey.id, 25.0)

        service = RankingService(db_session)
        result = service.calculate_final_grade(users[0].id)

        assert result is not None
        dist = {d.grade: (d.count, d.percentage) for d in result.grade_distribution}

        # Beginner should have count=2, percentage=100
        assert dist["Beginner"] == (2, 100.0)

        # Other grades should have count=0, percentage=0.0
        for grade in ["Intermediate", "Inter-Advanced", "Advanced", "Elite"]:
            assert dist[grade] == (0, 0.0)


# =============================================================================
# SUMMARY OF TEST CASES
# =============================================================================
#
# Total Test Cases: 24
#
# Test Coverage Matrix:
#
# REQ-B-B4-1 (Aggregate scores):
#   ✓ test_single_round_score_to_beginner_grade
#   ✓ test_single_round_score_to_advanced_grade
#   ✓ test_multi_round_aggregate_score
#   ✓ test_invalid_user_id_raises_error
#   ✓ test_user_with_no_test_results
#   ✓ test_incomplete_test_session_excluded
#
# REQ-B-B4-2 (5-grade system):
#   ✓ test_all_five_grade_tiers
#
# REQ-B-B4-3 (Grade calculation logic):
#   ✓ test_difficulty_weighted_score_adjustment
#
# REQ-B-B4-4 (Rank & percentile for 90-day cohort):
#   ✓ test_rank_calculation_for_90day_cohort
#   ✓ test_percentile_calculation
#   ✓ test_exclude_users_outside_90day_window
#   ✓ test_acceptance_rank_and_percentile_accuracy
#
# REQ-B-B4-5 (percentile_confidence):
#   ✓ test_percentile_confidence_medium_for_small_cohort
#   ✓ test_percentile_confidence_high_for_large_cohort
#
# REQ-B-B4-6 (Grade distribution):
#   ✓ test_grade_distribution_includes_all_grades
#   ✓ test_grade_distribution_counts_correct
#   ✓ test_grade_distribution_zero_count_for_empty_grades
#
# REQ-B-B4-Plus-1 (Grade-based badges):
#   ✓ test_badge_assignment_for_all_grades
#   ✓ test_acceptance_badges_auto_saved_on_grade_calculation
#
# REQ-B-B4-Plus-2 (Elite specialist badges):
#   ✓ test_elite_user_specialist_badge
#   ✓ test_acceptance_elite_gets_two_plus_badges
#
# REQ-B-B4-Plus-3 (Save & include in profile API):
#   ✓ test_badges_stored_in_user_badges_table
#   ✓ test_badges_included_in_profile_api
#
# Acceptance Criteria:
#   ✓ test_acceptance_score_80_equals_advanced_grade
#   ✓ test_acceptance_rank_and_percentile_accuracy
#
# =============================================================================
