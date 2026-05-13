"""User-related data transfer objects."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class GetProfileDto:
    """DTO for fetching user profile."""
    user_id: UUID


@dataclass(frozen=True)
class UpdateProfileDto:
    """DTO for updating user profile."""
    user_id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    preferred_language: Optional[str] = None
    avatar_url: Optional[str] = None


@dataclass(frozen=True)
class ChangePasswordDto:
    """DTO for changing user password."""
    user_id: UUID
    current_password: str
    new_password: str
