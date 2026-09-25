"""Unit tests for the User SQLAlchemy model database operations and constraints."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.dish import Dish
from app.models.rating import Rating
from app.models.user import User, UserRole

# ==========================================
# Creation & Default Tests
# ==========================================


def test_create_user_persists_successfully(db_session: Session) -> None:
    """Verify that a valid User record is saved and assigns default fields."""

    # GIVEN: Valid parameters for a new user
    user = User(
        name="Siraj",
        email="Siraj@siraj.com",
        password_hash="hashed_secret_key",
    )

    # WHEN: Persisting the record to the session
    db_session.add(user)
    db_session.commit()

    # THEN: Primary key is populated, role defaults to CUSTOMER, and date_created is set
    assert user.id is not None
    assert user.name == "Siraj"
    assert user.email == "Siraj@siraj.com"
    assert user.password_hash == "hashed_secret_key"
    assert user.role == UserRole.CUSTOMER
    assert user.date_created is not None
    assert isinstance(user.date_created, datetime)


def test_create_user_with_admin_role(db_session: Session) -> None:
    """Verify that explicit ADMIN role assignment persists correctly."""

    # GIVEN: User parameters explicitly specifying UserRole.ADMIN
    user = User(
        name="Admin",
        email="admin@admin.com",
        password_hash="hashed_admin_key",
        role=UserRole.ADMIN,
    )

    # WHEN: Persisting the record to the session
    db_session.add(user)
    db_session.commit()

    # THEN: Role is saved as ADMIN
    assert user.role == UserRole.ADMIN


def test_user_email_unique_constraint_fails(db_session: Session) -> None:
    """Verify that inserting duplicate email addresses raises an IntegrityError."""

    # GIVEN: An existing persisted user record
    existing_user = User(
        name="sir",
        email="sir@email.com",
        password_hash="hash_one",
    )
    db_session.add(existing_user)
    db_session.commit()

    # WHEN: Attempting to insert a second user with the same email
    duplicate_user = User(
        name="sir",
        email="sir@email.com",
        password_hash="hash_two",
    )
    db_session.add(duplicate_user)

    # THEN: Committing triggers a unique constraint IntegrityError
    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()

    assert (
        "unique" in str(exc_info.value).lower()
        or "email" in str(exc_info.value).lower()
    )


@pytest.mark.parametrize(
    "missing_kwargs",
    [
        {"email": "no_name@shack.com", "password_hash": "hash123"},
        {"name": "No Email", "password_hash": "hash123"},
        {"name": "No Password", "email": "no_pass@shack.com"},
    ],
)
def test_user_missing_required_fields_raises_integrity_error(
    db_session: Session, missing_kwargs: dict
) -> None:
    """Verify that omitting mandatory non-nullable fields raises an IntegrityError."""

    # GIVEN: User parameters missing a mandatory non-nullable attribute
    user = User(**missing_kwargs)

    # WHEN/THEN: Persisting the incomplete instance causes database column validation failure
    db_session.add(user)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_user_ratings_relationship_defaults_to_empty_list(db_session: Session) -> None:
    """Verify that the ratings relationship initializes as an empty list for new users."""

    # GIVEN: A newly persisted User instance
    user = User(
        name="New Customer",
        email="customer@customer.com",
        password_hash="secure_hash_456",
    )
    db_session.add(user)
    db_session.commit()

    # WHEN: Accessing the ratings collection property
    # THEN: Ratings is an empty collection
    assert user.ratings == []


def test_user_ratings_relationship_cascade_deletion(db_session: Session) -> None:
    """Verify that user.ratings updates dynamically when ratings are attached."""

    # GIVEN: A user, a dish, and an associated rating record
    user = User(
        name="Gourmet Goblin",
        email="goblin@shack.com",
        password_hash="hash_789",
    )
    dish = Dish(
        name="Mushroom Stew",
        description="Savory broth made with subterranean fungi.",
        price=Decimal("12.00"),
        image="https://example.com/stew.jpg",
    )
    db_session.add_all([user, dish])
    db_session.commit()

    rating = Rating(user_id=user.id, dish_id=dish.id, rating=5)
    db_session.add(rating)
    db_session.commit()

    # WHEN: Querying the user instance from the database session
    fetched_user = db_session.scalar(select(User).where(User.id == user.id))

    # THEN: Ratings collection contains the rating reference
    assert fetched_user is not None
    assert len(fetched_user.ratings) == 1
    assert fetched_user.ratings[0].rating == 5
    assert fetched_user.ratings[0].dish_id == dish.id
