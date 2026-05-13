"""User request/response schemas."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfileResponse(BaseModel):
    """User profile response data."""

    uuid: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: str
    preferred_language: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdateRequest(BaseModel):
    """User profile update request payload."""

    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    preferred_language: Optional[str] = Field(default=None, max_length=10)
    avatar_url: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class ChangePasswordRequest(BaseModel):
    """Change password request payload."""

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(extra="forbid")
