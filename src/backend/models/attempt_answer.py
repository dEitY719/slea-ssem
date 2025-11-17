"""
Attempt answer model for storing user responses to questions.

REQ: REQ-B-B2-Plus, REQ-B-B3-Score
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.models.user import Base


class AttemptAnswer(Base):
    """
    Attempt answer model for storing user responses to test questions.

    REQ: REQ-B-B2-Plus, REQ-B-B3-Score

    Design principle:
    - One record per question answered by user
    - Stores user response, correctness, and scoring metadata
    - Used for calculating TestResult score
    - Used for identifying weak categories (wrong answers by category)
    - Supports autosave functionality (REQ-B-B2-Plus)

    Attributes:
        id: Primary key (UUID)
        session_id: Foreign key to test_sessions
        question_id: Foreign key to questions
        user_answer: User's response (text, JSON, or serialized)
        is_correct: Boolean whether answer is correct
        score: Score earned (0-100, for partial credit on short answer)
        response_time_ms: Time spent answering in milliseconds
        saved_at: When answer was saved (for autosave tracking)
        created_at: Initial creation timestamp

    """

    __tablename__ = "attempt_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("test_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_answer: Mapped[str | dict] = mapped_column(JSON, nullable=False)
    is_correct: Mapped[bool] = mapped_column(default=False, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)  # Optional
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)  # For autosave
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """Return string representation of AttemptAnswer."""
        return (
            f"<AttemptAnswer(id='{self.id}', question_id='{self.question_id}', "
            f"is_correct={self.is_correct}, score={self.score})>"
        )
