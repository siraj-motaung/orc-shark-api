"""Unit tests for dish business logic service functions."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from app.core import exceptions
from app.models.dish import Dish
from app.repositories.dish_repository import DishQueryResult
from app.schemas.dish import DishCreate, DishUpdate
from app.services import dish_service


@pytest.fixture
def mock_db() -> MagicMock:
    """Provide a mocked SQLAlchemy database session instance."""

    return MagicMock(spec=Session)


@pytest.fixture
def sample_dish() -> Dish:
    """Provide a sample Dish model instance."""
    return Dish(
        id=1,
        name="Gorgoroth Roasted Ribs",
        description="Succulent charred ribs coated in dark honey glazed spice.",
        price=Decimal("24.99"),
        image="https://example.com/ribs.jpg",
    )


@patch("app.services.dish_service.dish_repository")
def test_create_dish_success(
    mock_repo: MagicMock, mock_db: MagicMock, sample_dish: Dish
) -> None:
    """Verify that create_dish delegates object creation to the repository."""

    # GIVEN: A valid DishCreate Pydantic schema
    payload = DishCreate(
        name="Gorgoroth Roasted Ribs",
        description="Succulent charred ribs coated in dark honey glazed spice.",
        price=Decimal("24.99"),
        image=HttpUrl("https://example.com/ribs.jpg"),
    )
    mock_repo.create_dish.return_value = sample_dish

    # WHEN: The `dish_service.create_dish` with a valid payload is called
    result = dish_service.create_dish(mock_db, payload)

    # THEN: Repository create_dish is called with a populated Dish entity
    mock_repo.create_dish.assert_called_once()
    passed_dish = mock_repo.create_dish.call_args[0][1]
    assert isinstance(passed_dish, Dish)
    assert passed_dish.name == "Gorgoroth Roasted Ribs"
    assert passed_dish.price == Decimal("24.99")
    assert passed_dish.image == "https://example.com/ribs.jpg"
    assert result.dish == sample_dish
    assert result.average_rating is None
    assert result.rating_count == 0


@patch("app.services.dish_service.dish_repository")
def test_get_dish_by_id_success(
    mock_repo: MagicMock, mock_db: MagicMock, sample_dish: Dish
) -> None:
    """Verify get_dish_by_id returns dish details when entity exists."""

    # GIVEN: Repository returns named dish details
    expected_result = DishQueryResult(sample_dish, 4.5, 2, [])
    mock_repo.get_dish_by_id.return_value = expected_result

    # WHEN: The `dish_service.get_dish_by_id` function get called with the valid parameters
    result = dish_service.get_dish_by_id(mock_db, dish_id=1)

    # THEN: We expect the named result to be returned cleanly
    mock_repo.get_dish_by_id.assert_called_once_with(mock_db, 1)
    assert result == expected_result


@patch("app.services.dish_service.dish_repository")
def test_get_dish_by_id_raises_not_found(
    mock_repo: MagicMock, mock_db: MagicMock
) -> None:
    """Verify get_dish_by_id raises DishNotFoundError when repository returns None."""

    # GIVEN: Repository returns None for given ID
    mock_repo.get_dish_by_id.return_value = None

    # WHEN: The `dish_service.get_dish_by_id` function is called with an invalid ID
    # THEN: Service raises DishNotFoundError
    with pytest.raises(
        exceptions.DishNotFoundError, match="Dish with ID 99 was not found"
    ):
        dish_service.get_dish_by_id(mock_db, dish_id=99)


@patch("app.services.dish_service.dish_repository")
def test_get_all_dishes_delegates_to_repo(
    mock_repo: MagicMock, mock_db: MagicMock
) -> None:
    """Verify get_all_dishes delegates directly to repository."""
    # GIVEN: Repository returning named dish summaries

    mock_repo.get_all_dishes.return_value = [
        DishQueryResult(sample_dish, 4.0, 1),
        DishQueryResult(sample_dish, 5.0, 3),
    ]

    # WHEN: The `dish_service.get_all_dishes` is called
    results = dish_service.get_all_dishes(mock_db)

    # THEN: We expect the List to be returned unchanged
    mock_repo.get_all_dishes.assert_called_once_with(mock_db)
    assert len(results) == 2


@patch("app.services.dish_service.dish_repository")
def test_search_dishes_delegates_to_repo(
    mock_repo: MagicMock, mock_db: MagicMock
) -> None:
    """Verify search_dishes passes search query string to repository."""

    # GIVEN: Query string 'ribs' and mocked repository response
    mock_repo.search_dishes.return_value = [DishQueryResult(sample_dish, 4.5, 1)]

    # WHEN: Executing search_dishes
    results = dish_service.search_dishes(mock_db, query="ribs")

    # THEN: Query parameter is passed to repository search method
    mock_repo.search_dishes.assert_called_once_with(mock_db, "ribs")
    assert len(results) == 1


@patch("app.services.dish_service.dish_repository")
def test_update_dish_partial_fields_success(
    mock_repo: MagicMock, mock_db: MagicMock, sample_dish: Dish
) -> None:
    """Verify update_dish mutates provided fields and updates repository entity."""
    # GIVEN: Existing dish and a partial update payload changing price and name

    mock_repo.get_entity_by_id.return_value = sample_dish
    mock_repo.get_dish_by_id.return_value = DishQueryResult(sample_dish, 4.5, 2, [])

    update_payload = DishUpdate(
        name="Updated Ribs",
        price=Decimal("29.99"),
    )

    # WHEN: The `dish_service.update_dish` function is called with update payload
    dish_service.update_dish(mock_db, dish_id=1, dish_update=update_payload)

    # THEN: Dish model properties are updated and persisted
    assert sample_dish.name == "Updated Ribs"
    assert sample_dish.price == Decimal("29.99")

    # Description and image remain unchanged
    assert (
        sample_dish.description
        == "Succulent charred ribs coated in dark honey glazed spice."
    )
    mock_repo.update.assert_called_once_with(mock_db, sample_dish)
    mock_repo.get_dish_by_id.assert_called_once_with(mock_db, 1)


@patch("app.services.dish_service.dish_repository")
def test_update_dish_raises_not_found(mock_repo: MagicMock, mock_db: MagicMock) -> None:
    """Verify update_dish raises DishNotFoundError when entity is missing."""

    # GIVEN: Repository returns None for get_entity_by_id
    mock_repo.get_entity_by_id.return_value = None
    update_payload = DishUpdate(name="Nonexistent Dish")

    # WHEN: The `dish_service.update_dish` is called with a non-existed ID
    # THEN: We expect a DishNotFoundError exception to be raised
    with pytest.raises(
        exceptions.DishNotFoundError, match="Dish with ID 99 was not found"
    ):
        dish_service.update_dish(mock_db, dish_id=99, dish_update=update_payload)

    mock_repo.update.assert_not_called()


@patch("app.services.dish_service.dish_repository")
def test_delete_dish_by_id_success(mock_repo: MagicMock, mock_db: MagicMock) -> None:
    """Verify delete_dish_by_id executes cleanly when deletion succeeds."""

    # GIVEN: Repository returns True for deletion
    mock_repo.delete.return_value = True

    # WHEN: Deleting an existing dish
    dish_service.delete_dish_by_id(mock_db, dish_id=1)

    # THEN: Delete repository method is invoked with dish_id
    mock_repo.delete.assert_called_once_with(mock_db, 1)


@patch("app.services.dish_service.dish_repository")
def test_delete_dish_by_id_raises_not_found(
    mock_repo: MagicMock, mock_db: MagicMock
) -> None:
    """Verify delete_dish_by_id raises DishNotFoundError when repository returns False."""

    # GIVEN: Repository returns False for deletion

    mock_repo.delete.return_value = False

    # WHEN: The `dish_service.delete_dish_by_id` is called Non-existent ID
    # THEN: We excpet DishNotFoundError exception to be raised
    with pytest.raises(
        exceptions.DishNotFoundError, match="Dish with ID 99 was not found"
    ):
        dish_service.delete_dish_by_id(mock_db, dish_id=99)
