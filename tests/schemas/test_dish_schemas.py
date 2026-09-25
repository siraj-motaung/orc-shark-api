"""Unit tests for dish Pydantic schemas validation rules."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.dish import DishCreate, DishDetailResponse, DishResponse, DishUpdate


def test_dish_create_valid_payload():
    """Verify that a valid payload succeeds and strips leading/trailing whitespace."""

    # GIVEN: A payload dictionary with extra whitespace around string fields
    payload = {
        "name": "   Dragon Fire Burger   ",
        "description": "   A super spicy burger with dragon sauce.   ",
        "price": Decimal("15.99"),
        "image": "https://example.com/burger.png",
    }

    # WHEN: Instantiating the DishCreate schema
    schema = DishCreate(**payload)

    # THEN: The schema parses correctly and strips the whitespace
    assert schema.name == "Dragon Fire Burger"
    assert schema.description == "A super spicy burger with dragon sauce."
    assert schema.price == Decimal("15.99")
    assert str(schema.image) == "https://example.com/burger.png"


@pytest.mark.parametrize(
    "name, description, error_substring",
    [
        ("", "Valid description text", "Field cannot be empty"),
        ("Valid Name", "Tiny", "String should have at least 5 characters"),
        ("  ", "Valid description text", "Field cannot be empty."),
        ("Valid Name", "", "Field cannot be empty."),
        (
            "a" * 105,
            "Valid description text",
            "String should have at most 100 characters",
        ),
    ],
)
def test_dish_create_invalid_string_fields(
    name: str, description: str, error_substring: str
):
    """Verify string length constraints and whitespace rejection."""

    # GIVEN: A payload with invalid string field lengths or empty whitespace
    payload = {
        "name": name,
        "description": description,
        "price": Decimal("10.00"),
        "image": "https://example.com/dish.jpg",
    }

    # WHEN: Instantiating DishCreate
    # THEN: raise a ValidationError matching the expected error
    with pytest.raises(ValidationError) as exc_info:
        DishCreate(**payload)

    assert error_substring in str(exc_info.value)


@pytest.mark.parametrize(
    "invalid_price",
    [
        Decimal("-1.00"),  # Violates ge=0
        Decimal("10.999"),  # Violates decimal_places=2
    ],
)
def test_dish_create_invalid_price(invalid_price: Decimal):
    """Verify price numerical constraints."""

    # GIVEN: A payload with an invalid numeric price
    payload = {
        "name": "Valid Dish Name",
        "description": "Valid description text here",
        "price": invalid_price,
        "image": "https://example.com/dish.jpg",
    }

    # WHEN: Instantiating DishCreate
    # THEN: Raises a ValidationError
    with pytest.raises(ValidationError):
        DishCreate(**payload)


def test_dish_create_invalid_image_url():
    """Verify invalid URL strings fail validation."""

    # GIVEN: A payload with a malformed URL string
    payload = {
        "name": "Valid Dish Name",
        "description": "Valid description text here",
        "price": Decimal("10.00"),
        "image": "not-a-valid-url",
    }

    # WHEN: Instantiating DishCreate
    # THEN: Raises a ValidationError
    with pytest.raises(ValidationError):
        DishCreate(**payload)


def test_dish_update_empty_payload_succeeds():
    """Verify DishUpdate allows all fields to be optional/None."""

    # GIVEN: An empty keyword arguments call

    # WHEN: Instantiating DishUpdate without arguments
    schema = DishUpdate()

    # THEN: All attributes default to None
    assert schema.name is None
    assert schema.description is None
    assert schema.price is None
    assert schema.image is None


def test_dish_update_partial_fields():
    """Verify DishUpdate correctly validates partial fields when supplied."""

    # GIVEN: A payload supplying only a name with extra padding spaces
    payload = {"name": "   Updated Name   "}

    # WHEN: Instantiating DishUpdate
    schema = DishUpdate(**payload)

    # THEN: The provided name is validated and cleaned while unspecified fields remain None
    assert schema.name == "Updated Name"
    assert schema.price is None


def test_dish_update_invalid_whitespace_name():
    """Verify string validation still runs on non-None update values."""
    # GIVEN: An update attempt containing only whitespace in a field

    # WHEN/THEN: Instantiating DishUpdate raises a ValidationError
    with pytest.raises(ValidationError) as exc_info:
        DishUpdate(name="   ")

    assert "Field cannot be empty." in str(exc_info.value)


def test_dish_response_serialization_from_dict():
    """Verify DishResponse instantiates correctly from dictionary data."""

    # GIVEN: A complete dictionary matching the expected ORM/database output fields
    now = datetime.now(timezone.utc)
    payload = {
        "id": 1,
        "name": "Goblins Roast",
        "description": "Hearty meal for brave adventurers.",
        "price": Decimal("12.00"),
        "image": "https://example.com/roast.jpg",
        "average_rating": 4.5,
        "rating_count": 12,
        "date_created": now,
        "date_updated": now,
    }

    # WHEN: Instantiating DishResponse with the data dictionary
    schema = DishResponse(**payload)

    # THEN: The model attributes match the dictionary values exactly
    assert schema.id == 1
    assert schema.average_rating == 4.5
    assert schema.rating_count == 12


def test_dish_detail_response_with_ratings():
    """Verify DishDetailResponse handles an optional nested ratings list."""

    # GIVEN: A detail payload dictionary containing a nested ratings list
    now = datetime.now(timezone.utc)
    payload = {
        "id": 1,
        "name": "Goblins Roast",
        "description": "Hearty meal for brave adventurers.",
        "price": Decimal("12.00"),
        "image": "https://example.com/roast.jpg",
        "average_rating": 5.0,
        "rating_count": 1,
        "date_created": now,
        "date_updated": now,
        "ratings": [
            {
                "id": 10,
                "rating": 5,
                "comment": "Delicious!",
                "user_id": 2,
                "dish_id": 1,
                "date_created": now,
                "date_updated": now,
            }
        ],
    }

    # WHEN: Instantiating DishDetailResponse
    schema = DishDetailResponse(**payload)

    # THEN: The nested ratings list is properly parsed into RatingResponse models
    assert schema.ratings is not None
    assert len(schema.ratings) == 1
    assert schema.ratings[0].rating == 5
