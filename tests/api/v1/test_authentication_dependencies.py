"""Integration tests for protected-route authentication dependencies."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.database import get_session
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture
def authenticated_db() -> Generator[MagicMock, None, None]:
    """Provide a database double for the real authentication dependency."""

    db = MagicMock(spec=Session)
    db.scalar.return_value = User(
        id=7,
        name="Authenticated Customer",
        email="customer@example.com",
        role=UserRole.CUSTOMER,
    )

    def override_get_session():
        yield db

    app.dependency_overrides[get_session] = override_get_session
    yield db
    app.dependency_overrides.pop(get_session, None)


@patch("app.api.v1.dishes.dish_service.get_all_dishes", return_value=[])
def test_protected_route_accepts_valid_token_and_loads_user(
    mock_get_all_dishes: MagicMock,
    client: TestClient,
    authenticated_db: MagicMock,
) -> None:
    """Verify a valid JWT reaches a protected route through real auth dependencies."""

    # GIVEN: A valid access token and a database user matching its subject
    token = create_access_token(user_id=7, expires_in_minutes=15)

    # WHEN: Calling a protected endpoint with the bearer token
    response = client.get(
        "/api/v1/dishes",
        headers={"Authorization": f"Bearer {token}"},
    )

    # THEN: Authentication succeeds and the route is allowed to execute
    assert response.status_code == status.HTTP_200_OK
    authenticated_db.scalar.assert_called_once()
    mock_get_all_dishes.assert_called_once()


@patch("app.api.v1.dishes.dish_service.get_all_dishes")
def test_protected_route_rejects_invalid_token(
    mock_get_all_dishes: MagicMock,
    client: TestClient,
    authenticated_db: MagicMock,
) -> None:
    """Verify an invalid JWT is translated into a 401 response."""

    # GIVEN: A malformed bearer token
    # WHEN: Calling a protected endpoint with the invalid token
    response = client.get(
        "/api/v1/dishes",
        headers={"Authorization": "Bearer invalid-token"},
    )

    # THEN: Authentication fails before the route service is called
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["code"] == "INVALID_CREDENTIALS"
    mock_get_all_dishes.assert_not_called()
