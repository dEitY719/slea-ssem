"""
Answer explanation model for storing question explanations with reference links.

REQ: REQ-B-B3-Explain
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.models.user import Base


class AnswerExplanation(Base):
    """
    Answer explanation model for storing generated explanations.

    REQ: REQ-B-B3-Explain-1

    Design principle:
    - One explanation per question (cached and reused across users)
    - Optional: Can be linked to specific attempt_answer_id for tracking user attempts
    - Stores explanation text and reference links
    - Used for providing learning feedback after scoring

    Attributes:
        id: Primary key (UUID)
        question_id: Foreign key to questions
        attempt_answer_id: Optional FK to attempt_answers for audit trail
        explanation_text: Explanation content (≥500 chars)
        reference_links: List of reference links [{title, url}, ...] (≥3)
        is_correct: Whether explanation is for correct or incorrect answer
        created_at: When explanation was generated
        updated_at: Last update timestamp (for cache invalidation)

    """

    __tablename__ = "answer_explanations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_answer_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("attempt_answers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    explanation_text: Mapped[str] = mapped_column(String(5000), nullable=False)
    reference_links: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    is_correct: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """Return string representation of AnswerExplanation."""
        return (
            f"<AnswerExplanation(id='{self.id}', question_id='{self.question_id}', "
            f"is_correct={self.is_correct}, links={len(self.reference_links)})>"
        )
