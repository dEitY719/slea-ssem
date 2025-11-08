"""
Attempt model for storing test attempt history.

REQ: REQ-B-B5-1, REQ-B-B5-2, REQ-B-B5-3, REQ-B-B5-4, REQ-B-B5-5
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.models.user import Base


class Attempt(Base):
    """
    Test attempt history record - permanent record of a completed test session.

    REQ: REQ-B-B5-1, REQ-B-B5-2, REQ-B-B5-3, REQ-B-B5-4, REQ-B-B5-5

    Design principle:
    - One record per test attempt (single or multi-round)
    - Linked to UserProfileSurvey for survey snapshot
    - Stores final grade, score, percentile, rank
    - Supports retry/history tracking
    - Separate from TestSession (which tracks active test state)

    Attributes:
        id: Primary key (UUID)
        user_id: Foreign key to users table (INTEGER, not UUID)
        survey_id: Foreign key to user_profile_surveys (UUID)
        test_type: Type of test ('level_test', 'fun_quiz')
        started_at: When attempt started
        finished_at: When attempt completed (NULL if in_progress)
        final_grade: Final grade (Beginner, Intermediate, ..., Elite) - NULL if in_progress
        final_score: Final score 0-100 - NULL if in_progress
        percentile: Percentile rank (0-100) - NULL for fun_quiz
        rank: Absolute rank - NULL for fun_quiz
        total_candidates: Total users in cohort - NULL for fun_quiz
        status: 'in_progress', 'completed', 'abandoned'
        created_at: Record creation timestamp

    """

    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    survey_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user_profile_surveys.id"),
        nullable=False,
        index=True,
    )
    test_type: Mapped[str] = mapped_column(String(50), nullable=False, default="level_test")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Results (NULL until completed)
    final_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    final_score: Mapped[float | None] = mapped_column(nullable=True)
    percentile: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_candidates: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress"
    )  # in_progress, completed, abandoned

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )

    # Indexes for queries
    __table_args__ = (
        Index("idx_attempt_user_finished", "user_id", "finished_at"),
        Index("idx_attempt_type_finished", "test_type", "finished_at"),
    )

    def __repr__(self) -> str:
        """Return string representation of Attempt."""
        return f"<Attempt(id='{self.id}', user_id={self.user_id}, grade='{self.final_grade}', status='{self.status}')>"
