"""Bcrypt password hashing (infrastructure)."""
from passlib.context import CryptContext

from app.domain.interfaces.password_hasher import PasswordHasher


class BcryptPasswordHasher:
    """Password hashing using bcrypt via passlib."""

    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password."""
        return self._context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a hash."""
        return self._context.verify(plain_password, hashed_password)
