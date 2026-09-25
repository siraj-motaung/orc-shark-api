"""A module containing API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.dishes import router as dishes_router
from app.api.v1.ratings import router as ratings_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(dishes_router)
api_router.include_router(ratings_router)
