"""
AttemptRound model for storing individual round scores within an attempt.

REQ: REQ-B-B5-1, REQ-B-B5-2
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.models.user import Base


class AttemptRound(Base):
    """
    Individual round within an attempt (test history).

    REQ: REQ-B-B5-1, REQ-B-B5-2

    Design principle:
    - One record per round in an attempt
    - Stores round-specific score and time spent
    - Links to Attempt (parent) and AttemptAnswers (children)

    Attributes:
        id: Primary key (UUID)
        attempt_id: Foreign key to attempts table
        round_idx: Round number (1, 2, etc.)
        score: Score for this round (0-100)
        time_spent_seconds: How long user took on this round
        created_at: When this round was created

    """

    __tablename__ = "attempt_rounds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    attempt_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("attempts.id"),
        nullable=False,
        index=True,
    )
    round_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)  # 0-100
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )

    # Indexes
    __table_args__ = (Index("idx_round_attempt_idx", "attempt_id", "round_idx"),)

    def __repr__(self) -> str:
        """Return string representation of AttemptRound."""
        return (
            f"<AttemptRound(id='{self.id}', attempt_id='{self.attempt_id}', "
            f"round={self.round_idx}, score={self.score})>"
        )
