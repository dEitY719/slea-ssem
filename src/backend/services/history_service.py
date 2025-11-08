"""
History service for managing test attempt history and retry functionality.

REQ: REQ-B-B5-1, REQ-B-B5-2, REQ-B-B5-3, REQ-B-B5-4, REQ-B-B5-5
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.backend.models import Attempt, AttemptRound, TestResult, TestSession, User, UserProfileSurvey
from src.backend.services.ranking_service import RankingService


@dataclass
class ImprovementResult:
    """Improvement metrics comparing two attempts."""

    previous_score: float
    current_score: float
    score_change: float  # +/- points
    previous_grade: str
    current_grade: str
    grade_improved: bool
    time_previous_seconds: int
    time_current_seconds: int
    time_change_seconds: int  # +/- seconds
    metrics_available: bool  # False if first attempt


class HistoryService:
    """
    Service for managing test attempt history and retry functionality.

    REQ: REQ-B-B5-1~5

    Design principle:
    - Separate test attempt history from active test state (TestSession)
    - Track all attempts for user with snapshot of survey at time of attempt
    - Support retry with new survey version (creates new UserProfileSurvey record)
    - Calculate improvement metrics between consecutive attempts
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize HistoryService.

        Args:
            session: SQLAlchemy database session

        """
        self.session = session

    def save_attempt(
        self,
        user_id: int,
        survey_id: str,
        test_session_id: str,
        test_type: str = "level_test",
    ) -> Attempt:
        """
        Save completed test session to permanent attempts table.

        REQ: REQ-B-B5-1

        Args:
            user_id: User ID
            survey_id: UserProfileSurvey ID (snapshot at time of test)
            test_session_id: TestSession ID to convert to Attempt
            test_type: Type of test ('level_test' or 'fun_quiz')

        Returns:
            Created Attempt object

        Raises:
            ValueError: If test_session or user not found

        """
        # Verify user exists
        user: User | None = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Get test session
        test_session: TestSession | None = (
            self.session.query(TestSession).filter(TestSession.id == test_session_id).first()
        )
        if not test_session:
            raise ValueError(f"TestSession with id {test_session_id} not found")

        # Get all test results for this session (both rounds if applicable)
        test_results: list[TestResult] = (
            self.session.query(TestResult)
            .filter(TestResult.session_id == test_session_id)
            .order_by(TestResult.round)
            .all()
        )

        # Calculate final grade and rank using RankingService
        ranking_service = RankingService(self.session)
        grade_result = ranking_service.calculate_final_grade(user_id)

        # Create Attempt record
        attempt: Attempt = Attempt(
            user_id=user_id,
            survey_id=survey_id,
            test_type=test_type,
            started_at=test_session.created_at,
            finished_at=datetime.utcnow(),
            final_grade=grade_result.grade if grade_result else None,
            final_score=grade_result.score if grade_result else None,
            percentile=int(grade_result.percentile) if grade_result else None,
            rank=grade_result.rank if grade_result else None,
            total_candidates=grade_result.total_cohort_size if grade_result else None,
            status="completed",
        )
        self.session.add(attempt)
        self.session.flush()  # Get attempt ID before creating rounds

        # Create AttemptRound records for each round
        total_time_seconds: int = 0
        for result in test_results:
            # Calculate time spent for this round
            round_time_seconds: int = self._calculate_round_time(test_session, result.round)
            total_time_seconds += round_time_seconds

            round_record: AttemptRound = AttemptRound(
                attempt_id=attempt.id,
                round_idx=result.round,
                score=result.score,
                time_spent_seconds=round_time_seconds,
            )
            self.session.add(round_record)

        self.session.commit()
        return attempt

    def _calculate_round_time(self, test_session: TestSession, round_num: int) -> int:
        """
        Calculate time spent on a specific round (placeholder implementation).

        In a real implementation, this would calculate based on when each round started/ended.
        For now, returns estimated time based on total session time.

        Args:
            test_session: TestSession object
            round_num: Round number (1, 2, etc.)

        Returns:
            Time in seconds spent on this round

        """
        if not test_session.created_at:
            return 0

        # Calculate total session duration
        finished_at: datetime = datetime.utcnow()
        duration_seconds: int = int((finished_at - test_session.created_at).total_seconds())

        # For MVP, distribute evenly across rounds (would be improved with round timing)
        return duration_seconds // 2 if round_num == 1 else duration_seconds - (duration_seconds // 2)

    def get_latest_attempt(self, user_id: int) -> Attempt | None:
        """
        Get most recent completed attempt for user.

        REQ: REQ-B-B5-2, REQ-B-B5-4

        Performance: O(1) with index on (user_id, finished_at DESC)

        Args:
            user_id: User ID

        Returns:
            Latest Attempt object or None if no attempts

        """
        latest: Attempt | None = (
            self.session.query(Attempt)
            .filter(
                and_(
                    Attempt.user_id == user_id,
                    Attempt.status == "completed",
                )
            )
            .order_by(Attempt.finished_at.desc())
            .first()
        )
        return latest

    def calculate_improvement(
        self,
        previous_attempt: Attempt,
        current_attempt: Attempt,
    ) -> ImprovementResult:
        """
        Calculate improvement metrics between two attempts.

        REQ: REQ-B-B5-2

        Args:
            previous_attempt: Earlier Attempt object
            current_attempt: Later Attempt object

        Returns:
            ImprovementResult with metrics

        Raises:
            ValueError: If attempts have no scores or grades

        """
        if not previous_attempt.final_score or not previous_attempt.final_grade:
            raise ValueError("Previous attempt missing score or grade")
        if not current_attempt.final_score or not current_attempt.final_grade:
            raise ValueError("Current attempt missing score or grade")

        # Calculate score change
        score_change: float = current_attempt.final_score - previous_attempt.final_score

        # Determine grade improvement
        grade_order: dict[str, int] = {
            "Beginner": 1,
            "Intermediate": 2,
            "Intermediate-Advanced": 3,
            "Advanced": 4,
            "Elite": 5,
        }
        previous_grade_rank: int = grade_order.get(previous_attempt.final_grade, 0)
        current_grade_rank: int = grade_order.get(current_attempt.final_grade, 0)
        grade_improved: bool = current_grade_rank > previous_grade_rank

        # Calculate time change
        previous_time: int = self._calculate_total_attempt_time(previous_attempt.id)
        current_time: int = self._calculate_total_attempt_time(current_attempt.id)
        time_change: int = current_time - previous_time

        return ImprovementResult(
            previous_score=previous_attempt.final_score,
            current_score=current_attempt.final_score,
            score_change=score_change,
            previous_grade=previous_attempt.final_grade,
            current_grade=current_attempt.final_grade,
            grade_improved=grade_improved,
            time_previous_seconds=previous_time,
            time_current_seconds=current_time,
            time_change_seconds=time_change,
            metrics_available=True,
        )

    def _calculate_total_attempt_time(self, attempt_id: str) -> int:
        """
        Calculate total time spent on an attempt across all rounds.

        Args:
            attempt_id: Attempt ID

        Returns:
            Total time in seconds

        """
        rounds: list[AttemptRound] = (
            self.session.query(AttemptRound).filter(AttemptRound.attempt_id == attempt_id).all()
        )
        return sum(r.time_spent_seconds for r in rounds)

    def get_previous_survey(self, user_id: int) -> UserProfileSurvey | None:
        """
        Get previous survey for pre-filling retry form.

        REQ: REQ-B-B5-4

        Performance: O(1) with index on (user_id, submitted_at DESC)

        Args:
            user_id: User ID

        Returns:
            Latest UserProfileSurvey or None if none exist

        """
        latest_survey: UserProfileSurvey | None = (
            self.session.query(UserProfileSurvey)
            .filter(UserProfileSurvey.user_id == user_id)
            .order_by(UserProfileSurvey.submitted_at.desc())
            .first()
        )
        return latest_survey

    def list_user_attempts(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[Attempt], int]:
        """
        Get paginated list of user's attempts with total count.

        REQ: REQ-B-B5-3

        Args:
            user_id: User ID
            limit: Number of records per page
            offset: Starting record offset

        Returns:
            Tuple of (attempts list, total count)

        """
        total_count: int = (
            self.session.query(Attempt)
            .filter(
                and_(
                    Attempt.user_id == user_id,
                    Attempt.status == "completed",
                )
            )
            .count()
        )

        attempts: list[Attempt] = (
            self.session.query(Attempt)
            .filter(
                and_(
                    Attempt.user_id == user_id,
                    Attempt.status == "completed",
                )
            )
            .order_by(Attempt.finished_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return attempts, total_count

    def get_attempt_details(self, attempt_id: str) -> dict:
        """
        Get full attempt data including rounds and answers.

        REQ: REQ-B-B5-1

        Args:
            attempt_id: Attempt ID

        Returns:
            Dictionary with attempt data, rounds, and answers

        """
        attempt: Attempt | None = self.session.query(Attempt).filter(Attempt.id == attempt_id).first()
        if not attempt:
            raise ValueError(f"Attempt with id {attempt_id} not found")

        rounds: list[AttemptRound] = (
            self.session.query(AttemptRound)
            .filter(AttemptRound.attempt_id == attempt_id)
            .order_by(AttemptRound.round_idx)
            .all()
        )

        return {
            "attempt_id": attempt.id,
            "user_id": attempt.user_id,
            "survey_id": attempt.survey_id,
            "test_type": attempt.test_type,
            "started_at": attempt.started_at.isoformat(),
            "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else None,
            "final_grade": attempt.final_grade,
            "final_score": attempt.final_score,
            "percentile": attempt.percentile,
            "rank": attempt.rank,
            "total_candidates": attempt.total_candidates,
            "status": attempt.status,
            "rounds": [
                {
                    "round_idx": r.round_idx,
                    "score": r.score,
                    "time_spent_seconds": r.time_spent_seconds,
                }
                for r in rounds
            ],
        }
