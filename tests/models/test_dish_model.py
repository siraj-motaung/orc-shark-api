"""Unit tests for the Dish SQLAlchemy model database operations."""

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.models.dish import Dish


def test_create_dish_persists_successfully(db_session: Session) -> None:
    """Verify that a valid Dish record is correctly saved and retrieves auto-generated defaults."""

    # GIVEN: Valid parameters for a new dish
    dish = Dish(
        name="Orcish Mutton Stew",
        description="A rich, hearty broth simmered with roasted root vegetables.",
        price=Decimal("18.50"),
        image="https://example.com/stew.jpg",
    )

    # WHEN: Persisting the dish to the database session
    db_session.add(dish)
    db_session.commit()

    # THEN: The database assigns a primary key ID and populates default UTC timestamps
    assert dish.id is not None
    assert isinstance(dish.id, int)
    assert dish.name == "Orcish Mutton Stew"
    assert dish.price == Decimal("18.50")
    assert dish.date_created is not None
    assert dish.date_updated is not None


def test_dish_price_numeric_precision(db_session: Session) -> None:
    """Verify that the price column maintains exact Decimal precision without floating point drift."""

    # GIVEN: A dish initialized with a precise 2-decimal price value
    dish = Dish(
        name="Dragon Ale",
        description="Potent brew from the fiery depths.",
        price=Decimal("12.99"),
        image="https://example.com/ale.jpg",
    )
    db_session.add(dish)
    db_session.commit()

    # WHEN: Querying the record back from the database
    fetched_dish = db_session.scalar(select(Dish).where(Dish.id == dish.id))

    # THEN: The retrieved price is an instance of Decimal and matches exactly
    assert fetched_dish is not None
    assert isinstance(fetched_dish.price, Decimal)
    assert fetched_dish.price == Decimal("12.99")


@pytest.mark.parametrize(
    "missing_field_kwargs",
    [
        {
            "description": "A dish without a name",
            "price": Decimal("10.00"),
            "image": "https://example.com/a.jpg",
        },
        {
            "name": "No Description",
            "price": Decimal("10.00"),
            "image": "https://example.com/a.jpg",
        },
        {
            "name": "No Price",
            "description": "Description text",
            "image": "https://example.com/a.jpg",
        },
        {
            "name": "No Image",
            "description": "Description text",
            "price": Decimal("10.00"),
        },
    ],
)
def test_dish_missing_non_nullable_fields_raises_error(
    db_session: Session, missing_field_kwargs: dict
) -> None:
    """Verify that omitting mandatory non-nullable fields triggers an IntegrityError on commit."""

    # GIVEN: A Dish missing one of its required non-nullable fields
    dish = Dish(**missing_field_kwargs)

    # WHEN/THEN: Committing the invalid model raises an IntegrityError
    db_session.add(dish)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_dish_name_exceeds_max_length_raises_error(db_session: Session) -> None:
    """Verify that exceeding the String(100) column limit for the name field raises an IntegrityError."""

    # GIVEN: A Dish with a name exceeding 100 characters (105 characters)
    overly_long_name = "A" * 105
    dish = Dish(
        name=overly_long_name,
        description="Valid description.",
        price=Decimal("15.00"),
        image="https://example.com/dish.jpg",
    )

    # WHEN/THEN: Persisting the record causes database column length validation failure
    db_session.add(dish)
    with pytest.raises((DataError, IntegrityError)):
        db_session.commit()


def test_dish_date_updated_refreshes_on_mutation(db_session: Session) -> None:
    """Verify that updating a dish attribute updates the date_updated timestamp."""

    # GIVEN: An existing dish saved in the database
    dish = Dish(
        name="Elven Bread",
        description="Freshly baked waybread.",
        price=Decimal("5.00"),
        image="https://example.com/bread.jpg",
    )
    db_session.add(dish)
    db_session.commit()
    initial_updated_at = dish.date_updated

    # WHEN: Modifying an attribute and committing changes
    dish.price = Decimal("6.50")
    db_session.commit()
    db_session.refresh(dish)

    # THEN: The date_updated timestamp is updated
    assert dish.date_updated >= initial_updated_at


def test_dish_ratings_relationship_defaults_to_empty_list(db_session: Session) -> None:
    """Verify that the ratings relationship initializes as an empty list for new dishes."""

    # GIVEN: A newly saved Dish instance
    dish = Dish(
        name="Goblins Roast",
        description="Roasted spiced meats.",
        price=Decimal("22.00"),
        image="https://example.com/roast.jpg",
    )
    db_session.add(dish)
    db_session.commit()

    # WHEN: Accessing the ratings relationship
    ratings = dish.ratings

    # THEN: The relationship evaluates to an empty list
    assert ratings == []
