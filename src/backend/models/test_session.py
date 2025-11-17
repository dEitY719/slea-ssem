"""
Test session model for managing test attempts and rounds.

REQ: REQ-B-B2-Gen, REQ-B-B2-Adapt, REQ-B-B2-Plus, REQ-B-B3-Score
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.models.user import Base


class TestSession(Base):
    """
    Test session model for managing user test attempts.

    REQ: REQ-B-B2-Gen, REQ-B-B2-Adapt, REQ-B-B2-Plus, REQ-B-B3-Score

    Design principle:
    - One session per user test attempt (each attempt creates new session)
    - Tracks round (1 or 2) and test status (in_progress, completed, paused)
    - Links to UserProfileSurvey to know which profile was used
    - Supports time-limited testing with pause/resume capability

    Attributes:
        id: Primary key (UUID)
        user_id: Foreign key to users table
        survey_id: Foreign key to user_profile_surveys (which profile was used)
        round: Current round (1=1차, 2=2차)
        status: Session status (in_progress, completed, paused)
        time_limit_ms: Time limit in milliseconds (default 1200000ms = 20 minutes)
        started_at: When the test was started (nullable until first question answered)
        paused_at: When the test was paused (nullable, set on timeout or manual pause)
        created_at: Session creation timestamp
        updated_at: Last update timestamp

    """

    __test__ = False

    __tablename__ = "test_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    survey_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user_profile_surveys.id", ondelete="CASCADE"),
        nullable=False,
    )
    round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        Enum("in_progress", "completed", "paused", name="session_status_enum"),
        nullable=False,
        default="in_progress",
    )
    time_limit_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1200000,  # 20 minutes in milliseconds
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    paused_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """Return string representation of TestSession."""
        return f"<TestSession(id='{self.id}', user_id={self.user_id}, round={self.round}, status='{self.status}')>"
