"""A module containing database operations for restaurant dishes."""

import logging
from dataclasses import dataclass

from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.dish import Dish
from app.models.rating import Rating

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DishQueryResult:
    """Dish data combined with its calculated rating information."""

    dish: Dish
    average_rating: float | None
    rating_count: int
    ratings: list[Rating] | None = None


def create_dish(db: Session, dish: Dish) -> Dish:
    """ "Create a new dish and save it to the database."""

    db.add(dish)
    db.commit()
    db.refresh(dish)

    return dish


def get_dish_by_id(db: Session, dish_id: int) -> DishQueryResult | None:
    """Return a dish with its rating summary and individual ratings."""

    statement = (
        select(
            Dish,
            func.avg(Rating.rating).label("average_rating"),
            func.count(Rating.id).label("rating_count"),
        )
        .outerjoin(Rating, Rating.dish_id == Dish.id)
        .where(Dish.id == dish_id)
        .group_by(Dish.id)
    )

    result = db.execute(statement).first()

    if result is None:
        return None

    dish, average_rating, rating_count = result

    ratings_statement = (
        select(Rating).where(Rating.dish_id == dish_id).order_by(Rating.id)
    )

    ratings = list(db.scalars(ratings_statement).all())

    return DishQueryResult(
        dish=dish,
        average_rating=(
            float(average_rating) if average_rating is not None else None
        ),
        rating_count=rating_count,
        ratings=ratings,
    )


def get_all_dishes(db: Session) -> list[DishQueryResult]:
    """Return all dishes with their rating summaries."""

    statement = (
        select(
            Dish,
            func.avg(Rating.rating).label("average_rating"),
            func.count(Rating.id).label("rating_count"),
        )
        .outerjoin(Rating, Rating.dish_id == Dish.id)
        .group_by(Dish.id)
        .order_by(Dish.id)
    )

    return [
        DishQueryResult(
            dish=dish,
            average_rating=(
                float(average_rating) if average_rating is not None else None
            ),
            rating_count=rating_count,
        )
        for dish, average_rating, rating_count in db.execute(statement).all()
    ]


def search_dishes(
    db: Session,
    query: str,
) -> list[DishQueryResult]:
    """Search dishes by name and return their rating summaries."""

    statement = (
        select(
            Dish,
            func.avg(Rating.rating).label("average_rating"),
            func.count(Rating.id).label("rating_count"),
        )
        .outerjoin(
            Rating,
            Rating.dish_id == Dish.id,
        )
        .where(
            Dish.name.ilike(f"%{query}%"),
        )
        .group_by(Dish.id)
        .order_by(Dish.id)
    )

    return [
        DishQueryResult(
            dish=dish,
            average_rating=(
                float(average_rating) if average_rating is not None else None
            ),
            rating_count=rating_count,
        )
        for dish, average_rating, rating_count in db.execute(statement).all()
    ]


def update(db: Session, dish: Dish) -> Dish:
    """Update and return an existing dish."""

    db.commit()
    db.refresh(dish)

    return dish


def get_entity_by_id(db: Session, dish_id: int) -> Dish | None:
    """Return a dish entity by ID."""

    statement = select(Dish).where(Dish.id == dish_id)

    return db.scalar(statement)


def delete(db: Session, dish_id: int) -> bool:
    """Delete a dish by ID and return whether it existed."""

    statement = sqlalchemy_delete(Dish).where(Dish.id == dish_id)
    result = db.execute(statement)

    if result.rowcount == 0:
        return False

    db.commit()

    return True
