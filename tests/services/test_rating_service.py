"""Unit tests for rating business logic service functions."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, RatingAlreadyExistsError
from app.models.dish import Dish
from app.models.rating import Rating
from app.models.user import User
from app.schemas.rating import RatingCreate
from app.services import rating_service


@pytest.fixture
def mock_db() -> MagicMock:
    """Provide a mocked SQLAlchemy database session instance."""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_user() -> User:
    """Provide a sample User model instance."""
    return User(id=1, name="Thrall", email="thrall@orctrader.com")


@pytest.fixture
def sample_dish() -> Dish:
    """Provide a sample Dish model instance."""
    return Dish(id=10, name="Gorgoroth Roasted Ribs")


@patch("app.services.rating_service.rating_repository")
@patch("app.services.rating_service.dish_repository")
@patch("app.services.rating_service.user_repository")
def test_create_rating_success(
    mock_user_repo: MagicMock,
    mock_dish_repo: MagicMock,
    mock_rating_repo: MagicMock,
    mock_db: MagicMock,
    sample_user: User,
    sample_dish: Dish,
) -> None:
    """Verify successful rating creation delegates to repository and returns entity."""

    # GIVEN: Valid user, valid dish, and no existing rating record
    payload = RatingCreate(dish_id=10, rating=5)

    mock_user_repo.get_user_by_id.return_value = sample_user
    mock_dish_repo.get_entity_by_id.return_value = sample_dish
    mock_rating_repo.get_by_user_and_dish.return_value = None

    created_rating = Rating(id=100, user_id=1, dish_id=10, rating=5)
    mock_rating_repo.create_rating.return_value = created_rating

    # WHEN: The `rating_service.create_rating` function is called
    result = rating_service.create_rating(mock_db, user_id=1, rating_data=payload)

    # THEN: User and dish existence are verified, unique check passes, and rating is created
    mock_user_repo.get_user_by_id.assert_called_once_with(mock_db, 1)
    mock_dish_repo.get_entity_by_id.assert_called_once_with(mock_db, 10)
    mock_rating_repo.get_by_user_and_dish.assert_called_once_with(mock_db, 1, 10)

    mock_rating_repo.create_rating.assert_called_once()
    passed_rating = mock_rating_repo.create_rating.call_args[0][1]
    assert isinstance(passed_rating, Rating)
    assert passed_rating.user_id == 1
    assert passed_rating.dish_id == 10
    assert passed_rating.rating == 5
    assert result == created_rating


@patch("app.services.rating_service.user_repository")
def test_create_rating_user_not_found_raises_error(
    mock_user_repo: MagicMock, mock_db: MagicMock
) -> None:
    """Verify create_rating raises NotFoundError when user does not exist."""
    # GIVEN: A user_id that returns None from user_repository

    payload = RatingCreate(dish_id=10, rating=4)
    mock_user_repo.get_user_by_id.return_value = None

    # WHEN: The `rating_service.create_rating` is called with an invalid UserID
    # THEN: We expect the Service to raises a NotFoundError exception
    with pytest.raises(NotFoundError, match="User with ID 99 was not found"):
        rating_service.create_rating(mock_db, user_id=99, rating_data=payload)


@patch("app.services.rating_service.dish_repository")
@patch("app.services.rating_service.user_repository")
def test_create_rating_dish_not_found_raises_error(
    mock_user_repo: MagicMock,
    mock_dish_repo: MagicMock,
    mock_db: MagicMock,
    sample_user: User,
) -> None:
    """Verify create_rating raises NotFoundError when dish does not exist."""

    # GIVEN: Existing user but non-existent dish_id
    payload = RatingCreate(dish_id=999, rating=4)
    mock_user_repo.get_user_by_id.return_value = sample_user
    mock_dish_repo.get_entity_by_id.return_value = None

    # WHEN: The `rating_service.create_rating` is called with an invalid DishID
    # THEN: We expect the Service to raises a NotFoundError exception
    with pytest.raises(NotFoundError, match="Dish with ID 999 was not found"):
        rating_service.create_rating(mock_db, user_id=1, rating_data=payload)


@patch("app.services.rating_service.rating_repository")
@patch("app.services.rating_service.dish_repository")
@patch("app.services.rating_service.user_repository")
def test_create_rating_duplicate_raises_error(
    mock_user_repo: MagicMock,
    mock_dish_repo: MagicMock,
    mock_rating_repo: MagicMock,
    mock_db: MagicMock,
    sample_user: User,
    sample_dish: Dish,
) -> None:
    """Verify create_rating raises RatingAlreadyExistsError when user rated dish previously."""

    # GIVEN: Existing user, dish, AND a prior rating record in rating_repository
    payload = RatingCreate(dish_id=10, rating=3)
    mock_user_repo.get_user_by_id.return_value = sample_user
    mock_dish_repo.get_entity_by_id.return_value = sample_dish

    existing_rating = Rating(id=50, user_id=1, dish_id=10, rating=5)
    mock_rating_repo.get_by_user_and_dish.return_value = existing_rating

    # WHEN: The `rating_service.create_rating` is called with an existing rating
    # THEN: We expect the Service to raise the RatingAlreadyExistsError exception
    with pytest.raises(
        RatingAlreadyExistsError, match="User has already rated this dish"
    ):
        rating_service.create_rating(mock_db, user_id=1, rating_data=payload)

    mock_rating_repo.create_rating.assert_not_called()
