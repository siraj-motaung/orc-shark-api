"""A module containing API endpoints for user authentication."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Session = Depends(get_session)) -> UserResponse:
    """Register a new user"""

    return auth_service.register_user(db, user_data)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    login_credentials: LoginRequest, db: Session = Depends(get_session)
) -> TokenResponse:
    "Authenticate a user and return access token."

    access_token = auth_service.login_user(db=db, login_credentials=login_credentials)

    return TokenResponse(access_token=access_token)
