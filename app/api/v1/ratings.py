"""A module containing API endpoints for restaurant dish ratings."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_session
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingResponse
from app.services import rating_service

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def create_rating(
    rating_data: RatingCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RatingResponse:
    """Create a new rating for a dish."""

    return rating_service.create_rating(db, current_user.id, rating_data)
