from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models.base import Base
from app.utils.logging import get_logger

logger = get_logger("app.database")
settings = get_settings()

# Configure SQLAlchemy 2.x Engine with connection pooling and fast connect timeout for resilience
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
    connect_args={"connect_timeout": 2} if "psycopg" in settings.DATABASE_URL else {},
)

# Session factory for generating database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a transactional database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Verify if the database is currently reachable without throwing unhandled exceptions."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connectivity check failed: {e}")
        return False
