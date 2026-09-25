"""Unit tests for the authentication service business logic and rate limiting."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import exceptions
from app.models.user import User, UserRole
from app.schemas.user import LoginRequest, UserCreate
from app.services import auth_service


@pytest.fixture(autouse=True)
def reset_rate_limit_state():
    """Reset global in-memory login rate limit state before each test execution."""

    auth_service._failed_login_attempts.clear()
    yield
    auth_service._failed_login_attempts.clear()


@pytest.fixture
def mock_db() -> MagicMock:
    """Provide a mocked SQLAlchemy database session instance."""
    return MagicMock(spec=Session)


@patch("app.services.auth_service.user_repository")
@patch("app.services.auth_service.hash_password")
def test_register_user_success(
    mock_hash_password: MagicMock, mock_user_repo: MagicMock, mock_db: MagicMock
) -> None:
    """Verify successful registration hashes the password and returns the created user."""

    # GIVEN: A valid UserCreate payload and no existing user with that email
    payload = UserCreate(
        name="Siraj Motaung",
        email="siraj@motaung.com",
        password="securePassword123",
        confirm_password="securePassword123",
    )

    mock_user_repo.get_user_by_email.return_value = None
    mock_hash_password.return_value = "hashed_secret"

    created_user = User(
        id=1,
        name="Siraj Motaung",
        email="siraj@motaung.com",
        password_hash="hashed_secret",
        role=UserRole.CUSTOMER,
    )

    mock_user_repo.create_user.return_value = created_user

    # WHEN: The `auth_service.register_user` function is called with the correct payload
    result = auth_service.register_user(mock_db, payload)

    # THEN: The email is normalized, the password is hashed, and the user is created
    mock_user_repo.get_user_by_email.assert_called_once_with(
        mock_db, "siraj@motaung.com"
    )
    mock_hash_password.assert_called_once_with("securePassword123")
    mock_user_repo.create_user.assert_called_once()

    assert result.id == 1
    assert result.email == "siraj@motaung.com"


@patch("app.services.auth_service.user_repository")
def test_register_user_already_exists_raises_error(
    mock_user_repo: MagicMock, mock_db: MagicMock
) -> None:
    """Verify registering an existing email raises UserAlreadyExistsError."""

    # GIVEN: A payload whose normalized email address already exists
    payload = UserCreate(
        name="Existing User",
        email="existing@gmail.com",
        password="password123",
        confirm_password="password123",
    )

    mock_user_repo.get_user_by_email.return_value = User(
        id=10,
        email="existing@gmail.com",
    )

    # WHEN: Registering a user with an existing email
    # THEN: UserAlreadyExistsError is raised
    with pytest.raises(
        exceptions.UserAlreadyExistsError,
        match="email already exists",
    ):
        auth_service.register_user(mock_db, payload)

    mock_user_repo.create_user.assert_not_called()


@patch("app.services.auth_service.user_repository")
def test_register_user_translates_database_duplicate_to_conflict(
    mock_user_repo: MagicMock, mock_db: MagicMock
) -> None:
    """Verify a concurrent duplicate insert becomes a domain conflict error."""

    # GIVEN: The pre-check sees no user, but the database rejects the insert
    payload = UserCreate(
        name="Concurrent User",
        email="concurrent@gmail.com",
        password="password123",
        confirm_password="password123",
    )
    mock_user_repo.get_user_by_email.return_value = None
    mock_user_repo.create_user.side_effect = IntegrityError(
        "duplicate key value violates unique constraint",
        {},
        Exception("duplicate email"),
    )

    # WHEN: Registration races with another request for the same email
    # THEN: The database failure is translated into the normal conflict error
    with pytest.raises(
        exceptions.UserAlreadyExistsError,
        match="email already exists",
    ):
        auth_service.register_user(mock_db, payload)

    mock_db.rollback.assert_called_once_with()


@patch("app.services.auth_service.user_repository")
def test_login_user_not_found_raises_authentication_error(
    mock_user_repo: MagicMock, mock_db: MagicMock
) -> None:
    """Verify unknown email raises AuthenticationError and records a failed attempt."""

    # GIVEN: Unmapped email address
    credentials = LoginRequest(email="unknown@gmail.com", password="password123")
    mock_user_repo.get_user_by_email.return_value = None

    # WHEN: Calling `auth_service.login_user` with invalid credentials
    # THEN: Then we expect AuthenticationError to be raised
    with pytest.raises(
        exceptions.AuthenticationError, match="Invalid email or password"
    ):
        auth_service.login_user(mock_db, credentials)

    assert len(auth_service._failed_login_attempts["unknown@gmail.com"]) == 1


@patch("app.services.auth_service.verify_password")
@patch("app.services.auth_service.user_repository")
def test_login_user_invalid_password_raises_authentication_error(
    mock_user_repo: MagicMock, mock_verify_password: MagicMock, mock_db: MagicMock
) -> None:
    """Verify wrong password raises AuthenticationError and records a failed attempt."""

    # GIVEN: Existing user but incorrect password
    credentials = LoginRequest(email="user@gmail.com", password="wrongPassword")
    mock_user_repo.get_user_by_email.return_value = User(id=1, password_hash="hash")
    mock_verify_password.return_value = False

    # WHEN: The `auth_service.login_user` function is called with the wrong passeord
    # THEN: Login raises AuthenticationError
    with pytest.raises(
        exceptions.AuthenticationError, match="Invalid email or password"
    ):
        auth_service.login_user(mock_db, credentials)

    assert len(auth_service._failed_login_attempts["user@gmail.com"]) == 1


@patch("app.services.auth_service.user_repository")
def test_login_user_exceeding_max_attempts_triggers_rate_limit(
    mock_user_repo: MagicMock, mock_db: MagicMock
) -> None:
    """Verify exceeding MAX_FAILED_LOGIN_ATTEMPTS locks out future login requests."""

    # GIVEN: An email with 5 recorded failed login attempts
    email = "locked@gmail.com"
    credentials = LoginRequest(email=email, password="password123")

    # WHEN: The `auth_service._record_failed_login` is called subsequenlt
    for _ in range(auth_service.MAX_FAILED_LOGIN_ATTEMPTS):
        auth_service._record_failed_login(email)

    # THEN: We expect RateLimitError get raised without checking database
    with pytest.raises(
        exceptions.RateLimitError, match="Too many failed login attempts"
    ):
        auth_service.login_user(mock_db, credentials)

    mock_user_repo.get_user_by_email.assert_not_called()


@patch("app.services.auth_service.create_access_token")
@patch("app.services.auth_service.verify_password")
@patch("app.services.auth_service.user_repository")
def test_successful_login_resets_failed_attempts(
    mock_user_repo: MagicMock,
    mock_verify_password: MagicMock,
    mock_create_token: MagicMock,
    mock_db: MagicMock,
) -> None:
    """Verify a successful login clears prior recorded failure attempts."""

    # GIVEN: An email with 3 prior failure attempts below lockout threshold
    email = "user@gmail.com"
    credentials = LoginRequest(email=email, password="validPassword123")

    for _ in range(3):
        auth_service._record_failed_login(email)

    mock_user_repo.get_user_by_email.return_value = User(
        id=5, email=email, password_hash="hash"
    )
    mock_verify_password.return_value = True
    mock_create_token.return_value = "token123"

    # WHEN: Logging in successfully
    auth_service.login_user(mock_db, credentials)

    # THEN: The failure tracking entry for this email is cleared
    assert email not in auth_service._failed_login_attempts
