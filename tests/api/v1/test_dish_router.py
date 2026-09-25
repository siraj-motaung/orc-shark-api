"""Integration tests for restaurant dishes API endpoints."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user, require_admin
from app.core import exceptions
from app.main import app
from app.models.dish import Dish
from app.models.user import User, UserRole
from app.repositories.dish_repository import DishQueryResult


@pytest.fixture
def mock_admin_user() -> User:
    """Provide a mock admin user for authorization testing."""
    return User(
        id=1,
        name="Warchief Orgrim",
        email="admin@orctrader.com",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_customer_user() -> User:
    """Provide a mock customer user for authentication testing."""
    return User(
        id=2,
        name="Thrall Durotan",
        email="customer@orctrader.com",
        role=UserRole.CUSTOMER,
    )


@pytest.fixture
def sample_dish() -> Dish:
    """Provide a sample Dish instance for endpoint tests."""
    now = datetime.now(timezone.utc)
    return Dish(
        id=10,
        name="Gorgoroth Roasted Ribs",
        description="Succulent charred ribs coated in dark honey glazed spice.",
        price=Decimal("24.99"),
        image="https://example.com/ribs.jpg",
        date_created=now,
        date_updated=now,
    )


# Override auth dependencies by default to simulate an authenticated customer
@pytest.fixture(autouse=True)
def override_auth_dependencies(mock_customer_user: User):
    """Override get_current_user and require_admin defaults."""

    app.dependency_overrides[get_current_user] = lambda: mock_customer_user
    app.dependency_overrides[require_admin] = lambda: mock_customer_user
    yield
    app.dependency_overrides.clear()


@patch("app.api.v1.dishes.dish_service.create_dish")
def test_create_dish_as_admin_success(
    mock_create_dish: MagicMock,
    client: TestClient,
    mock_admin_user: User,
    sample_dish: Dish,
) -> None:
    """Verify POST /dishes creates a dish and returns HTTP 201 Created when executed by an admin."""

    # GIVEN: Admin authorization override and valid payload
    app.dependency_overrides[require_admin] = lambda: mock_admin_user
    payload = {
        "name": "Gorgoroth Roasted Ribs",
        "description": "Succulent charred ribs coated in dark honey glazed spice.",
        "price": 24.99,
        "image": "https://example.com/ribs.jpg",
    }
    mock_create_dish.return_value = DishQueryResult(
        dish=sample_dish,
        average_rating=None,
        rating_count=0,
    )

    # WHEN: Requesting dish creation
    response = client.post("/api/v1/dishes", json=payload)

    # THEN: Status code is 201 Created and properties match
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] == 10
    assert data["name"] == "Gorgoroth Roasted Ribs"
    assert data["rating_count"] == 0
    assert data["average_rating"] is None


@patch("app.api.v1.dishes.dish_service.get_all_dishes")
def test_get_all_dishes_success(
    mock_get_all: MagicMock, client: TestClient, sample_dish: Dish
) -> None:
    """Verify GET /dishes returns a list of dish response objects."""

    # GIVEN: Service returning a named dish summary
    mock_get_all.return_value = [DishQueryResult(sample_dish, 4.5, 2)]

    # WHEN: Fetching all dishes
    response = client.get("/api/v1/dishes")

    # THEN: HTTP 200 OK and response contains formatted dish data
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 10
    assert data[0]["average_rating"] == 4.5
    assert data[0]["rating_count"] == 2


@patch("app.api.v1.dishes.dish_service.search_dishes")
def test_search_dishes_success(
    mock_search: MagicMock, client: TestClient, sample_dish: Dish
) -> None:
    """Verify GET /dishes/search filters dishes by query string."""

    # GIVEN: Service returning a named matching dish summary
    mock_search.return_value = [DishQueryResult(sample_dish, 4.5, 2)]

    # WHEN: Executing search query
    response = client.get("/api/v1/dishes/search?query=ribs")

    # THEN: HTTP 200 OK with matching payload
    assert response.status_code == status.HTTP_200_OK
    mock_search.assert_called_once()
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Gorgoroth Roasted Ribs"


@patch("app.api.v1.dishes.dish_service.get_dish_by_id")
def test_get_dish_by_id_success(
    mock_get_by_id: MagicMock, client: TestClient, sample_dish: Dish
) -> None:
    """Verify GET /dishes/{dish_id} returns detailed dish info."""

    # GIVEN: Service returning full dish details with ratings
    mock_get_by_id.return_value = DishQueryResult(sample_dish, 4.5, 2, [])

    # WHEN: Fetching dish by ID
    response = client.get("/api/v1/dishes/10")

    # THEN: HTTP 200 OK with detailed response format
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 10
    assert "ratings" in data


@patch("app.api.v1.dishes.dish_service.get_dish_by_id")
def test_get_dish_by_id_not_found_returns_404(
    mock_get_by_id: MagicMock, client: TestClient
) -> None:
    """Verify GET /dishes/{dish_id} returns 404 Not Found for non-existent IDs."""

    # GIVEN: Service raising DishNotFoundError
    mock_get_by_id.side_effect = exceptions.DishNotFoundError(
        "Dish with ID 99 was not found."
    )

    # WHEN: Fetching missing dish ID
    response = client.get("/api/v1/dishes/99")

    # THEN: HTTP 404 Not Found
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error_message"] == "Dish with ID 99 was not found."


@patch("app.api.v1.dishes.dish_service.update_dish")
def test_update_dish_success(
    mock_update: MagicMock,
    client: TestClient,
    mock_admin_user: User,
    sample_dish: Dish,
) -> None:
    """Verify PATCH /dishes/{dish_id} updates entity and returns updated payload."""
    # GIVEN: Admin authentication and partial update payload

    app.dependency_overrides[require_admin] = lambda: mock_admin_user
    payload = {"name": "Updated Ribs"}
    mock_update.return_value = DishQueryResult(sample_dish, 5.0, 1, [])

    # WHEN: Requesting patch update
    response = client.patch("/api/v1/dishes/10", json=payload)

    # THEN: HTTP 200 OK with refreshed properties
    assert response.status_code == status.HTTP_200_OK
    mock_update.assert_called_once()


@patch("app.api.v1.dishes.dish_service.delete_dish_by_id")
def test_delete_dish_success(
    mock_delete: MagicMock, client: TestClient, mock_admin_user: User
) -> None:
    """Verify DELETE /dishes/{dish_id} deletes entity and returns 204 No Content."""

    # GIVEN: Admin authorization
    app.dependency_overrides[require_admin] = lambda: mock_admin_user
    mock_delete.return_value = None

    # WHEN: Requesting dish deletion
    response = client.delete("/api/v1/dishes/10")

    # THEN: HTTP 204 No Content with empty body
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""
