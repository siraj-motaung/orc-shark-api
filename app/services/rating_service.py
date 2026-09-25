"""A module containing business logic for restaurant ratings."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, RatingAlreadyExistsError
from app.models.rating import Rating
from app.repositories import dish_repository, rating_repository, user_repository
from app.schemas.rating import RatingCreate


def create_rating(db: Session, user_id: int, rating_data: RatingCreate) -> Rating:
    """Create a new rating for a dish."""

    user = user_repository.get_user_by_id(db, user_id)

    if user is None:
        raise NotFoundError(f"User with ID {user_id} was not found.")

    dish = dish_repository.get_entity_by_id(
        db,
        rating_data.dish_id,
    )

    if dish is None:
        raise NotFoundError(f"Dish with ID {rating_data.dish_id} was not found.")

    existing_rating = rating_repository.get_by_user_and_dish(
        db,
        user_id,
        rating_data.dish_id,
    )

    if existing_rating is not None:
        raise RatingAlreadyExistsError("User has already rated this dish.")

    rating = Rating(
        user_id=user_id,
        dish_id=rating_data.dish_id,
        rating=rating_data.rating,
    )

    return rating_repository.create_rating(db, rating)
