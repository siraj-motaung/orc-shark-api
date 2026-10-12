"""Pytest global configuration and database fixtures for PostgreSQL testing."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import Base
from app.main import app

TEST_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@localhost:5433/orc_shack_test"
)

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def setup_test_database() -> Generator[None, None, None]:
    """Create the test schema for tests that explicitly use the database."""

    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as error:
        pytest.skip(f"Test PostgreSQL database is unavailable: {error}")

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(setup_test_database: None) -> Generator[Session, None, None]:
    """Provide a transactional database session for each test."""

    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session: Session, ended_transaction) -> None:
        if ended_transaction.nested and not ended_transaction.parent.nested:
            session.begin_nested()

    try:
        yield session
    finally:
        event.remove(session, "after_transaction_end", restart_savepoint)
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI test client."""

    return TestClient(app)
