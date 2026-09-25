"""Unit tests for password hashing and JWT security functions."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_returns_valid_argon2_hash() -> None:
    """Verify hash_password generates a non-empty Argon2 hash string."""

    # GIVEN: A plaintext password
    password = "SuperSecretPassword123!"

    # WHEN: Generating the password hash
    hashed = hash_password(password)

    # THEN: Output is a valid string distinct from plaintext containing Argon2 identifier
    assert isinstance(hashed, str)
    assert hashed != password
    assert "$argon2id$" in hashed


def test_verify_password_returns_true_for_matching_password() -> None:
    """Verify verify_password succeeds when given the correct plaintext password."""

    # GIVEN: A plaintext password and its Argon2 hash
    password = "CorrectHorseBatteryStaple"
    hashed = hash_password(password)

    # WHEN: Verifying the correct password
    is_valid = verify_password(password, hashed)

    # THEN: Verification succeeds and returns True
    assert is_valid is True


def test_verify_password_returns_false_for_incorrect_password() -> None:
    """Verify verify_password fails when given an incorrect plaintext password."""

    # GIVEN: A plaintext password and its corresponding Argon2 hash
    password = "OriginalPassword123"
    hashed = hash_password(password)

    # WHEN: Verifying with an incorrect password
    is_valid = verify_password("WrongPassword123", hashed)

    # THEN: Verification fails and returns False
    assert is_valid is False


def test_verify_password_returns_false_for_malformed_hash() -> None:
    """Verify verify_password returns False without crashing when given an invalid hash."""

    # GIVEN: A plaintext password and a malformed hash string
    password = "Password123"
    invalid_hash = "not_a_valid_argon2_hash_string"

    # WHEN: Verifying against the corrupted hash
    is_valid = verify_password(password, invalid_hash)

    # THEN: Verification catches exception and returns False
    assert is_valid is False


def test_create_access_token_returns_signed_jwt() -> None:
    """Verify create_access_token generates a valid JWT with subject and expiry claims."""

    # GIVEN: A user ID and expiration window
    user_id = 42
    expires_in_minutes = 15

    # WHEN: Generating an access token
    token = create_access_token(user_id=user_id, expires_in_minutes=expires_in_minutes)

    # THEN: Token decodes successfully and contains expected claims
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert payload["purpose"] == "access"
    assert payload["role"] == "CUSTOMER"
    assert payload["iss"] == settings.jwt_issuer
    assert payload["ver"] == settings.jwt_token_version
    assert "exp" in payload


def test_decode_access_token_success() -> None:
    """Verify decode_access_token parses valid signed tokens cleanly."""

    # GIVEN: A validly generated access token
    user_id = 100
    token = create_access_token(user_id=user_id, expires_in_minutes=30)

    # WHEN: Decoding the token
    payload = decode_access_token(token)

    # THEN: Claims match encoded values
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert payload["purpose"] == "access"
    assert payload["role"] == "CUSTOMER"


def test_decode_access_token_raises_error_for_wrong_issuer() -> None:
    """Verify decode_access_token rejects tokens issued by another service."""

    # GIVEN: A validly signed access token issued by another service
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    token = jwt.encode(
        {
            "sub": "42",
            "exp": expires_at,
            "iss": "another-service",
            "type": "access",
            "purpose": "access",
            "role": "CUSTOMER",
            "ver": settings.jwt_token_version,
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    # WHEN: Decoding the token
    # THEN: InvalidTokenError is raised because the issuer is not trusted
    with pytest.raises(InvalidTokenError, match="Invalid access token"):
        decode_access_token(token)


def test_decode_access_token_raises_error_for_invalid_type() -> None:
    """Verify decode_access_token raises InvalidTokenError if payload type is not 'access'."""

    # GIVEN: A signed token with a non-access type claim
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    invalid_type_payload = {
        "sub": "42",
        "exp": expires_at,
        "iss": settings.jwt_issuer,
        "type": "refresh",
        "purpose": "refresh",
        "role": "CUSTOMER",
        "ver": settings.jwt_token_version,
    }
    token = jwt.encode(
        invalid_type_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    # WHEN/THEN: Decoding raises InvalidTokenError due to claim mismatch
    with pytest.raises(InvalidTokenError, match="Invalid token type"):
        decode_access_token(token)


def test_decode_access_token_raises_error_when_expired() -> None:
    """Verify decode_access_token raises InvalidTokenError for expired signatures."""

    # GIVEN: A token generated with a timestamp in the past
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    expired_payload = {
        "sub": "42",
        "exp": expired_time,
        "iss": settings.jwt_issuer,
        "type": "access",
        "purpose": "access",
        "role": "CUSTOMER",
        "ver": settings.jwt_token_version,
    }
    token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    # WHEN: The `decode_access_token` function is called with an expired token
    # THEN: We expect the service raises InvalidTokenError due to expiration
    with pytest.raises(InvalidTokenError, match="Token has expired."):
        decode_access_token(token)


def test_decode_access_token_raises_error_for_malformed_token() -> None:
    """Verify decode_access_token raises InvalidTokenError when given garbage strings."""

    # GIVEN: An invalid JWT string
    invalid_token = "invalid.jwt.token_string"

    # WHEN: # WHEN: The `decode_access_token` function is called with an expired token
    # THEN: # THEN: We expect the service raises InvalidTokenError due to expiration
    with pytest.raises(InvalidTokenError):
        decode_access_token(invalid_token)
