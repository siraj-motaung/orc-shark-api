"""Module containing Pydantic schemas for dish API requests and responses."""

from datetime import datetime
from decimal import Decimal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

from app.schemas.rating import RatingResponse


class DishCreate(BaseModel):
    """Schema for creating a new dish."""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=5, max_length=1000)
    price: Decimal = Field(ge=0, decimal_places=2)
    image: AnyHttpUrl

    @field_validator("name", "description", mode="before")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty.")

        return value


class DishUpdate(BaseModel):
    """Schema for updating an existing dish."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        min_length=5,
        max_length=1000,
    )
    price: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )
    image: AnyHttpUrl | None = None

    @field_validator("name", "description")
    @classmethod
    def validate_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty.")

        return value


class DishResponse(BaseModel):
    """Schema returned when representing a dish."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price: Decimal
    image: AnyHttpUrl
    average_rating: float | None
    rating_count: int
    date_created: datetime
    date_updated: datetime


class DishDetailResponse(DishResponse):
    """Schema returned when representing a dish with its ratings."""

    ratings: list[RatingResponse] | None = None
