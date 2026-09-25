import logging
from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verifies connections before issuing queries
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""


def get_session() -> Iterator[Session]:
    """
    Dependency that yields a database session per request
    and guarantees closure upon completion.
    """

    db_session = SessionLocal()

    try:
        yield db_session
    except Exception:
        db_session.rollback()
        raise
    finally:
        db_session.close()


def check_database_connection() -> bool:
    """Ping the database to verify connectivity."""

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True

    except Exception:
        logger.exception("Database connectivity check failed: %s")
        return False
