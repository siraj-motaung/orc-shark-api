"""A Module containing FastAPI dependencies for authentication and authorization."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import InvalidTokenError, decode_access_token
from app.db.database import get_session
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_session),
) -> User:
    """Return the authenticated user presented by the JWT."""

    jwt_token = credentials.credentials

    try:
        payload = decode_access_token(token=jwt_token)
    except InvalidTokenError:
        raise AuthenticationError("Invalid authentication token.")

    subject = payload.get("sub")

    if subject is None:
        raise AuthenticationError("Invalid authentication token.")

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise AuthenticationError("Invalid authentication token.")

    user = db.scalar(select(User).where(User.id == user_id))

    if user is None:
        raise AuthenticationError("Invalid authentication token.")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require the authenticated user to have the admin role"""

    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("You do not have permission to perform this action.")

    return current_user
