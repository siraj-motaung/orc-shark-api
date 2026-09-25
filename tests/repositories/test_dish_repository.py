"""Unit tests for the dish database repository operations."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.dish import Dish
from app.models.rating import Rating
from app.models.user import User, UserRole
from app.repositories import dish_repository


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create and persist a user for rating association."""

    user = User(
        name="Gorgoroth Eater",
        email="eater@orctrader.com",
        password_hash="hashed_secret_123",
        role=UserRole.CUSTOMER,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_dish(db_session: Session) -> Dish:
    """Create and persist a baseline dish."""

    dish = Dish(
        name="Orcish Mutton Stew",
        description="A rich, hearty broth simmered with roasted root vegetables.",
        price=Decimal("18.50"),
        image="https://example.com/stew.jpg",
    )
    db_session.add(dish)
    db_session.commit()
    return dish


def test_create_dish_persists_and_returns_dish(db_session: Session) -> None:
    """Verify that create_dish adds a new dish record and assigns a primary key."""

    # GIVEN: An unpersisted Dish model instance
    dish = Dish(
        name="Dragon Ale",
        description="Potent brew from the fiery depths.",
        price=Decimal("12.99"),
        image="https://example.com/ale.jpg",
    )

    # WHEN: Calling `dish_repository.create_dish` function.
    created = dish_repository.create_dish(db_session, dish)

    # THEN: The returned dish is persisted with an auto-generated ID
    assert created.id is not None
    assert created.name == "Dragon Ale"
    assert created.price == Decimal("12.99")


def test_get_entity_by_id_returns_dish_when_found(
    db_session: Session, sample_dish: Dish
) -> None:
    """Verify get_entity_by_id retrieves an existing dish by primary key."""

    # GIVEN: An existing dish persisted in the database

    # WHEN: Fetching the entity by ID
    found = dish_repository.get_entity_by_id(db_session, sample_dish.id)

    # THEN: The retrieved entity matches the sample dish
    assert found is not None
    assert found.id == sample_dish.id
    assert found.name == sample_dish.name


def test_get_entity_by_id_returns_none_when_not_found(db_session: Session) -> None:
    """Verify get_entity_by_id returns None for non-existent IDs."""

    # GIVEN: A non-existent dish ID
    non_existent_id = 999999

    # WHEN: Querying for the entity
    found = dish_repository.get_entity_by_id(db_session, non_existent_id)

    # THEN: Result is None
    assert found is None


def test_get_dish_by_id_returns_dish_summary_and_ratings(
    db_session: Session, sample_user: User, sample_dish: Dish
) -> None:
    """Verify get_dish_by_id computes average_rating, rating_count, and rating list correctly."""

    # GIVEN: A dish with two ratings attached
    rating1 = Rating(user_id=sample_user.id, dish_id=sample_dish.id, rating=5)

    # Create a second user for the second rating to respect unique user_id/dish_id constraint
    second_user = User(
        name="Second Customer",
        email="customer2@orctrader.com",
        password_hash="hash_456",
    )
    db_session.add(second_user)
    db_session.commit()

    rating2 = Rating(user_id=second_user.id, dish_id=sample_dish.id, rating=3)
    db_session.add_all([rating1, rating2])
    db_session.commit()

    # WHEN: Calling `dish_repository.get_dish_by_id`
    result = dish_repository.get_dish_by_id(db_session, sample_dish.id)

    # THEN: A named result is returned with precise rating averages
    assert result is not None

    assert result.dish.id == sample_dish.id
    assert result.average_rating == 4.0
    assert result.rating_count == 2
    assert result.ratings is not None
    assert len(result.ratings) == 2


def test_get_dish_by_id_returns_none_when_dish_does_not_exist(
    db_session: Session,
) -> None:
    """Verify get_dish_by_id returns None when given a non-existent ID."""

    # GIVEN: An invalid dish ID
    non_existent_id = 888888

    # WHEN: Querying for dish details
    result = dish_repository.get_dish_by_id(db_session, non_existent_id)

    # THEN: The function returns None
    assert result is None


def test_get_all_dishes_returns_dishes_with_summaries(
    db_session: Session, sample_user: User, sample_dish: Dish
) -> None:
    """Verify get_all_dishes lists all dishes along with rating aggregations."""

    # GIVEN: Multiple dishes, one with a rating and one without
    dish_without_rating = Dish(
        name="Elven Bread",
        description="Freshly baked waybread.",
        price=Decimal("5.00"),
        image="https://example.com/bread.jpg",
    )
    db_session.add(dish_without_rating)

    rating = Rating(user_id=sample_user.id, dish_id=sample_dish.id, rating=4)
    db_session.add(rating)
    db_session.commit()

    # WHEN: Retrieving all dishes
    all_dishes = dish_repository.get_all_dishes(db_session)

    # THEN: Two records are returned ordered by ID
    assert len(all_dishes) == 2

    # Find sample_dish in returned summaries
    sample_row = next(row for row in all_dishes if row.dish.id == sample_dish.id)
    assert float(sample_row.average_rating) == 4.0
    assert sample_row.rating_count == 1

    # Find dish_without_rating in returned summaries
    unrated_row = next(
        row for row in all_dishes if row.dish.id == dish_without_rating.id
    )
    assert unrated_row.average_rating is None
    assert unrated_row.rating_count == 0


def test_search_dishes_case_insensitive_matching(
    db_session: Session, sample_dish: Dish
) -> None:
    """Verify search_dishes performs case-insensitive ILIKE matching on dish names."""

    # GIVEN: An existing dish named 'Orcish Mutton Stew'

    # WHEN: Searching with lowercase query substring 'mutton'
    results = dish_repository.search_dishes(db_session, "mutton")

    # THEN: The matching dish row is returned
    assert len(results) == 1
    found_dish = results[0].dish
    assert found_dish.id == sample_dish.id


def test_search_dishes_returns_empty_list_when_no_match(
    db_session: Session, sample_dish: Dish
) -> None:
    """Verify search_dishes returns an empty list when no dishes match the query."""
    # GIVEN: A query term that does not exist in any dish name

    # WHEN: Executing the search
    results = dish_repository.search_dishes(db_session, "does_not_exist")

    # THEN: An empty list is returned
    assert results == []


def test_update_dish_persists_changes(db_session: Session, sample_dish: Dish) -> None:
    """Verify update flushes attribute mutations and refreshes the entity."""

    # GIVEN: An existing dish with updated fields
    sample_dish.price = Decimal("21.00")
    sample_dish.description = "Updated gourmet stew recipe."

    # WHEN: Calling update
    updated_dish = dish_repository.update(db_session, sample_dish)

    # THEN: The returned entity contains the updated attributes
    assert updated_dish.price == Decimal("21.00")
    assert updated_dish.description == "Updated gourmet stew recipe."


def test_delete_dish_removes_record_and_returns_true(
    db_session: Session, sample_dish: Dish
) -> None:
    """Verify delete removes an existing dish and returns True."""

    # GIVEN: An existing dish record
    dish_id = sample_dish.id

    # WHEN: `dish_repository.delete` function is called
    success = dish_repository.delete(db_session, dish_id)

    # THEN: We expect the operation returns True and the dish is no longer found in DB
    assert success is True
    assert dish_repository.get_entity_by_id(db_session, dish_id) is None


def test_delete_dish_returns_false_when_not_found(db_session: Session) -> None:
    """Verify delete returns False when given a non-existent dish ID."""

    # GIVEN: An invalid dish ID
    non_existent_id = 777777

    # WHEN: Attempting to delete the dish
    success = dish_repository.delete(db_session, non_existent_id)

    # THEN: The operation returns False
    assert success is False
