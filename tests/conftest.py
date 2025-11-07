"""Pytest configuration and shared fixtures."""

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.backend.api.auth import router as auth_router
from src.backend.api.profile import router as profile_router
from src.backend.database import get_db
from src.backend.models.user import Base, User


@pytest.fixture(scope="function")
def db_engine(tmp_path: Path) -> Generator[Engine, None, None]:
    """
    Create file-based SQLite database for testing.

    Args:
        tmp_path: Temporary directory path from pytest

    Yields:
        SQLAlchemy engine

    """
    # Use file-based SQLite instead of in-memory to avoid per-connection isolation
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:  # noqa: ANN401
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """
    Create a new database session for each test.

    Args:
        db_engine: SQLAlchemy engine fixture

    Yields:
        SQLAlchemy session

    """
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = session_local()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with mocked database.

    Args:
        db_session: Database session from fixture

    Yields:
        TestClient for making HTTP requests

    """
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(profile_router)

    # Override database dependency to use the test session
    def override_get_db() -> Generator[Session, None, None]:
        # Flush any pending changes from previous requests
        db_session.commit()
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest.fixture(scope="function")
def user_fixture(db_session: Session) -> User:
    """
    Create a test user in the database.

    Args:
        db_session: Database session

    Returns:
        User instance

    """
    from datetime import datetime

    user = User(
        knox_id="test_user_001",
        name="Test User",
        dept="Test Dept",
        business_unit="Test BU",
        email="test@samsung.com",
        nickname="alice_test",
        last_login=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
