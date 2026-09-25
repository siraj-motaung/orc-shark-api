"""A module containing business logic and database operations for restaurant dishes."""

import logging

from sqlalchemy.orm import Session

from app.core import exceptions
from app.models.dish import Dish
from app.repositories import dish_repository
from app.repositories.dish_repository import DishQueryResult
from app.schemas.dish import DishCreate, DishUpdate

logger = logging.getLogger(__name__)


def create_dish(db: Session, dish_data: DishCreate) -> DishQueryResult:
    """ "Create a new dish and save it to the database."""

    dish = Dish(
        name=dish_data.name,
        description=dish_data.description,
        price=dish_data.price,
        image=str(dish_data.image),
    )

    created_dish = dish_repository.create_dish(db, dish)

    return DishQueryResult(
        dish=created_dish,
        average_rating=None,
        rating_count=0,
    )


def get_dish_by_id(db: Session, dish_id: int) -> DishQueryResult:
    """Return a dish with its rating information."""

    result = dish_repository.get_dish_by_id(db, dish_id)

    if result is None:
        raise exceptions.DishNotFoundError(f"Dish with ID {dish_id} was not found.")

    return result


def get_all_dishes(db: Session) -> list[DishQueryResult]:
    """Return all dishes with their rating information."""

    return dish_repository.get_all_dishes(db)


def search_dishes(
    db: Session,
    query: str,
) -> list[DishQueryResult]:
    """Search dishes by name and return their rating summaries."""

    return dish_repository.search_dishes(db, query)


def update_dish(
    db: Session,
    dish_id: int,
    dish_update: DishUpdate,
) -> DishQueryResult:
    """Update an existing dish."""

    dish = dish_repository.get_entity_by_id(db, dish_id)

    if dish is None:
        raise exceptions.DishNotFoundError(f"Dish with ID {dish_id} was not found.")

    if dish_update.name is not None:
        dish.name = dish_update.name

    if dish_update.description is not None:
        dish.description = dish_update.description

    if dish_update.price is not None:
        dish.price = dish_update.price

    if dish_update.image is not None:
        dish.image = str(dish_update.image)

    dish_repository.update(db, dish)

    return dish_repository.get_dish_by_id(db, dish_id)


def delete_dish_by_id(db: Session, dish_id: int) -> None:
    """Delete an existing dish by ID."""

    deleted = dish_repository.delete(db, dish_id)

    if not deleted:
        raise exceptions.DishNotFoundError(f"Dish with ID {dish_id} was not found.")
