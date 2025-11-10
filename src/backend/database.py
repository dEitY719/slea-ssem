"""Database configuration and session management."""

from collections.abc import Generator

# ✅ 비동기 전용으로 바꿔
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Database connection string (SQLite for MVP, configurable via env)
DATABASE_URL: str = "sqlite:///./test.db"

# Create engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database session.

    Yields:
        SQLAlchemy Session instance

    Example:
        >>> async def my_route(db: Session = Depends(get_db)):
        ...     user = db.query(User).first()

    """
    async with SessionLocal() as db:
        yield db


def init_db() -> None:
    assert isinstance(engine, AsyncEngine)
    async with engine.begin() as conn:
        # 동기 메타데이터 DDL을 비동기 컨텍스트에서 실행
        await conn.run_sync(Base.metadata.create_all)
