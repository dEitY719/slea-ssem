"""User model for Samsung AD authentication."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class User(Base):
    """
    User model for storing Samsung AD authenticated users.

    Attributes:
        id: Primary key
        knox_id: Unique Samsung Knox ID (AD identifier)
        name: User's full name
        dept: Department
        business_unit: Business unit
        email: Email address
        nickname: User's chosen nickname (UNIQUE, set during REQ-B-A2)
        privacy_consent: User's privacy consent status (default: False, set during REQ-B-A3)
        consent_at: Timestamp of privacy consent (nullable, set when user grants consent)
        last_login: Timestamp of last login
        created_at: Account creation timestamp
        updated_at: Timestamp of last update

    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    knox_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dept: Mapped[str] = mapped_column(String(255), nullable=False)
    business_unit: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True, index=True)
    privacy_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        """Return string representation of User."""
        nickname_str = f", nickname='{self.nickname}'" if self.nickname else ""
        return f"<User(id={self.id}, knox_id='{self.knox_id}', name='{self.name}'{nickname_str})>"
