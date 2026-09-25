"""Integration tests for restaurant dish ratings API endpoint."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user
from app.core import exceptions
from app.main import app
from app.models.rating import Rating
from app.models.user import User, UserRole


@pytest.fixture
def mock_customer_user() -> User:
    """Provide a mock authenticated customer user."""
    return User(
        id=42,
        name="Thrall Durotan",
        email="customer@orctrader.com",
        role=UserRole.CUSTOMER,
    )


@pytest.fixture
def sample_rating() -> Rating:
    """Provide a sample Rating instance for endpoint tests."""
    now = datetime.now(timezone.utc)
    return Rating(
        id=1,
        user_id=42,
        dish_id=10,
        rating=5,
        date_created=now,
        date_updated=now,
    )


@pytest.fixture(autouse=True)
def override_auth_dependency(mock_customer_user: User):
    """Override get_current_user dependency for test authentication."""
    app.dependency_overrides[get_current_user] = lambda: mock_customer_user
    yield
    app.dependency_overrides.clear()


@patch("app.api.v1.ratings.rating_service.create_rating")
def test_create_rating_success(
    mock_create_rating: MagicMock,
    client: TestClient,
    mock_customer_user: User,
    sample_rating: Rating,
) -> None:
    """Verify POST /ratings creates a rating and returns HTTP 201 Created."""
    # GIVEN: Valid RatingCreate payload and mocked service response

    payload = {
        "dish_id": 10,
        "rating": 5,
    }
    mock_create_rating.return_value = sample_rating

    # WHEN: Requesting rating creation
    response = client.post("/api/v1/ratings", json=payload)

    # THEN: Status code is 201 Created and fields match schema format
    assert response.status_code == status.HTTP_201_CREATED
    mock_create_rating.assert_called_once()
    assert mock_create_rating.call_args[0][1] == mock_customer_user.id

    data = response.json()
    assert data["id"] == 1
    assert data["user_id"] == 42
    assert data["dish_id"] == 10
    assert data["rating"] == 5


@patch("app.api.v1.ratings.rating_service.create_rating")
def test_create_rating_dish_not_found_returns_404(
    mock_create_rating: MagicMock, client: TestClient
) -> None:
    """Verify POST /ratings returns 404 Not Found when dish does not exist."""

    # GIVEN: Payload with an invalid dish_id
    payload = {
        "dish_id": 999,
        "rating": 4,
    }
    mock_create_rating.side_effect = exceptions.NotFoundError(
        "Dish with ID 999 was not found."
    )

    # WHEN: Posting rating
    response = client.post("/api/v1/ratings", json=payload)

    # THEN: Response status is 404 Not Found
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error_message"] == "Dish with ID 999 was not found."


@patch("app.api.v1.ratings.rating_service.create_rating")
def test_create_rating_duplicate_returns_409(
    mock_create_rating: MagicMock, client: TestClient
) -> None:
    """Verify POST /ratings returns 409 Conflict when user has already rated dish."""

    # GIVEN: Payload for a dish the user has previously rated
    payload = {
        "dish_id": 10,
        "rating": 3,
    }
    mock_create_rating.side_effect = exceptions.RatingAlreadyExistsError(
        "User has already rated this dish."
    )

    # WHEN: Attempting duplicate rating
    response = client.post("/api/v1/ratings", json=payload)

    # THEN: Response status is 409 Conflict
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["error_message"] == "User has already rated this dish."


def test_create_rating_validation_error_score_out_of_bounds(client: TestClient) -> None:
    """Verify Pydantic schema validation rejects ratings outside allowed range [1, 5]."""

    # GIVEN: Invalid score payload
    payload = {
        "dish_id": 10,
        "rating": 6,
    }

    # WHEN: Posting rating with invalid score
    response = client.post("/api/v1/ratings", json=payload)

    # THEN: Response returns HTTP 422 Unprocessable Entity
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
