"""Unit tests for dish API response serializers."""

from datetime import datetime, timezone
from decimal import Decimal

from app.api.serializers.dish import to_dish_detail_response, to_dish_response
from app.models.dish import Dish
from app.models.rating import Rating
from app.repositories.dish_repository import DishQueryResult


def test_to_dish_response_maps_query_result() -> None:
    """Verify a dish query result becomes the public summary response."""

    # GIVEN: A dish query result with calculated rating information
    now = datetime.now(timezone.utc)
    dish = Dish(
        id=1,
        name="Goblins Roast",
        description="Hearty meal for brave adventurers.",
        price=Decimal("12.00"),
        image="https://example.com/roast.jpg",
        date_created=now,
        date_updated=now,
    )
    result = DishQueryResult(
        dish=dish,
        average_rating=4.5,
        rating_count=12,
    )

    # WHEN: Serializing the query result
    response = to_dish_response(result)

    # THEN: Dish fields and rating summary are mapped to the response
    assert response.id == dish.id
    assert response.name == dish.name
    assert response.price == dish.price
    assert response.average_rating == 4.5
    assert response.rating_count == 12


def test_to_dish_detail_response_maps_ratings() -> None:
    """Verify detailed serialization includes nested ratings."""

    # GIVEN: A dish query result containing one rating
    now = datetime.now(timezone.utc)
    dish = Dish(
        id=1,
        name="Goblins Roast",
        description="Hearty meal for brave adventurers.",
        price=Decimal("12.00"),
        image="https://example.com/roast.jpg",
        date_created=now,
        date_updated=now,
    )
    rating = Rating(
        id=10,
        user_id=2,
        dish_id=1,
        rating=5,
        date_created=now,
        date_updated=now,
    )
    result = DishQueryResult(
        dish=dish,
        average_rating=5.0,
        rating_count=1,
        ratings=[rating],
    )

    # WHEN: Serializing the detailed query result
    response = to_dish_detail_response(result)

    # THEN: The rating is converted to the nested response schema
    assert response.average_rating == 5.0
    assert response.ratings is not None
    assert len(response.ratings) == 1
    assert response.ratings[0].id == rating.id
    assert response.ratings[0].rating == rating.rating


def test_to_dish_detail_response_uses_none_for_empty_ratings() -> None:
    """Verify detailed serialization omits an empty rating collection."""

    # GIVEN: A dish query result without ratings
    now = datetime.now(timezone.utc)
    dish = Dish(
        id=1,
        name="Goblins Roast",
        description="Hearty meal for brave adventurers.",
        price=Decimal("12.00"),
        image="https://example.com/roast.jpg",
        date_created=now,
        date_updated=now,
    )
    result = DishQueryResult(
        dish=dish,
        average_rating=None,
        rating_count=0,
        ratings=[],
    )

    # WHEN: Serializing the detailed query result
    response = to_dish_detail_response(result)

    # THEN: Empty ratings are represented as None
    assert response.ratings is None
