"""Authentication DTOs."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class LoginDto:
    email: Optional[str]
    phone_number: Optional[str]
    password: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    channel: str = "web"


@dataclass(frozen=True)
class LoginResultDto:
    access_token: str
    uuid: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    preferred_language: str


@dataclass(frozen=True)
class RegisterDto:
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    password: str
    preferred_language: str = "en"


@dataclass(frozen=True)
class RegisterResultDto:
    uuid: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    preferred_language: str


@dataclass(frozen=True)
class LogoutDto:
    user_id: UUID
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    channel: str = "web"
