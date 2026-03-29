"""Authentication-related domain exceptions."""

from app.domain.exceptions.base import DomainError


class AuthenticationFailure(DomainError):
    """Base for failures when establishing or validating identity."""


class InvalidCredentialsError(AuthenticationFailure):
    """Raised when credentials do not match a valid user."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        self.message = message
        super().__init__(message)


class TokenExpiredError(AuthenticationFailure):
    """Raised when a security token has expired."""

    def __init__(self, message: str = "Token has expired") -> None:
        self.message = message
        super().__init__(message)


class InvalidTokenError(AuthenticationFailure):
    """Raised when a security token cannot be validated."""

    def __init__(self, message: str = "Could not validate credentials") -> None:
        self.message = message
        super().__init__(message)


class UserAlreadyExistsError(DomainError):
    """Raised when attempting to register with an email or phone already in use."""

    def __init__(self, message: str = "A user with this identifier already exists") -> None:
        self.message = message
        super().__init__(message)
