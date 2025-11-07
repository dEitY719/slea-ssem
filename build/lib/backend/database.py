"""Database configuration and session management."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

# Database connection string (SQLite for MVP, configurable via env)
DATABASE_URL: str = "sqlite:///./test.db"

# Create engine
engine: Engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database session.

    Yields:
        SQLAlchemy Session instance

    Example:
        >>> async def my_route(db: Session = Depends(get_db)):
        ...     user = db.query(User).first()

    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database and create all tables."""
    from src.backend.models.user import Base

    Base.metadata.create_all(bind=engine)
