"""A module containing exception handlers for application and unexpected errors."""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


async def handle_app_error(
    request: Request,
    error: AppError,
) -> JSONResponse:
    """Handle expected application errors."""

    return JSONResponse(
        status_code=error.status_code,
        content={"error_message": error.message, "code": error.code},
    )


async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    """Handle unexpected errors without exposing implementation details."""

    logger.exception(
        "Unhandled application error while processing request: %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error_message": ("An unexpected error occurred. Please try again later."),
        },
    )


async def handle_validation_error(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    """Handle request validation errors consistently."""

    errors = []

    for validation_error in error.errors():
        message = validation_error["msg"]

        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")

        errors.append(
            {
                "field": validation_error["loc"][-1],
                "message": message,
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error_message": "Validation failed.",
            "errors": errors,
        },
    )
