"""Authentication service."""
from app.application.dtos.auth_dto import LoginDto, LoginResultDto
from app.domain.exceptions import InvalidCredentialsError
from app.domain.interfaces.password_hasher import PasswordHasher
from app.domain.interfaces.token_issuer import AccessTokenIssuer
from app.domain.interfaces.user_repository import IUserRepository


class AuthService:
    """Business logic for authentication."""

    def __init__(
        self,
        repository: IUserRepository,
        password_hasher: PasswordHasher,
        token_issuer: AccessTokenIssuer,
    ) -> None:
        self.repository = repository
        self.password_hasher = password_hasher
        self.token_issuer = token_issuer

    async def login(self, dto: LoginDto) -> LoginResultDto:
        """Authenticate a user and return a login result."""
        user = None
        if dto.email:
            user = await self.repository.get_by_email(dto.email)
        elif dto.phone_number:
            user = await self.repository.get_by_phone(dto.phone_number)

        if not user or not user.hashed_password:
            raise InvalidCredentialsError()

        if not self.password_hasher.verify_password(dto.password, user.hashed_password):
            raise InvalidCredentialsError()

        token = self.token_issuer.create_access_token(
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
