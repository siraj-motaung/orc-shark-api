"""Unit tests for rating Pydantic schemas validation rules."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.rating import RatingCreate, RatingResponse


def test_rating_create_valid_payload():
    """Verify that a valid rating payload instantiates successfully."""

    # GIVEN: A dictionary with valid dish_id and rating values
    payload = {
        "dish_id": 10,
        "rating": 5,
    }

    # WHEN: Instantiating the RatingCreate schema
    schema = RatingCreate(**payload)

    # THEN: Validation passes and attributes match input values
    assert schema.dish_id == 10
    assert schema.rating == 5


@pytest.mark.parametrize("valid_rating", [1, 2, 3, 4, 5])
def test_rating_create_allowed_rating_boundary_values(valid_rating: int):
    """Verify that all rating integers between 1 and 5 are accepted."""

    # GIVEN: A payload with a rating within the allowed range [1, 5]
    payload = {
        "dish_id": 1,
        "rating": valid_rating,
    }

    # WHEN: Instantiating RatingCreate
    schema = RatingCreate(**payload)

    # THEN: The schema parses cleanly with the given rating
    assert schema.rating == valid_rating


@pytest.mark.parametrize(
    "invalid_dish_id, error_substring",
    [
        (0, "Dish ID must be greater than 0"),
        (-1, "Dish ID must be greater than 0"),
    ],
)
def test_rating_create_invalid_dish_id(invalid_dish_id: int, error_substring: str):
    """Verify that dish_id must be greater than 0."""

    # GIVEN: A payload with an invalid dish_id (<= 0)
    payload = {
        "dish_id": invalid_dish_id,
        "rating": 4,
    }

    # WHEN/THEN: Instantiating RatingCreate raises a ValidationError
    with pytest.raises(ValidationError) as exc_info:
        RatingCreate(**payload)

    assert error_substring in str(exc_info.value)


@pytest.mark.parametrize(
    "invalid_rating, error_substring",
    [
        (0, "Rating must be between 1 and 5."),
        (6, "Rating must be between 1 and 5."),
        (-5, "Rating must be between 1 and 5."),
    ],
)
def test_rating_create_invalid_rating_boundaries(
    invalid_rating: int, error_substring: str
):
    """Verify that ratings outside the 1 to 5 range trigger validation errors."""

    # GIVEN: A payload with a rating out of bounds
    payload = {
        "dish_id": 1,
        "rating": invalid_rating,
    }

    # WHEN/THEN: Instantiating RatingCreate raises a ValidationError matching expected boundary error
    with pytest.raises(ValidationError) as exc_info:
        RatingCreate(**payload)

    assert error_substring in str(exc_info.value)


def test_rating_response_serialization_from_dict():
    """Verify RatingResponse correctly parses valid dictionary/ORM representation."""

    # GIVEN: A complete rating dictionary
    now = datetime.now(timezone.utc)
    payload = {
        "id": 1,
        "user_id": 42,
        "dish_id": 10,
        "rating": 5,
        "date_created": now,
        "date_updated": now,
    }

    # WHEN: Instantiating RatingResponse
    schema = RatingResponse(**payload)

    # THEN: The model attributes match the dictionary attributes
    assert schema.id == 1
    assert schema.user_id == 42
    assert schema.dish_id == 10
    assert schema.rating == 5
    assert schema.date_created == now
    assert schema.date_updated == now


def test_rating_response_missing_required_field():
    """Verify RatingResponse raises a ValidationError when required fields are missing."""

    # GIVEN: An incomplete dictionary lacking user_id
    now = datetime.now(timezone.utc)
    payload = {
        "id": 1,
        "dish_id": 10,
        "rating": 5,
        "date_created": now,
        "date_updated": now,
    }

    # WHEN/THEN: Instantiating RatingResponse raises a ValidationError
    with pytest.raises(ValidationError) as exc_info:
        RatingResponse(**payload)

    assert "user_id" in str(exc_info.value)
