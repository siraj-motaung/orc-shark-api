"""Repository functions for restaurant rating database operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rating import Rating


def get_by_user_and_dish(db: Session, user_id: int, dish_id: int) -> Rating | None:
    """Return a user's rating for a dish, if one exists."""

    statement = select(Rating).where(
        Rating.user_id == user_id,
        Rating.dish_id == dish_id,
    )

    return db.scalar(statement)


def create_rating(db: Session, rating: Rating) -> Rating:
    """Create and return a new rating."""

    db.add(rating)
    db.commit()
    db.refresh(rating)

    return rating
