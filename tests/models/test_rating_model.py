"""Unit tests for the Rating SQLAlchemy model database operations and constraints."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.dish import Dish
from app.models.rating import Rating
from app.models.user import User, UserRole


# Helper Fixtures
@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create and persist a sample user for rating tests."""
    user = User(
        name="Test Customer",
        email="customer@example.com",
        password_hash="hashed_pass_123",
        role=UserRole.CUSTOMER,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_dish(db_session: Session) -> Dish:
    """Create and persist a sample dish for rating tests."""

    dish = Dish(
        name="Gorgoroth Roasted Ribs",
        description="Succulent charred ribs coated in dark honey glazed spice.",
        price=Decimal("24.99"),
        image="https://example.com/ribs.jpg",
    )
    db_session.add(dish)
    db_session.commit()
    return dish


# Creation & Relationship Tests


def test_create_rating_persists_successfully(
    db_session: Session, sample_user: User, sample_dish: Dish
) -> None:
    """Verify that a valid Rating record persists cleanly and sets default timestamps."""

    # GIVEN: A rating associated with a valid user and dish
    rating = Rating(
        user_id=sample_user.id,
        dish_id=sample_dish.id,
        rating=5,
    )

    # WHEN: Persisting the rating to the session
    db_session.add(rating)
    db_session.commit()

    # THEN: Primary key is generated and timestamps are set automatically
    assert rating.id is not None
    assert rating.user_id == sample_user.id
    assert rating.dish_id == sample_dish.id
    assert rating.rating == 5
    assert isinstance(rating.date_created, datetime)
    assert isinstance(rating.date_updated, datetime)
    assert rating.date_created is not None
    assert rating.date_updated is not None


def test_rating_relationships_load_correctly(
    db_session: Session, sample_user: User, sample_dish: Dish
) -> None:
    """Verify bidirectional ORM relationships between User, Dish, and Rating."""

    # GIVEN: A persisted rating record
    rating = Rating(
        user_id=sample_user.id,
        dish_id=sample_dish.id,
        rating=4,
    )
    db_session.add(rating)
    db_session.commit()

    # WHEN: Fetching the rating from the database
    fetched_rating = db_session.scalar(select(Rating).where(Rating.id == rating.id))

    # THEN: The related user and dish instances are populated
    assert fetched_rating is not None
    assert fetched_rating.user.id == sample_user.id
    assert fetched_rating.dish.id == sample_dish.id
    assert rating in sample_user.ratings
    assert rating in sample_dish.ratings


@pytest.mark.parametrize("invalid_score", [0, 6, -1, 10])
def test_rating_score_check_constraint_fails(
    db_session: Session, sample_user: User, sample_dish: Dish, invalid_score: int
) -> None:
    """Verify CheckConstraint 'ck_ratings_rating_range' rejects values outside [1, 5]."""

    # GIVEN: A rating score outside the allowed 1-5 boundary
    rating = Rating(
        user_id=sample_user.id,
        dish_id=sample_dish.id,
        rating=invalid_score,
    )

    # WHEN/THEN: Committing raises an IntegrityError due to constraint violation
    db_session.add(rating)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert (
        "ck_ratings_rating_range" in str(exc_info.value).lower()
        or "check constraint" in str(exc_info.value).lower()
    )


def test_rating_unique_user_dish_constraint_fails(
    db_session: Session, sample_user: User, sample_dish: Dish
) -> None:
    """Verify UniqueConstraint 'uq_ratings_user_dish' prevents a user from rating the same dish twice."""

    # GIVEN: An existing rating for a given user and dish
    initial_rating = Rating(
        user_id=sample_user.id,
        dish_id=sample_dish.id,
        rating=5,
    )
    db_session.add(initial_rating)
    db_session.commit()

    # WHEN: Attempting to insert a second rating for the exact same user_id and dish_id
    duplicate_rating = Rating(
        user_id=sample_user.id,
        dish_id=sample_dish.id,
        rating=3,
    )
    db_session.add(duplicate_rating)

    # THEN: Committing raises an IntegrityError
    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert (
        "uq_ratings_user_dish" in str(exc_info.value).lower()
        or "unique constraint" in str(exc_info.value).lower()
    )


def test_rating_cascades_on_user_deletion(
    db_session: Session, sample_user: User, sample_dish: Dish
) -> None:
    """Verify ON DELETE CASCADE deletes ratings when the associated user is removed."""

    # GIVEN: A persisted rating record
    rating = Rating(
        user_id=sample_user.id,
        dish_id=sample_dish.id,
        rating=5,
    )
    db_session.add(rating)
    db_session.commit()
    rating_id = rating.id

    # WHEN: Deleting the associated user
    db_session.delete(sample_user)
    db_session.commit()

    # THEN: The rating record is automatically deleted via FK cascade
    fetched_rating = db_session.scalar(select(Rating).where(Rating.id == rating_id))
    assert fetched_rating is None


def test_rating_cascades_on_dish_deletion(
    db_session: Session, sample_user: User, sample_dish: Dish
) -> None:
    """Verify ON DELETE CASCADE deletes ratings when the associated dish is removed."""

    # GIVEN: A persisted rating record
    rating = Rating(
        user_id=sample_user.id,
        dish_id=sample_dish.id,
        rating=4,
    )
    db_session.add(rating)
    db_session.commit()
    rating_id = rating.id

    # WHEN: Deleting the associated dish
    db_session.delete(sample_dish)
    db_session.commit()

    # THEN: The rating record is automatically deleted via FK cascade
    fetched_rating = db_session.scalar(select(Rating).where(Rating.id == rating_id))
    assert fetched_rating is None
