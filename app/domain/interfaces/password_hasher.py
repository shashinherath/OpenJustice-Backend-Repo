"""Password hashing contract (implemented in infrastructure)."""
from typing import Protocol


class PasswordHasher(Protocol):
    """Hash and verify passwords without exposing algorithm details."""

    def hash_password(self, password: str) -> str:
        """Return a secure hash of the plaintext password."""
        ...

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Return True if the plaintext matches the stored hash."""
        ...
