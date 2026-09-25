"""A module containing tests for database connection."""

from unittest.mock import patch

from app.db.database import check_database_connection


def test_check_database_connection_success():
    # GIVEN: The database is availabe

    # WHEN: We call the `check_database_connection()` function.
    result = check_database_connection()

    # THEN: We expect the database connectivity check to succeed
    assert result is True


def test_check_database_connection_failure():

    # GIVEN: The database is availabe

    with patch(
        "app.db.database.engine.connect", side_effect=Exception("Database Down")
    ):
        # WHEN: We call the `check_database_connection()` function.
        result = check_database_connection()

        # THEN: We expect the database connectivity check to fail
        assert result is False
