"""User profile survey model for self-assessment data."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.models.user import Base


class UserProfileSurvey(Base):
    """
    User profile survey model for storing self-assessment data.

    REQ: REQ-B-A2-Edit-3

    Design principle:
    - Creates NEW record on each survey submission (never updates existing)
    - Maintains history of all survey submissions
    - Latest survey identified by submitted_at DESC order
    - Index on (user_id, submitted_at DESC) for efficient latest lookup

    Self-level mapping:
    - Beginner: 입문 - 기초 개념 학습 중
    - Intermediate: 초급 - 기본 업무 수행 가능
    - Intermediate-Advanced: 중급 - 독립적으로 업무 수행
    - Advanced: 고급 - 복잡한 문제 해결 가능
    - Elite: 전문가 - 다른 사람을 지도 가능

    Attributes:
        id: Primary key (UUID)
        user_id: Foreign key to users table
        self_level: Self-assessed proficiency level (Beginner/Intermediate/Intermediate-Advanced/Advanced/Elite)
        years_experience: Years of experience (0-60)
        job_role: Job role/title
        duty: Main job duties/responsibilities
        interests: JSON array of interest categories (e.g., ["LLM", "RAG"])
        submitted_at: Timestamp when survey was submitted

    """

    __tablename__ = "user_profile_surveys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    self_level: Mapped[str | None] = mapped_column(
        Enum(
            "Beginner",
            "Intermediate",
            "Intermediate-Advanced",
            "Advanced",
            "Elite",
            name="self_level_enum",
        ),
        nullable=True,
    )
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duty: Mapped[str | None] = mapped_column(String(500), nullable=True)
    interests: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    __table_args__ = (Index("ix_user_id_submitted_at", "user_id", "submitted_at"),)

    def __repr__(self) -> str:
        """Return string representation of UserProfileSurvey."""
        return (
            f"<UserProfileSurvey(id='{self.id}', user_id={self.user_id}, "
            f"self_level='{self.self_level}', submitted_at={self.submitted_at})>"
        )
