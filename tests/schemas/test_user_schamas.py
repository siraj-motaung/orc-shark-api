"""Unit tests for user Pydantic schemas validation rules."""

import pytest
from pydantic import ValidationError

from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse


def test_user_create_valid_payload():
    """Verify that a valid user registration payload passes validation."""
    # GIVEN: A payload dictionary with matching passwords and valid attributes

    payload = {
        "name": "   Siraj Prince   ",
        "email": "siraj@gmail.com",
        "password": "securepassword123",
        "confirm_password": "securepassword123",
    }

    # WHEN: Instantiating the UserCreate schema
    schema = UserCreate(**payload)

    # THEN: Validation succeeds and the name is stripped of surrounding whitespace
    assert schema.name == "Siraj Prince"
    assert schema.email == "siraj@gmail.com"
    assert schema.password == "securepassword123"


def test_user_create_password_mismatch_raises_error():
    """Verify that a model validator raises an error when passwords do not match."""

    # GIVEN: A payload where password and confirm_password differ
    payload = {
        "name": "Siraj Prince",
        "email": "siraj@gmail.com",
        "password": "securepassword123",
        "confirm_password": "differentpassword",
    }

    # WHEN/THEN: Instantiating UserCreate raises a ValidationError
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**payload)

    assert "Passwords do not match." in str(exc_info.value)


@pytest.mark.parametrize(
    "invalid_email",
    [
        "invalid-email",
        "missing-at-domain.com",
        "@no-username.com",
    ],
)
def test_user_create_invalid_email_format(invalid_email: str):
    """Verify that invalid email strings fail EmailStr validation."""

    # GIVEN: A payload containing an improperly formatted email address
    payload = {
        "name": "Valid Name",
        "email": invalid_email,
        "password": "securepassword123",
        "confirm_password": "securepassword123",
    }

    # WHEN/THEN: Instantiating UserCreate raises a ValidationError
    with pytest.raises(ValidationError):
        UserCreate(**payload)


@pytest.mark.parametrize(
    "name, error_substring",
    [
        ("   ", "Name cannot be empty."),
        ("a" * 101, "String should have at most 100 characters"),
    ],
)
def test_user_create_invalid_name_constraints(name: str, error_substring: str):
    """Verify name length constraints and empty string rejection."""

    # GIVEN: A payload with an invalid name string
    payload = {
        "name": name,
        "email": "test@example.com",
        "password": "securepassword123",
        "confirm_password": "securepassword123",
    }

    # WHEN/THEN: Instantiating UserCreate raises a ValidationError
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**payload)

    assert error_substring in str(exc_info.value)


@pytest.mark.parametrize(
    "password, error_substring",
    [
        ("short", "String should have at least 8 characters"),
        ("        ", "Password cannot contain only whitespace."),
        ("a" * 129, "String should have at most 128 characters"),
    ],
)
def test_user_create_invalid_password_constraints(password: str, error_substring: str):
    """Verify password min/max length rules and whitespace-only checks."""

    # GIVEN: A payload with a password violating constraint rules
    payload = {
        "name": "Valid Name",
        "email": "test@example.com",
        "password": password,
        "confirm_password": password,
    }

    # WHEN/THEN: Instantiating UserCreate raises a ValidationError
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**payload)

    assert error_substring in str(exc_info.value)


def test_user_response_serialization_from_dict():
    """Verify UserResponse correctly parses valid dictionary."""

    # GIVEN: A complete user payload dictionary
    payload = {
        "id": 1,
        "name": "Siraj Prince",
        "email": "siraj@gmail.com",
    }

    # WHEN: Instantiating UserResponse
    schema = UserResponse(**payload)

    # THEN: All attributes match expected values
    assert schema.id == 1
    assert schema.name == "Siraj Prince"
    assert schema.email == "siraj@gmail.com"


def test_login_request_valid_payload():
    """Verify LoginRequest succeeds with valid email and password format."""

    # GIVEN: A dictionary with valid email and password length
    payload = {
        "email": "siraj@gmail.com",
        "password": "securepassword123",
    }

    # WHEN: Instantiating LoginRequest
    schema = LoginRequest(**payload)

    # THEN: Attributes match input values
    assert schema.email == "siraj@gmail.com"
    assert schema.password == "securepassword123"


def test_login_request_invalid_password_length():
    """Verify LoginRequest enforces password minimum length constraints."""

    # GIVEN: A login payload with a short password (<8 chars)
    payload = {
        "email": "siraj@gmail.com",
        "password": "short",
    }

    # WHEN/THEN: Instantiating LoginRequest raises a ValidationError
    with pytest.raises(ValidationError) as exc_info:
        LoginRequest(**payload)

    assert "String should have at least 8 characters" in str(exc_info.value)


def test_token_response_defaults():
    """Verify TokenResponse sets default token_type to 'bearer'."""

    # GIVEN: A token payload supplying only the access_token
    payload = {
        "access_token": "access_token",
    }

    # WHEN: Instantiating TokenResponse
    schema = TokenResponse(**payload)

    # THEN: access_token matches and token_type defaults to "bearer"
    assert schema.access_token == "access_token"
    assert schema.token_type == "bearer"
