"""Database configuration and session management."""

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

# Load .env file for development (not present in Docker)
# In Docker, environment variables are injected by docker-compose.yml
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)

# Database connection string from environment (must be set)
DATABASE_URL: str = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. Please set it to a PostgreSQL connection string in .env file"
    )

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


def get_db() -> Generator[Session]:
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
