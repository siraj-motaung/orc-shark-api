"""Integration tests for user authentication API endpoints."""

from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from app.core import exceptions
from app.models.user import User, UserRole


@patch("app.api.v1.auth.auth_service.register_user")
def test_register_user_success(mock_register_user, client: TestClient) -> None:
    """Verify POST /auth/register creates a user and returns 201 Created."""

    # GIVEN: Valid UserCreate JSON payload
    payload = {
        "name": "Thrall Durotan",
        "email": "thrall@orctrader.com",
        "password": "securePassword123",
        "confirm_password": "securePassword123",
    }

    # Mock service layer return value
    mock_register_user.return_value = User(
        id=1,
        name="Thrall Durotan",
        email="thrall@orctrader.com",
        password_hash="hashed_secret",
        role=UserRole.CUSTOMER,
    )

    # WHEN: Making a POST request to /api/v1/auth/register
    response = client.post("/api/v1/auth/register", json=payload)

    # THEN: Status code is 201 Created and response payload excludes password_hash
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == 1
    assert data["email"] == "thrall@orctrader.com"
    assert data["name"] == "Thrall Durotan"
    assert "password_hash" not in data


@patch("app.api.v1.auth.auth_service.register_user")
def test_register_user_already_exists_returns_conflict(
    mock_register_user, client: TestClient
) -> None:
    """Verify POST /auth/register returns 409 Conflict when email is taken."""

    # GIVEN: Payload with an existing email
    payload = {
        "name": "Existing User",
        "email": "taken@orctrader.com",
        "password": "password123",
        "confirm_password": "password123",
    }

    # Mock service layer raising UserAlreadyExistsError
    mock_register_user.side_effect = exceptions.UserAlreadyExistsError(
        "A user with this email already exists."
    )

    # WHEN: Posting registration request
    response = client.post("/api/v1/auth/register", json=payload)

    # THEN: Response returns HTTP 409 Conflict
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["error_message"]


def test_register_user_validation_error_mismatched_passwords(
    client: TestClient,
) -> None:
    """Verify Pydantic validation rejects mismatched password confirmation."""

    # GIVEN: Payload where password and password_confirm do not match
    payload = {
        "name": "Warchief",
        "email": "warchief@orctrader.com",
        "password": "password123",
        "password_confirm": "differentPassword123",
    }

    # WHEN: Posting to /auth/register
    response = client.post("/api/v1/auth/register", json=payload)

    # THEN: Status is 422 Unprocessable Entity
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("app.api.v1.auth.auth_service.login_user")
def test_login_user_success(mock_login_user, client: TestClient) -> None:
    """Verify POST /auth/login returns 200 OK and JWT access token."""

    # GIVEN: Valid login credentials
    payload = {
        "email": "thrall@orctrader.com",
        "password": "securePassword123",
    }
    mock_login_user.return_value = "mocked_jwt_bearer_token"

    # WHEN: Making a POST request to /api/v1/auth/login
    response = client.post("/api/v1/auth/login", json=payload)

    # THEN: Response returns 200 OK with token payload structure
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["access_token"] == "mocked_jwt_bearer_token"
    assert data["token_type"] == "bearer"


@patch("app.api.v1.auth.auth_service.login_user")
def test_login_user_invalid_credentials_returns_unauthorized(
    mock_login_user, client: TestClient
) -> None:
    """Verify POST /auth/login returns 401 Unauthorized for bad credentials."""

    # GIVEN: Invalid password or email
    payload = {
        "email": "thrall@orctrader.com",
        "password": "wrongPassword",
    }
    mock_login_user.side_effect = exceptions.AuthenticationError(
        "Invalid email or password"
    )

    # WHEN: Attempting login
    response = client.post("/api/v1/auth/login", json=payload)

    # THEN: Status code is 401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error_message"] == "Invalid email or password"


@patch("app.api.v1.auth.auth_service.login_user")
def test_login_user_rate_limit_exceeded_returns_too_many_requests(
    mock_login_user, client: TestClient
) -> None:
    """Verify POST /auth/login returns 429 Too Many Requests when locked out."""

    # GIVEN: Locked out login credentials
    payload = {
        "email": "locked@orctrader.com",
        "password": "password123",
    }
    mock_login_user.side_effect = exceptions.RateLimitError(
        "Too many failed login attempts. Please try again later"
    )

    # WHEN: Attempting login while locked out
    response = client.post("/api/v1/auth/login", json=payload)

    # THEN: Status code is 429 Too Many Requests
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many failed login attempts" in response.json()["error_message"]
