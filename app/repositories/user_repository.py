"""Repository functions for restaurant user database operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    """Return a user by ID."""

    statement = select(User).where(User.id == user_id)

    return db.scalar(statement)


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    """Return a user by email address."""

    statement = select(User).where(User.email == email)

    return db.scalar(statement)


def create_user(
    db: Session,
    user: User,
) -> User:
    """Create and return a new user."""

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
