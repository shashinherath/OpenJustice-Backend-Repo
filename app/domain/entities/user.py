"""Domain user entity definitions."""
from enum import Enum


class UserRole(str, Enum):
    """User roles supported by the system."""

    USER = "user"
    ADMIN = "admin"
    RESEARCHER = "researcher"
