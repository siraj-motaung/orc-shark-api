"""Serializers for dish API responses."""

from app.repositories.dish_repository import DishQueryResult
from app.schemas.dish import DishDetailResponse, DishResponse


def to_dish_response(result: DishQueryResult) -> DishResponse:
    """Convert a dish query result into the public dish response schema."""

    dish = result.dish

    return DishResponse(
        id=dish.id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        image=dish.image,
        average_rating=result.average_rating,
        rating_count=result.rating_count,
        date_created=dish.date_created,
        date_updated=dish.date_updated,
    )


def to_dish_detail_response(result: DishQueryResult) -> DishDetailResponse:
    """Convert a dish query result into the detailed response schema."""

    return DishDetailResponse(
        **to_dish_response(result).model_dump(),
        ratings=result.ratings or None,
    )
