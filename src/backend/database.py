"""Database configuration and session management."""

import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

# Database connection string from environment or default to SQLite
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Convert async PostgreSQL URL to sync if needed
# postgresql+asyncpg:// → postgresql://
db_url_for_sync = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Create engine
engine: Engine = create_engine(
    db_url_for_sync,
    connect_args={"check_same_thread": False} if "sqlite" in db_url_for_sync else {},
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
    # Import all models to register them with SQLAlchemy
    import src.backend.models  # noqa: F401
    from src.backend.models.user import Base  # noqa: F401

    Base.metadata.create_all(bind=engine)
