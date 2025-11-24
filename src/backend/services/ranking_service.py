"""
Ranking and grading service for calculating final grades and rankings.

REQ: REQ-B-B4-1, REQ-B-B4-2, REQ-B-B4-3, REQ-B-B4-4, REQ-B-B4-5
REQ: REQ-B-B4-Plus-1, REQ-B-B4-Plus-2, REQ-B-B4-Plus-3
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.backend.models import TestResult, TestSession, User, UserBadge

# Grade cutoff thresholds (REQ-B-B4-2)
GRADE_CUTOFFS = {
    "Beginner": 0,
    "Intermediate": 40,
    "Inter-Advanced": 60,
    "Advanced": 75,
    "Elite": 90,
}

# Grade-to-badge mapping (REQ-B-B4-Plus-1)
GRADE_BADGES = {
    "Beginner": "시작자 배지",
    "Intermediate": "중급자 배지",
    "Inter-Advanced": "중상급자 배지",
    "Advanced": "고급자 배지",
    "Elite": "엘리트 배지",
}


@dataclass
class GradeDistribution:
    """Distribution data for a single grade tier."""

    grade: str
    count: int
    percentage: float


@dataclass
class GradeResult:
    """Result of grade and ranking calculation."""

    user_id: int
    grade: str
    score: float
    rank: int
    total_cohort_size: int
    percentile: float
    percentile_confidence: str
    percentile_description: str
    grade_distribution: list[GradeDistribution]


class RankingService:
    """
    Service for calculating final grades and rankings.

    REQ: REQ-B-B4-1~5, REQ-B-B4-Plus-1~3

    Design principle:
    - Aggregates all test results for a user
    - Calculates final grade based on composite score
    - Computes rank and percentile within 90-day cohort
    - Auto-assigns badges based on grade
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize RankingService.

        Args:
            session: SQLAlchemy database session

        """
        self.session = session

    def calculate_final_grade(self, user_id: int) -> GradeResult | None:
        """
        Calculate final grade and ranking for a user.

        REQ: REQ-B-B4-1, REQ-B-B4-3, REQ-B-B4-4, REQ-B-B4-5

        Args:
            user_id: User ID to calculate grade for

        Returns:
            GradeResult with grade, rank, percentile, confidence
            Returns None if user not found or no test results

        Raises:
            ValueError: If user_id is invalid

        """
        # Verify user exists
        user: User | None = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Get all completed test results for this user
        test_results: list[TestResult] = (
            self.session.query(TestResult)
            .join(TestSession, TestResult.session_id == TestSession.id)
            .filter(
                and_(
                    TestSession.user_id == user_id,
                    TestSession.status == "completed",
                )
            )
            .all()
        )

        # If no test results, return None
        if not test_results:
            return None

        # Calculate composite score (REQ-B-B4-1, REQ-B-B4-3)
        composite_score: float = self._calculate_composite_score(test_results)

        # Determine grade tier (REQ-B-B4-2)
        grade: str = self._determine_grade(composite_score)

        # Calculate rank and percentile within 90-day cohort (REQ-B-B4-4)
        rank, total_cohort_size = self._calculate_rank(user_id, composite_score)

        # Calculate percentile
        percentile: float = self._calculate_percentile(rank, total_cohort_size)

        # Determine percentile confidence (REQ-B-B4-5)
        percentile_confidence: str = "medium" if total_cohort_size < 100 else "high"

        # Generate percentile description
        percentile_description: str = f"상위 {100 - percentile:.1f}%"

        # Calculate grade distribution (REQ-B-B4-6)
        grade_dist: list[GradeDistribution] = self._calculate_grade_distribution()

        return GradeResult(
            user_id=user_id,
            grade=grade,
            score=round(composite_score, 2),
            rank=rank,
            total_cohort_size=total_cohort_size,
            percentile=round(percentile, 2),
            percentile_confidence=percentile_confidence,
            percentile_description=percentile_description,
            grade_distribution=grade_dist,
        )

    def _calculate_composite_score(self, test_results: list[TestResult]) -> float:
        """
        Calculate composite score from all test results with difficulty adjustment.

        REQ-B-B4-3: Base score + difficulty correction

        Args:
            test_results: List of TestResult objects

        Returns:
            Composite score (0-100)

        """
        if not test_results:
            return 0.0

        total_score: float = 0.0
        total_weight: float = 0.0

        for result in test_results:
            # Base score from test result
            base_score: float = result.score

            # Difficulty adjustment: weight by correct rate
            # If user gets most questions correct, boost score slightly
            if result.total_count > 0:
                correct_rate: float = result.correct_count / result.total_count
                difficulty_bonus: float = correct_rate * 5  # Up to 5% bonus
                adjusted_score: float = base_score + difficulty_bonus
            else:
                adjusted_score: float = base_score

            # Cap at 100
            adjusted_score: float = min(adjusted_score, 100.0)

            # Weight by round (Round 2 more important than Round 1)
            weight: float = 2.0 if result.round == 2 else 1.0

            total_score += adjusted_score * weight
            total_weight += weight

        # Calculate weighted average
        composite_score: float = total_score / total_weight if total_weight > 0 else 0.0

        return composite_score

    def _determine_grade(self, composite_score: float) -> str:
        """
        Determine grade tier from composite score.

        REQ-B-B4-2: 5-grade system

        Args:
            composite_score: Score (0-100)

        Returns:
            Grade string: Beginner, Intermediate, Inter-Advanced, Advanced, Elite

        """
        if composite_score >= GRADE_CUTOFFS["Elite"]:
            return "Elite"
        elif composite_score >= GRADE_CUTOFFS["Advanced"]:
            return "Advanced"
        elif composite_score >= GRADE_CUTOFFS["Inter-Advanced"]:
            return "Inter-Advanced"
        elif composite_score >= GRADE_CUTOFFS["Intermediate"]:
            return "Intermediate"
        else:
            return "Beginner"

    def _calculate_rank(self, user_id: int, user_score: float) -> tuple[int, int]:
        """
        Calculate relative rank within 90-day cohort.

        REQ-B-B4-4: RANK() OVER within 90-day period

        Args:
            user_id: User ID
            user_score: User's composite score

        Returns:
            Tuple of (rank, total_cohort_size)
            rank: 1-indexed position (1 is highest)

        """
        # Define 90-day window
        cutoff_date: datetime = datetime.now(UTC) - timedelta(days=90)

        # Get all users in 90-day cohort with their scores
        # Subquery: get composite scores for all users in cohort
        cohort_query = (
            self.session.query(
                TestSession.user_id,
                func.avg(TestResult.score).label("avg_score"),
            )
            .join(TestResult, TestResult.session_id == TestSession.id)
            .filter(
                and_(
                    TestSession.status == "completed",
                    TestSession.created_at >= cutoff_date,
                )
            )
            .group_by(TestSession.user_id)
            .all()
        )

        # Count users with score >= user_score
        rank: int = 1
        total_cohort_size: int = len(cohort_query)

        for _cohort_user_id, avg_score in cohort_query:
            if avg_score > user_score:
                rank += 1

        return rank, total_cohort_size

    def _calculate_percentile(self, rank: int, total_cohort_size: int) -> float:
        """
        Calculate percentile from rank.

        Args:
            rank: User's rank (1-indexed)
            total_cohort_size: Total users in cohort

        Returns:
            Percentile (0-100), where 100 = top performer

        """
        if total_cohort_size == 0:
            return 0.0

        # Percentile = (total - rank + 1) / total * 100
        # So rank 1 → 100th percentile, rank total → 0th percentile
        percentile: float = ((total_cohort_size - rank + 1) / total_cohort_size) * 100

        return percentile

    def _calculate_grade_distribution(self) -> list[GradeDistribution]:
        """
        Calculate grade distribution across all users with completed test sessions.

        REQ-B-B4-6: Return all grades with count and percentage

        Returns:
            List of GradeDistribution objects for each grade (Beginner~Elite)

        """
        # Get all completed test results and calculate composite scores for all users
        cohort_query = (
            self.session.query(
                TestSession.user_id,
                func.avg(TestResult.score).label("avg_score"),
                func.count(TestResult.id).label("result_count"),
            )
            .join(TestResult, TestResult.session_id == TestSession.id)
            .filter(TestSession.status == "completed")
            .group_by(TestSession.user_id)
            .all()
        )

        # Count users in each grade
        grade_counts: dict[str, int] = {
            "Beginner": 0,
            "Intermediate": 0,
            "Inter-Advanced": 0,
            "Advanced": 0,
            "Elite": 0,
        }

        # Classify each user into a grade
        for _user_id, avg_score, _result_count in cohort_query:
            grade: str = self._determine_grade(avg_score)
            grade_counts[grade] += 1

        # Calculate total and percentages
        total_users: int = len(cohort_query)
        distribution: list[GradeDistribution] = []

        for grade in ["Beginner", "Intermediate", "Inter-Advanced", "Advanced", "Elite"]:
            count: int = grade_counts[grade]
            percentage: float = (count / total_users * 100) if total_users > 0 else 0.0
            distribution.append(
                GradeDistribution(
                    grade=grade,
                    count=count,
                    percentage=round(percentage, 2),
                )
            )

        return distribution

    def assign_badges(self, user_id: int, grade: str) -> list[UserBadge]:
        """
        Assign badges to user based on grade.

        REQ: REQ-B-B4-Plus-1, REQ-B-B4-Plus-2, REQ-B-B4-Plus-3

        Args:
            user_id: User ID
            grade: Grade string (Beginner, Intermediate, etc.)

        Returns:
            List of assigned UserBadge objects

        """
        assigned_badges: list[UserBadge] = []

        # Check if user already has grade badge
        existing_grade_badge: UserBadge | None = (
            self.session.query(UserBadge)
            .filter(
                and_(
                    UserBadge.user_id == user_id,
                    UserBadge.badge_type == "grade",
                )
            )
            .first()
        )

        # Assign grade badge (REQ-B-B4-Plus-1)
        if not existing_grade_badge:
            badge_name: str = GRADE_BADGES.get(grade, "알 수 없음")
            grade_badge: UserBadge = UserBadge(
                user_id=user_id,
                badge_name=badge_name,
                badge_type="grade",
                awarded_at=datetime.now(UTC),
            )
            self.session.add(grade_badge)
            assigned_badges.append(grade_badge)

        # If Elite, assign specialist badge (REQ-B-B4-Plus-2)
        if grade == "Elite":
            existing_specialist: UserBadge | None = (
                self.session.query(UserBadge)
                .filter(
                    and_(
                        UserBadge.user_id == user_id,
                        UserBadge.badge_type == "specialist",
                    )
                )
                .first()
            )

            if not existing_specialist:
                specialist_badge: UserBadge = UserBadge(
                    user_id=user_id,
                    badge_name="Agent Specialist 배지",
                    badge_type="specialist",
                    awarded_at=datetime.now(UTC),
                )
                self.session.add(specialist_badge)
                assigned_badges.append(specialist_badge)

        # Commit changes
        self.session.commit()

        return assigned_badges

    def get_user_badges(self, user_id: int) -> list[dict]:
        """
        Get all badges for a user.

        REQ-B-B4-Plus-3: Include in profile API

        Args:
            user_id: User ID

        Returns:
            List of badge dicts with name and awarded_date

        """
        badges: list[UserBadge] = self.session.query(UserBadge).filter(UserBadge.user_id == user_id).all()

        return [
            {
                "name": badge.badge_name,
                "awarded_date": badge.awarded_at.isoformat(),
                "type": badge.badge_type,
            }
            for badge in badges
        ]
