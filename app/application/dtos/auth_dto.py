"""Authentication DTOs."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class LoginDto:
    email: Optional[str]
    phone_number: Optional[str]
    password: str


@dataclass(frozen=True)
class LoginResultDto:
    access_token: str
    uuid: UUID
    role: str
    preferred_language: str


@dataclass(frozen=True)
class RegisterDto:
    email: Optional[str]
    phone_number: Optional[str]
    password: str
    preferred_language: str = "en"


@dataclass(frozen=True)
class RegisterResultDto:
    uuid: UUID
    role: str
    preferred_language: str
