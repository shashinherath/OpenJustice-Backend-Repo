"""Application-specific exceptions."""
from dataclasses import dataclass


@dataclass
class AppError(Exception):
    """Base application error with HTTP metadata."""

    message: str
    status_code: int
    error_code: str

    def __str__(self) -> str:  # pragma: no cover - simple wrapper
        return self.message


class AuthenticationError(AppError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message=message, status_code=401, error_code="AUTHENTICATION_ERROR")
