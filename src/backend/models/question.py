"""
Question model for managing test questions.

REQ: REQ-B-B2-Gen, REQ-B-B2-Adapt, REQ-B-B3-Score
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.models.user import Base


class Question(Base):
    """
    Question model for storing generated test questions.

    REQ: REQ-B-B2-Gen, REQ-B-B2-Adapt, REQ-B-B3-Score

    Design principle:
    - One question per test session and round
    - Stores all question metadata: type, stem, choices, answer info, difficulty
    - Supports multiple question types: multiple_choice, true_false, short_answer
    - Links to TestSession to track which test round this question belongs to

    Attributes:
        id: Primary key (UUID)
        session_id: Foreign key to test_sessions
        item_type: Question type (multiple_choice, true_false, short_answer)
        stem: Question content/text
        choices: JSON array of choices (for multiple_choice/true_false)
        answer_schema: JSON object with answer info and explanation
        difficulty: Difficulty level (1~10)
        category: Category/topic of question (AI, LLM, RAG, Semiconductor, etc.)
        round: Which round (1=1차, 2=2차)
        created_at: Question creation timestamp

    """

    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("test_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(
        Enum("multiple_choice", "true_false", "short_answer", name="item_type_enum"),
        nullable=False,
    )
    stem: Mapped[str] = mapped_column(String(2000), nullable=False)
    choices: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    answer_schema: Mapped[dict] = mapped_column(JSON, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """Return string representation of Question."""
        return (
            f"<Question(id='{self.id}', session_id='{self.session_id}', "
            f"item_type='{self.item_type}', difficulty={self.difficulty})>"
        )
