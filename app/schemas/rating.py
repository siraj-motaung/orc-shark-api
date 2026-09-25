"""A module containing Pydantic schemas for rating API requests and responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RatingCreate(BaseModel):
    """Schema for creating a dish rating."""

    dish_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)

    @field_validator("dish_id", mode="before")
    @classmethod
    def validate_dish_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Dish ID must be greater than 0.")
        return value

    @field_validator("rating", mode="before")
    @classmethod
    def validate_rating(cls, value: int) -> int:
        if not 1 <= value <= 5:
            raise ValueError("Rating must be between 1 and 5.")

        return value


class RatingResponse(BaseModel):
    """Schema returned when representing a dish rating."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    dish_id: int
    rating: int
    date_created: datetime
    date_updated: datetime
