"""Unit tests for API exception handlers."""

import json

from fastapi import Request
from fastapi.exceptions import RequestValidationError

from app.api.exception_handlers import handle_validation_error


def test_validation_error_preserves_full_location_and_message() -> None:
    """Verify validation responses retain nested locations and Pydantic messages."""

    # GIVEN: A validation error for a nested request field
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/test",
            "headers": [],
        }
    )
    error = RequestValidationError(
        [
            {
                "loc": ("body", "items", 0, "rating"),
                "msg": "Value error, Rating must be between 1 and 5.",
            }
        ]
    )

    # WHEN: The validation error handler builds the response
    response = handle_validation_error(request, error)

    # THEN: The response preserves the full field location and original message
    assert response.status_code == 422
    assert json.loads(response.body) == {
        "error_message": "Validation failed.",
        "errors": [
            {
                "field": "body.items.0.rating",
                "message": "Value error, Rating must be between 1 and 5.",
            }
        ],
    }
