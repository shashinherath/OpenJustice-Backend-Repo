import os
os.environ.setdefault("OPENAI_API_KEY", "test-key")

import pytest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

from app.application.dtos.auth_dto import LoginDto
from app.application.services.auth_service import AuthService
from app.core.exceptions import AuthenticationError
from app.core.security.password_hasher import hash_password


@pytest.mark.asyncio
async def test_login_success_with_email():
    repo = AsyncMock()
    user = SimpleNamespace(
        uuid=uuid4(),
        role="user",
        preferred_language="en",
        hashed_password=hash_password("secret123"),
    )
    repo.get_by_email.return_value = user

    service = AuthService(repository=repo)
    result = await service.login(
        LoginDto(email="user@example.com", phone_number=None, password="secret123")
    )

    assert result.uuid == user.uuid
    assert result.role == "user"
    assert result.access_token
    repo.get_by_email.assert_awaited_once_with("user@example.com")


@pytest.mark.asyncio
async def test_login_unknown_user_raises():
    repo = AsyncMock()
    repo.get_by_email.return_value = None

    service = AuthService(repository=repo)

    with pytest.raises(AuthenticationError):
        await service.login(
            LoginDto(email="missing@example.com", phone_number=None, password="secret123")
        )


@pytest.mark.asyncio
async def test_login_wrong_password_raises():
    repo = AsyncMock()
    user = SimpleNamespace(
        uuid=uuid4(),
        role="user",
        preferred_language="en",
        hashed_password=hash_password("correct-password"),
    )
    repo.get_by_phone.return_value = user

    service = AuthService(repository=repo)

    with pytest.raises(AuthenticationError):
        await service.login(
            LoginDto(email=None, phone_number="+15551234567", password="wrong-password")
        )
    repo.get_by_phone.assert_awaited_once_with("+15551234567")
