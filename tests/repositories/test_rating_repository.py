"""Unit tests for the rating database repository operations."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.dish import Dish
from app.models.rating import Rating
from app.models.user import User, UserRole
from app.repositories import rating_repository


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create and persist a baseline user for rating repository tests."""
    user = User(
        name="Rating Reviewer",
        email="reviewer@orctrader.com",
        password_hash="hashed_secret_123",
        role=UserRole.CUSTOMER,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_dish(db_session: Session) -> Dish:
    """Create and persist a baseline dish for rating repository tests."""
    dish = Dish(
        name="Gorgoroth Roasted Ribs",
        description="Succulent charred ribs coated in dark honey glazed spice.",
        price=Decimal("24.99"),
        image="https://example.com/ribs.jpg",
    )
    db_session.add(dish)
    db_session.commit()
    return dish


def test_create_rating_persists_and_returns_rating(
    db_session: Session, sample_user: User, sample_dish: Dish
) -> None:
    """Verify create_rating saves a new rating and returns the refreshed entity."""
    # GIVEN: An unpersisted Rating model instance
    rating = Rating(
        user_id=sample_user.id,
        dish_id=sample_dish.id,
        rating=5,
    )

    # WHEN: Executing create_rating
    created = rating_repository.create_rating(db_session, rating)

    # THEN: The returned rating has a generated ID and matches input values
    assert created.id is not None
    assert created.user_id == sample_user.id
    assert created.dish_id == sample_dish.id
    assert created.rating == 5
    assert created.date_created is not None


def test_get_by_user_and_dish_returns_rating_when_exists(
    db_session: Session, sample_user: User, sample_dish: Dish
) -> None:
    """Verify get_by_user_and_dish retrieves the specific rating for a user and dish."""

    # GIVEN: A rating record persisted in the database
    rating = Rating(
        user_id=sample_user.id,
        dish_id=sample_dish.id,
        rating=4,
    )
    db_session.add(rating)
    db_session.commit()

    # WHEN: Fetching the rating by user_id and dish_id
    fetched = rating_repository.get_by_user_and_dish(
        db_session, user_id=sample_user.id, dish_id=sample_dish.id
    )

    # THEN: The exact rating entity is returned
    assert fetched is not None
    assert fetched.id == rating.id
    assert fetched.user_id == sample_user.id
    assert fetched.dish_id == sample_dish.id
    assert fetched.rating == 4


def test_get_by_user_and_dish_returns_none_when_no_rating_exists(
    db_session: Session, sample_user: User, sample_dish: Dish
) -> None:
    """Verify get_by_user_and_dish returns None when a user has not rated the given dish."""

    # GIVEN: A user and dish without an associated rating record

    # WHEN: Querying for a rating that does not exist
    fetched = rating_repository.get_by_user_and_dish(
        db_session, user_id=sample_user.id, dish_id=sample_dish.id
    )

    # THEN: The function returns None
    assert fetched is None


def test_get_by_user_and_dish_returns_none_for_non_existent_identifiers(
    db_session: Session,
) -> None:
    """Verify get_by_user_and_dish returns None when passed arbitrary non-existent IDs."""

    # GIVEN: Non-existent user_id and dish_id values
    non_existent_user_id = 99999
    non_existent_dish_id = 88888

    # WHEN: Querying with unmapped IDs
    fetched = rating_repository.get_by_user_and_dish(
        db_session, user_id=non_existent_user_id, dish_id=non_existent_dish_id
    )

    # THEN: Result is None
    assert fetched is None
