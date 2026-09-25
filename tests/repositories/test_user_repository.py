"""Unit tests for user database repository operations."""

import pytest
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories import user_repository


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create and persist a baseline user for repository tests."""

    user = User(
        name="Siraj",
        email="siraj@motaung.com",
        password_hash="argon2_hashed_secret_key",
        role=UserRole.CUSTOMER,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_create_user_persists_and_returns_user(db_session: Session) -> None:
    """Verify create_user saves a new user record and returns the refreshed entity."""

    # GIVEN: An unpersisted User model instance
    user = User(
        name="Nkosi Zwane",
        email="nkosi@zwane.com",
        password_hash="argon2_hashed_admin_key",
        role=UserRole.ADMIN,
    )

    # WHEN: Executing create_user
    created = user_repository.create_user(db_session, user)

    # THEN: The returned user has a generated ID and matches input fields
    assert created.id is not None
    assert created.name == "Nkosi Zwane"
    assert created.email == "nkosi@zwane.com"
    assert created.role == UserRole.ADMIN
    assert created.date_created is not None


def test_get_user_by_id_returns_user_when_found(
    db_session: Session, sample_user: User
) -> None:
    """Verify get_user_by_id retrieves an existing user by primary key."""

    # GIVEN: An existing user persisted in the database

    # WHEN: Fetching the user by ID
    found = user_repository.get_user_by_id(db_session, sample_user.id)

    # THEN: The retrieved user matches the sample user instance
    assert found is not None
    assert found.id == sample_user.id
    assert found.email == sample_user.email
    assert found.name == sample_user.name


def test_get_user_by_id_returns_none_when_not_found(db_session: Session) -> None:
    """Verify get_user_by_id returns None when passed a non-existent ID."""

    # GIVEN: A non-existent user ID
    non_existent_id = 999999

    # WHEN: The `user_repository.get_user_by_id`
    # is called with a non_existent_id
    found = user_repository.get_user_by_id(db_session, non_existent_id)

    # THEN: We expect the Result to be None
    assert found is None


def test_get_user_by_email_returns_user_when_found(
    db_session: Session, sample_user: User
) -> None:
    """Verify get_user_by_email retrieves an existing user by exact email match."""

    # GIVEN: An existing user persisted in the database

    # WHEN: The `user_repository.get_user_by_email` function is
    #  called with a valid email
    found = user_repository.get_user_by_email(db_session, "siraj@motaung.com")

    # THEN: The retrieved user entity matches expected attributes
    assert found is not None
    assert found.id == sample_user.id
    assert found.email == "siraj@motaung.com"


def test_get_user_by_email_returns_none_when_user_does_not_exist(
    db_session: Session,
) -> None:
    """Verify get_user_by_email returns None for an unmapped email address."""

    # GIVEN: An email address not present in the database
    unknown_email = "nonexistent@nonexistent.com"

    # WHEN: The `user_repository.get_user_by_email` is called with an unkown email
    found = user_repository.get_user_by_email(db_session, unknown_email)

    # THEN: We expect the result to be None
    assert found is None
