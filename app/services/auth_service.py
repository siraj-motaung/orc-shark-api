"""Business logic for restaurant authentication."""

import logging
from collections import defaultdict
from time import monotonic

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import exceptions
from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories import user_repository
from app.schemas.user import LoginRequest, UserCreate

logger = logging.getLogger(__name__)


MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300


_failed_login_attempts: dict[str, list[float]] = defaultdict(list)


def _is_login_locked(email: str) -> bool:
    """Determine whether an email address is temporarily locked out."""

    now = monotonic()

    attempts = _failed_login_attempts.get(email, [])

    recent_attempts = [
        attempt for attempt in attempts if now - attempt < LOCKOUT_DURATION_SECONDS
    ]

    _failed_login_attempts[email] = recent_attempts

    return len(recent_attempts) >= MAX_FAILED_LOGIN_ATTEMPTS


def _record_failed_login(email: str) -> None:
    """Record a failed login attempt."""

    _failed_login_attempts[email].append(monotonic())


def _reset_failed_login(email: str) -> None:
    """Reset failed login attempts after successful authentication."""

    _failed_login_attempts.pop(email, None)


def register_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    """Register a new user with a securely hashed password."""

    email = str(user_data.email).lower()

    existing_user = user_repository.get_user_by_email(
        db,
        email,
    )

    if existing_user is not None:
        raise exceptions.UserAlreadyExistsError(
            "A user with this email already exists."
        )

    user = User(
        name=user_data.name,
        email=email,
        password_hash=hash_password(user_data.password),
        role=UserRole.CUSTOMER,
    )

    try:
        user = user_repository.create_user(db, user)
    except IntegrityError as error:
        db.rollback()

        raise exceptions.UserAlreadyExistsError(
            "A user with this email already exists."
        ) from error

    logger.info(
        "User registered successfully: user_id=%s",
        user.id,
    )

    return user


def login_user(
    db: Session,
    login_credentials: LoginRequest,
) -> str:
    """Authenticate a user and return an access token."""

    email = str(login_credentials.email).lower()

    if _is_login_locked(email):
        logger.warning("Login blocked due to repeated failed attempts")

        raise exceptions.RateLimitError(
            "Too many failed login attempts. Please try again later"
        )

    user = user_repository.get_user_by_email(
        db,
        email,
    )

    if user is None or not verify_password(
        login_credentials.password,
        user.password_hash,
    ):
        _record_failed_login(email)

        logger.warning("Failed login attempt")

        raise exceptions.AuthenticationError("Invalid email or password")

    _reset_failed_login(email)

    access_token = create_access_token(
        user_id=user.id,
        expires_in_minutes=settings.jwt_access_token_expire_minutes,
        role=user.role.value if user.role else UserRole.CUSTOMER.value,
    )

    logger.info(
        "User logged in successfully: user_id=%s",
        user.id,
    )

    return access_token
