"""Domain exceptions."""

from app.domain.exceptions.auth import (
    AuthenticationFailure,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    UserAlreadyExistsError,
)
from app.domain.exceptions.base import DomainError

__all__ = [
    "AuthenticationFailure",
    "DomainError",
    "InvalidCredentialsError",
    "InvalidTokenError",
    "TokenExpiredError",
    "UserAlreadyExistsError",
]
