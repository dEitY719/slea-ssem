"""User model for Samsung AD authentication."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

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
        last_login: Timestamp of last login
        created_at: Account creation timestamp

    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    knox_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dept: Mapped[str] = mapped_column(String(255), nullable=False)
    business_unit: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        """Return string representation of User."""
        return f"<User(id={self.id}, knox_id='{self.knox_id}', name='{self.name}')>"
