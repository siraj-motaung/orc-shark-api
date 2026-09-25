"A module containing security utilities for password hashing and JWT handling"

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from jwt.exceptions import ExpiredSignatureError, PyJWTError

from app.core.config import settings


class InvalidTokenError(Exception):
    """Raised when a JWT cannot be validated."""


password_hasher = PasswordHasher()

ACCESS_TOKEN_EXPIRES_MINUTES = 30


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2."""

    return password_hasher.hash(password=password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against an Argo2 password hash."""

    try:
        return password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(
    user_id: int,
    expires_in_minutes: int,
    role: str = "CUSTOMER",
) -> str:
    """Create a signed JWT access token for a user."""

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
        "iss": settings.jwt_issuer,
        "type": "access",
        "purpose": "access",
        "role": role,
        "ver": settings.jwt_token_version,
    }

    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token."""

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={
                "require": [
                    "sub",
                    "exp",
                    "iss",
                    "type",
                    "purpose",
                    "role",
                    "ver",
                ]
            },
        )
    except ExpiredSignatureError as error:
        raise InvalidTokenError("Token has expired.") from error
    except PyJWTError as error:
        raise InvalidTokenError("Invalid access token.") from error

    if payload.get("type") != "access" or payload.get("purpose") != "access":
        raise InvalidTokenError("Invalid token type.")

    if payload.get("ver") != settings.jwt_token_version:
        raise InvalidTokenError("Unsupported token version.")

    return payload
