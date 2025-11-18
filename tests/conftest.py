"""Pytest configuration and shared fixtures."""

import os
import sys
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from dotenv import load_dotenv

# Add project root to sys.path for proper imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Note: Do NOT mock langgraph/langchain modules here as it breaks imports
# Let pytest skip agent tests if dependencies are missing instead


def pytest_configure(config):
    """Configure pytest to ignore agent tests if dependencies are missing."""
    # Check if langgraph is available
    try:
        import langgraph  # noqa: F401
        import langchain_core  # noqa: F401
    except (ImportError, ModuleNotFoundError):
        # Add --ignore option for agent tests
        config.option.ignore_glob = ["tests/agent/*"]


from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from src.backend.database import get_db
from src.backend.models.attempt import Attempt
from src.backend.models.attempt_answer import AttemptAnswer
from src.backend.models.attempt_round import AttemptRound
from src.backend.models.question import Question
from src.backend.models.test_result import TestResult
from src.backend.models.test_session import TestSession
from src.backend.models.user import Base, User
from src.backend.models.user_profile import UserProfileSurvey

# Load .env to get TEST_DATABASE_URL
load_dotenv()


@pytest.fixture(scope="function")
def db_engine() -> Generator[Engine, None, None]:
    """
    Create PostgreSQL test database for testing.

    Uses TEST_DATABASE_URL from .env file.
    Creates and drops all tables for test isolation.

    Yields:
        SQLAlchemy engine connected to test database

    """
    test_database_url = os.getenv("TEST_DATABASE_URL")
    if not test_database_url:
        raise ValueError(
            "TEST_DATABASE_URL environment variable is not set. "
            "Please set it in .env file for testing."
        )

    # Convert async PostgreSQL URL to sync if needed
    # postgresql+asyncpg:// → postgresql://
    db_url_for_sync = test_database_url.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(db_url_for_sync)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Drop all tables after test
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
    # Explicitly drop and recreate tables for each test
    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)

    # Reset all sequences to 1 for PostgreSQL
    with db_engine.connect() as conn:
        # Get all table names
        db_inspector = inspect(db_engine)
        for table_name in db_inspector.get_table_names():
            # Reset sequence for each table (assuming id is the primary key)
            try:
                conn.execute(text(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1"))
            except Exception:
                # Skip if sequence doesn't exist
                pass
        conn.commit()

    session_local = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = session_local()
    yield session
    session.close()


@pytest.fixture(scope="function")
def authenticated_user(db_session: Session) -> User:
    """
    Create a test user for authenticated requests.

    Args:
        db_session: Database session

    Returns:
        Test user instance

    """
    user = User(
        # Don't explicitly set id; let the database auto-generate it
        knox_id="test_jwt_user",
        name="JWT Test User",
        dept="Test Dept",
        business_unit="Test BU",
        email="jwt_test@samsung.com",
        nickname="jwt_test_user",
        last_login=datetime.now(UTC),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def client(db_session: Session, authenticated_user: User) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with mocked database.

    Args:
        db_session: Database session from fixture
        authenticated_user: Test user for authenticated requests

    Yields:
        TestClient for making HTTP requests

    """
    # Lazy import routers to avoid import errors during conftest loading
    from src.backend.api.auth import router as auth_router
    from src.backend.api.profile import router as profile_router
    from src.backend.api.questions import router as questions_router
    from src.backend.api.survey import router as survey_router
    from src.backend.utils.auth import get_current_user

    app = FastAPI()
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(profile_router, prefix="/profile", tags=["profile"])
    app.include_router(survey_router, prefix="/survey", tags=["survey"])
    app.include_router(questions_router, prefix="/questions", tags=["questions"])

    # Override database dependency to use the test session
    def override_get_db() -> Generator[Session, None, None]:
        # Flush any pending changes from previous requests
        db_session.commit()
        yield db_session

    # Override JWT authentication to return test user
    def override_get_current_user() -> User:
        return authenticated_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield TestClient(app)


@pytest.fixture(scope="function")
def user_fixture(db_session: Session) -> User:
    """
    Create a test user in the database.

    Uses auto-increment ID for general test use.
    For JWT/authenticated tests, use authenticated_user fixture instead.

    Args:
        db_session: Database session

    Returns:
        User instance with auto-generated ID

    """
    user = User(
        knox_id="test_user_001",
        name="Test User",
        dept="Test Dept",
        business_unit="Test BU",
        email="test@samsung.com",
        nickname="alice_test",
        last_login=datetime.now(UTC),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def user_profile_survey_fixture(db_session: Session, authenticated_user: User) -> UserProfileSurvey:
    """
    Create a test user profile survey record.

    Args:
        db_session: Database session
        authenticated_user: Authenticated test user

    Returns:
        UserProfileSurvey instance

    """
    survey = UserProfileSurvey(
        id="survey_001",
        user_id=authenticated_user.id,
        self_level="Intermediate",
        years_experience=3,
        job_role="Senior Engineer",
        duty="ML Model Development",
        interests=["LLM", "RAG"],
        submitted_at=datetime.now(UTC),
    )
    db_session.add(survey)
    db_session.commit()
    db_session.refresh(survey)
    return survey


@pytest.fixture(scope="function")
def test_session_round1_fixture(
    db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
) -> TestSession:
    """
    Create a Round 1 test session for testing adaptive logic.

    Args:
        db_session: Database session
        authenticated_user: Authenticated test user (user_id=1)
        user_profile_survey_fixture: Survey fixture

    Returns:
        TestSession record for Round 1

    """
    session = TestSession(
        id=str(uuid4()),
        user_id=authenticated_user.id,
        survey_id=user_profile_survey_fixture.id,
        round=1,
        status="completed",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture(scope="function")
def test_result_low_score(db_session: Session, test_session_round1_fixture: TestSession) -> TestResult:
    """Create TestResult with low score (30%) and weak categories."""
    result = TestResult(
        session_id=test_session_round1_fixture.id,
        round=1,
        score=30.0,
        total_points=30,
        correct_count=1,
        total_count=5,
        wrong_categories={"RAG": 2, "Robotics": 1, "LLM": 1},
    )
    db_session.add(result)
    db_session.commit()
    return result


@pytest.fixture(scope="function")
def test_result_medium_score(db_session: Session, test_session_round1_fixture: TestSession) -> TestResult:
    """Create TestResult with medium score (55%) and some weak categories."""
    result = TestResult(
        session_id=test_session_round1_fixture.id,
        round=1,
        score=55.0,
        total_points=55,
        correct_count=3,
        total_count=5,
        wrong_categories={"RAG": 2},
    )
    db_session.add(result)
    db_session.commit()
    return result


@pytest.fixture(scope="function")
def test_result_high_score(db_session: Session, test_session_round1_fixture: TestSession) -> TestResult:
    """Create TestResult with high score (80%) and minimal weak areas."""
    result = TestResult(
        session_id=test_session_round1_fixture.id,
        round=1,
        score=80.0,
        total_points=80,
        correct_count=4,
        total_count=5,
        wrong_categories={"Robotics": 1},
    )
    db_session.add(result)
    db_session.commit()
    return result


@pytest.fixture(scope="function")
def attempt_answers_for_session(db_session: Session, test_session_round1_fixture: TestSession) -> list[AttemptAnswer]:
    """Create attempt answer records for a test session."""
    # Create 5 questions for the session
    questions = []
    for idx in range(5):
        q = Question(
            id=str(uuid4()),
            session_id=test_session_round1_fixture.id,
            item_type="multiple_choice",
            stem=f"Test question {idx + 1}",
            choices=["A", "B", "C", "D"],
            answer_schema={"correct_key": "A", "explanation": "Test"},
            difficulty=5,
            category=["LLM", "RAG", "Robotics"][idx % 3],
            round=1,
        )
        db_session.add(q)
        questions.append(q)

    db_session.commit()

    # Create attempt answers with expected scoring pattern
    # Pattern: 1 correct (LLM), 4 wrong (RAG, RAG, Robotics, LLM)
    # Note: Initially set to unscored state (is_correct=False, score=0)
    # so that _score_all_unscored_answers() will process them
    answers = []
    answer_data = [
        (questions[0], {"selected_key": "A"}),  # LLM: will be correct (correct_key is "A")
        (questions[1], {"selected_key": "B"}),  # RAG: will be wrong (correct_key is "A")
        (questions[2], {"selected_key": "B"}),  # Robotics: will be wrong (correct_key is "A")
        (questions[3], {"selected_key": "B"}),  # LLM: will be wrong (correct_key is "A")
        (questions[4], {"selected_key": "B"}),  # RAG: will be wrong (correct_key is "A")
    ]

    for question, user_answer in answer_data:
        answer = AttemptAnswer(
            session_id=test_session_round1_fixture.id,
            question_id=question.id,
            user_answer=user_answer,
            is_correct=False,  # Default autosave state
            score=0.0,  # Default autosave state
            response_time_ms=5000,
        )
        db_session.add(answer)
        answers.append(answer)

    db_session.commit()
    return answers


@pytest.fixture(scope="function")
def test_session_in_progress(
    db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
) -> TestSession:
    """
    Create an in-progress test session for autosave testing.

    Args:
        db_session: Database session
        authenticated_user: Authenticated test user (user_id=1)
        user_profile_survey_fixture: Survey fixture

    Returns:
        TestSession record with status='in_progress'

    """
    session = TestSession(
        id=str(uuid4()),
        user_id=authenticated_user.id,
        survey_id=user_profile_survey_fixture.id,
        round=1,
        status="in_progress",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


# ============================================================================
# RANKING SERVICE TEST FIXTURES (REQ-B-B4)
# ============================================================================


@pytest.fixture(scope="function")
def create_multiple_users(db_session: Session) -> callable:
    """
    Fixture factory to create multiple test users.

    Returns:
        Callable that creates n users and returns them

    """

    def _create_users(count: int) -> list[User]:
        users = []
        for i in range(count):
            user = User(
                knox_id=f"test_user_{i:03d}",
                name=f"User {i}",
                dept="Test Dept",
                business_unit="Test BU",
                email=f"user{i}@samsung.com",
                nickname=f"user_{i:03d}",
                last_login=datetime.now(UTC),
            )
            db_session.add(user)
            users.append(user)

        db_session.commit()
        return users

    return _create_users


@pytest.fixture(scope="function")
def create_survey_for_user(db_session: Session) -> callable:
    """
    Fixture factory to create survey for a user.

    Returns:
        Callable that creates survey for a given user

    """

    def _create_survey(user_id: int) -> UserProfileSurvey:
        survey = UserProfileSurvey(
            id=str(uuid4()),
            user_id=user_id,
            self_level="Intermediate",
            years_experience=3,
            job_role="Engineer",
            duty="Development",
            interests=["LLM", "RAG"],
            submitted_at=datetime.now(UTC),
        )
        db_session.add(survey)
        db_session.commit()
        db_session.refresh(survey)
        return survey

    return _create_survey


@pytest.fixture(scope="function")
def create_test_session_with_result(db_session: Session) -> callable:
    """
    Fixture factory to create test session with result.

    Returns:
        Callable that creates session+result with given parameters

    """

    def _create_session(
        user_id: int, survey_id: str, score: float, round_num: int = 1, days_ago: int = 0
    ) -> tuple[TestSession, TestResult]:
        session_created_at = datetime.now(UTC) - timedelta(days=days_ago)

        session = TestSession(
            id=str(uuid4()),
            user_id=user_id,
            survey_id=survey_id,
            round=round_num,
            status="completed",
            created_at=session_created_at,
        )
        db_session.add(session)
        db_session.flush()

        # Calculate correct count based on score
        correct_count = int((score / 100.0) * 5)
        total_count = 5

        result = TestResult(
            session_id=session.id,
            round=round_num,
            score=score,
            total_points=int(score),
            correct_count=correct_count,
            total_count=total_count,
            wrong_categories={"RAG": max(0, total_count - correct_count)},
            created_at=session_created_at,
        )
        db_session.add(result)
        db_session.commit()

        return session, result

    return _create_session


@pytest.fixture(scope="function")
def create_attempt(db_session: Session) -> callable:
    """
    Fixture factory to create Attempt record for history testing.

    Returns:
        Callable that creates Attempt with given parameters
    """

    def _create(
        user_id: int,
        survey_id: str,
        test_type: str = "level_test",
        status: str = "completed",
        final_grade: str = "Intermediate",
        final_score: float = 65.0,
        days_ago: int = 0,
    ) -> Attempt:
        started_at = datetime.now(UTC) - timedelta(days=days_ago)
        finished_at = started_at + timedelta(minutes=30)

        attempt = Attempt(
            user_id=user_id,
            survey_id=survey_id,
            test_type=test_type,
            started_at=started_at,
            finished_at=finished_at if status == "completed" else None,
            final_grade=final_grade if status == "completed" else None,
            final_score=final_score if status == "completed" else None,
            percentile=45 if status == "completed" else None,
            rank=250 if status == "completed" else None,
            total_candidates=500 if status == "completed" else None,
            status=status,
        )
        db_session.add(attempt)
        db_session.commit()
        db_session.refresh(attempt)
        return attempt

    return _create


@pytest.fixture(scope="function")
def create_attempt_round(db_session: Session) -> callable:
    """
    Fixture factory to create AttemptRound record.

    Returns:
        Callable that creates AttemptRound with given parameters
    """

    def _create(
        attempt_id: str,
        round_idx: int = 1,
        score: float = 75.0,
        time_spent_seconds: int = 1800,
    ) -> AttemptRound:
        round_record = AttemptRound(
            attempt_id=attempt_id,
            round_idx=round_idx,
            score=score,
            time_spent_seconds=time_spent_seconds,
        )
        db_session.add(round_record)
        db_session.commit()
        db_session.refresh(round_record)
        return round_record

    return _create


# ============================================================================
# CONTENT VALIDATOR TEST FIXTURES (REQ-B-B6-2)
# ============================================================================


@pytest.fixture(scope="function")
def question_factory(db_session: Session, test_session_round1_fixture: TestSession) -> callable:
    """
    Fixture factory to create Question record for content validator testing.

    Returns:
        Callable that creates Question with given parameters
    """

    def _create(
        stem: str = "What is AI?",
        choices: list[str] | None = None,
        item_type: str = "multiple_choice",
        difficulty: int = 5,
        category: str = "LLM",
        round: int = 1,
        answer_schema: dict | None = None,
    ) -> Question:
        if choices is None:
            choices = ["Option A", "Option B", "Option C"]
        if answer_schema is None:
            answer_schema = {
                "correct_key": "A",
                "explanation": "This is the correct answer.",
            }

        question = Question(
            id=str(uuid4()),
            session_id=test_session_round1_fixture.id,
            item_type=item_type,
            stem=stem,
            choices=choices,
            answer_schema=answer_schema,
            difficulty=difficulty,
            category=category,
            round=round,
        )
        db_session.add(question)
        db_session.commit()
        db_session.refresh(question)
        return question

    return _create
