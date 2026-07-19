"""SQLAlchemy engine and session factory.

Design decision: Synchronous sessions chosen over async for simplicity.
Trade-offs:
  - Pros: simpler code, easier debugging, compatible with all SQLAlchemy features
  - Cons: blocks event loop if used with async FastAPI handlers
For async migration: replace with AsyncSession + create_async_engine.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import get_settings

settings = get_settings()

# NOTE: pool_pre_ping=True detects stale connections and reconnects automatically
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
