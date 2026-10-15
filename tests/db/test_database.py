"""A module containing Tests for database session management and connectivity checks."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.db.database import check_database_connection, get_session


def test_check_database_connection_success() -> None:
    """Verify the health probe executes a trivial query and closes its connection."""

    # GIVEN: A database connection can be opened and used
    connection = MagicMock()
    connection_context = MagicMock()
    connection_context.__enter__.return_value = connection

    # WHEN: The connectivity check runs
    with patch(
        "app.db.database.engine.connect",
        return_value=connection_context,
    ) as connect:
        result = check_database_connection()

    # THEN: It executes SELECT 1 and closes the connection cleanly
    assert result is True
    connect.assert_called_once_with()
    connection.execute.assert_called_once()
    assert str(connection.execute.call_args.args[0]) == "SELECT 1"
    connection_context.__exit__.assert_called_once_with(None, None, None)


def test_check_database_connection_failure_logs_sqlalchemy_error(caplog) -> None:
    """Verify connection errors are reported as unhealthy and logged correctly."""

    # GIVEN: Opening a database connection raises a SQLAlchemy error
    error = OperationalError("SELECT 1", {}, Exception("database unavailable"))

    # WHEN: The connectivity check runs
    with patch(
        "app.db.database.engine.connect",
        side_effect=error,
    ):
        result = check_database_connection()

    # THEN: It reports unhealthy and logs the original exception
    assert result is False
    assert any(
        record.getMessage() == "Database connectivity check failed"
        and record.exc_info is not None
        for record in caplog.records
    )


def test_check_database_connection_query_failure_returns_false() -> None:
    """Verify query execution failures are also treated as an unhealthy database."""

    # GIVEN: The connection opens, but SELECT 1 fails
    connection = MagicMock()
    connection.execute.side_effect = OperationalError(
        "SELECT 1",
        {},
        Exception("query failed"),
    )
    connection_context = MagicMock()
    connection_context.__enter__.return_value = connection

    # WHEN: The connectivity check runs
    with patch(
        "app.db.database.engine.connect",
        return_value=connection_context,
    ):
        result = check_database_connection()

    # THEN: It reports unhealthy and closes the connection
    assert result is False
    connection_context.__exit__.assert_called_once()


def test_check_database_connection_does_not_hide_unexpected_errors() -> None:
    """Verify programming errors are not incorrectly reported as DB outages."""

    # GIVEN: Opening a connection raises a non-SQLAlchemy programming error
    # WHEN: The connectivity check runs
    with (
        patch(
            "app.db.database.engine.connect",
            side_effect=RuntimeError("unexpected failure"),
        ),
        pytest.raises(RuntimeError, match="unexpected failure"),
    ):
        check_database_connection()

    # THEN: The unexpected error is surfaced to the caller

def test_get_session_closes_session_after_normal_completion() -> None:
    """Verify a session is closed when the request completes normally."""

    # GIVEN: A session factory returns a session
    session = MagicMock()

    # WHEN: The dependency generator completes normally
    with patch("app.db.database.SessionLocal", return_value=session):
        session_generator = get_session()

        assert next(session_generator) is session
        with pytest.raises(StopIteration):
            next(session_generator)

    # THEN: The session is closed without an unnecessary rollback
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


def test_get_session_rolls_back_and_closes_after_request_error() -> None:
    """Verify request errors trigger rollback and session closure."""

    # GIVEN: A session has been yielded to a request
    session = MagicMock()
    request_error = RuntimeError("request failed")

    with patch("app.db.database.SessionLocal", return_value=session):
        session_generator = get_session()
        assert next(session_generator) is session

        # WHEN: The request raises an error
        with pytest.raises(RuntimeError, match="request failed"):
            session_generator.throw(request_error)

    # THEN: The session is rolled back, closed, and the original error is re-raised
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()
