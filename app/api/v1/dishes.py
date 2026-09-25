"""A module containing API endpoints for restaurant dishes"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.api.serializers.dish import to_dish_detail_response, to_dish_response
from app.db.database import get_session
from app.models.user import User
from app.schemas.dish import DishCreate, DishDetailResponse, DishResponse, DishUpdate
from app.services import dish_service

router = APIRouter(prefix="/dishes", tags=["Dishes"])


@router.post("", response_model=DishResponse, status_code=status.HTTP_201_CREATED)
def create_dish(
    dish: DishCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
) -> DishResponse:
    """Create a new dish"""

    created_dish = dish_service.create_dish(dish_data=dish, db=db)

    return to_dish_response(created_dish)


@router.get("", response_model=list[DishResponse])
def get_all_dishes(
    db: Session = Depends(get_session), current_user: User = Depends(get_current_user)
) -> list[DishResponse]:
    """Retrieve all dishes"""

    results = dish_service.get_all_dishes(db)

    return [
        to_dish_response(dish)
        for dish in results
    ]


@router.get("/search", response_model=list[DishResponse])
def search_dishes(
    query: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):

    results = dish_service.search_dishes(
        db=db,
        query=query,
    )

    return [
        to_dish_response(dish)
        for dish in results
    ]


@router.get("/{dish_id}", response_model=DishDetailResponse)
def get_dish_by_id(
    dish_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DishDetailResponse:
    """Retrieve a dish by ID."""

    dish = dish_service.get_dish_by_id(db, dish_id)

    return to_dish_detail_response(dish)


@router.patch("/{dish_id}", response_model=DishResponse)
def update_dish(
    dish_id: int,
    dish_data: DishUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
) -> DishResponse:
    """Update an existing dish."""

    dish = dish_service.update_dish(db, dish_id, dish_data)

    return to_dish_response(dish)


@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dish(
    dish_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
) -> None:
    """Delete an existing dish."""

    dish_service.delete_dish_by_id(db, dish_id)
