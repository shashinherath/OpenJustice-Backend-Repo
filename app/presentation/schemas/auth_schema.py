"""Authentication request/response schemas."""
import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


_PHONE_E164 = re.compile(r"^\+\d{7,15}$")


class LoginRequest(BaseModel):
    """Login request payload."""

    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: str = Field(min_length=8, max_length=128)
    recaptcha_token: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not _PHONE_E164.match(value):
            raise ValueError("phone_number must be in E.164 format, e.g. +15551234567")
        return value

    @model_validator(mode="after")
    def validate_contact_method(self) -> "LoginRequest":
        has_email = self.email is not None
        has_phone = self.phone_number is not None
        if not has_email and not has_phone:
            raise ValueError("Provide at least one of email or phone_number")
        return self


class LoginResponseData(BaseModel):
    """Login response data."""

    uuid: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    preferred_language: str
    access_token: str

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    """Register request payload."""

    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: str = Field(min_length=8, max_length=128)
    preferred_language: str = Field(default="en", max_length=10)
    recaptcha_token: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not _PHONE_E164.match(value):
            raise ValueError("phone_number must be in E.164 format, e.g. +15551234567")
        return value

    @model_validator(mode="after")
    def validate_contact_method(self) -> "RegisterRequest":
        has_email = self.email is not None
        has_phone = self.phone_number is not None
        if not has_email and not has_phone:
            raise ValueError("Provide at least one of email or phone_number")
        return self


class RegisterResponseData(BaseModel):
    """Register response data."""

    uuid: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    preferred_language: str

    model_config = ConfigDict(from_attributes=True)
