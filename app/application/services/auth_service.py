"""Authentication service."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth_dto import LoginDto, LoginResultDto
from app.core.exceptions import AuthenticationError
from app.core.security.jwt_handler import jwt_handler
from app.core.security.password_hasher import verify_password
from app.domain.interfaces.user_repository import IUserRepository
from app.infrastructure.repositories.user_repository import UserRepository


class AuthService:
    """Business logic for authentication."""

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        repository: Optional[IUserRepository] = None,
    ) -> None:
        if repository is None:
            if db is None:
                raise ValueError("Either db or repository must be provided")
            self.repository = UserRepository(db)
        else:
            self.repository = repository

    async def login(self, dto: LoginDto) -> LoginResultDto:
        """Authenticate a user and return a login result."""
        user = None
        if dto.email:
            user = await self.repository.get_by_email(dto.email)
        elif dto.phone_number:
            user = await self.repository.get_by_phone(dto.phone_number)

        if not user or not user.hashed_password:
            raise AuthenticationError()

        if not verify_password(dto.password, user.hashed_password):
            raise AuthenticationError()

        token = jwt_handler.create_access_token(
            data={
                "sub": str(user.uuid),
                "role": user.role,
                "preferred_language": user.preferred_language,
            }
        )

        return LoginResultDto(
            access_token=token,
            uuid=user.uuid,
            role=user.role,
            preferred_language=user.preferred_language,
        )
