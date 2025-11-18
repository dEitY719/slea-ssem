"""
Test result model for storing round scores and analysis.

REQ: REQ-B-B2-Adapt, REQ-B-B3-Score
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.models.user import Base


class TestResult(Base):
    """
    Test result model for storing round scores and category analysis.

    REQ: REQ-B-B2-Adapt, REQ-B-B3-Score

    Design principle:
    - One result record per test session round
    - Stores score (0-100%), correct/wrong counts, and category breakdown
    - Used for adaptive difficulty calculation in Round 2
    - Used for ranking calculation after all rounds complete

    Attributes:
        id: Primary key (UUID)
        session_id: Foreign key to test_sessions
        round: Which round (1, 2, or 3)
        score: Percentage score (0-100)
        total_points: Total points earned
        correct_count: Number of correct answers
        total_count: Total number of questions
        wrong_categories: JSON dict with category -> wrong count mapping
        created_at: Result recording timestamp

    """

    __test__ = False

    __tablename__ = "test_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("test_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100 percentage
    total_points: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False)
    wrong_categories: Mapped[dict] = mapped_column(JSON, nullable=True)  # {"LLM": 1, "RAG": 2}
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """Return string representation of TestResult."""
        return f"<TestResult(id='{self.id}', session_id='{self.session_id}', round={self.round}, score={self.score}%)>"
