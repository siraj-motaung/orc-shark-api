class AppError(Exception):
    """Base exception for expected application errors."""

    def __init__(self, message: str) -> None:
        self.message = message

        super().__init__(message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    status_code = 404
    code = "NOT_FOUND"


class DishNotFoundError(NotFoundError):
    code = "DISH_NOT_FOUND"


class ConflictError(AppError):
    """Raised when a request conflicts with the current application state."""

    status_code = 409
    code = "CONFLICT"


class UserAlreadyExistsError(ConflictError):
    """Raised when attempting to register an existing user."""

    code = "USER_ALREADY_EXISTS"


class RatingAlreadyExistsError(ConflictError):
    """Raised when a user has already rated a dish."""

    code = "RATING_ALREADY_EXISTS"


class AuthenticationError(AppError):
    """Raise when authentication credentials are invalid"""

    status_code = 401
    code = "INVALID_CREDENTIALS"


class AuthorizationError(AppError):
    """Raised when an authenticated user lacks permission."""

    status_code = 403
    code = "FORBIDDEN"


class RateLimitError(AppError):
    """Raise when a client exceeds an allowed request threshold"""

    status_code = 429
    code = "TOO_MANY_ATTEMPTS"
