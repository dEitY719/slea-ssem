"""
Difficulty Keyword model for managing difficulty-specific keywords and concepts.

REQ: REQ-A-Mode1-Tool3
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.models.user import Base


class DifficultyKeyword(Base):
    """
    Difficulty Keyword model for storing difficulty-specific keywords and concepts.

    REQ: REQ-A-Mode1-Tool3

    Design principle:
    - Provides keywords, concepts, and examples for each difficulty level
    - Supports easy lookup by (difficulty, category) pair
    - Helps guide LLM-based question generation with contextual hints
    - Cached in memory for fast access

    Attributes:
        id: Primary key (UUID)
        difficulty: Difficulty level (1-10)
        category: Top-level category (technical, business, general)
        keywords: JSON array of keywords relevant to this difficulty
        concepts: JSON array of concept objects with definitions
        example_questions: JSON array of example questions
        is_active: Whether this record is active and searchable
        created_at: Record creation timestamp
        updated_at: Last update timestamp

    """

    __tablename__ = "difficulty_keywords"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    concepts: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    example_questions: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """Return string representation of DifficultyKeyword."""
        return f"<DifficultyKeyword(id='{self.id}', difficulty={self.difficulty}, category='{self.category}')>"
