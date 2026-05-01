"""Authentication service."""
from app.application.dtos.auth_dto import (
    LoginDto,
    LoginResultDto,
    RegisterDto,
    RegisterResultDto,
)
from app.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.domain.interfaces.password_hasher import PasswordHasher
from app.domain.interfaces.token_issuer import AccessTokenIssuer
from app.domain.interfaces.user_repository import IUserRepository
from app.infrastructure.models.user import User
from app.domain.interfaces.user_session_repository import IUserSessionRepository
from app.domain.interfaces.audit_log_repository import IAuditLogRepository
import uuid


class AuthService:
    """Business logic for authentication."""

    def __init__(
        self,
        repository: IUserRepository,
        password_hasher: PasswordHasher,
        token_issuer: AccessTokenIssuer,
        user_session_repo: IUserSessionRepository = None,
        audit_log_repo: IAuditLogRepository = None,
    ) -> None:
        self.repository = repository
        self.password_hasher = password_hasher
        self.token_issuer = token_issuer
        self.user_session_repo = user_session_repo
        self.audit_log_repo = audit_log_repo

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
                "sub": str(user.id),
                "role": user.role,
                "preferred_language": user.preferred_language,
            }
        )

        if self.user_session_repo:
            session_token = uuid.uuid4()
            await self.user_session_repo.create_session(
                user_id=user.id,
                session_token=session_token,
                channel=dto.channel,
                ip_address=dto.ip_address,
                user_agent=dto.user_agent
            )
            
        if self.audit_log_repo:
            await self.audit_log_repo.log_action(
                user_id=user.id,
                action="USER_LOGIN",
                metadata={"channel": dto.channel, "ip_address": dto.ip_address}
            )

        return LoginResultDto(
            access_token=token,
            uuid=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            preferred_language=user.preferred_language,
        )

    async def register(self, dto: RegisterDto) -> RegisterResultDto:
        """Register a new user and return a login result (auto-login)."""
        # Check for existing user
        if dto.email:
            existing = await self.repository.get_by_email(dto.email)
            if existing:
                raise UserAlreadyExistsError("A user with this email already exists")
        if dto.phone_number:
            existing = await self.repository.get_by_phone(dto.phone_number)
            if existing:
                raise UserAlreadyExistsError("A user with this phone number already exists")

        # Hash password and create user model
        hashed_password = self.password_hasher.hash_password(dto.password)
        user = User(
            first_name=dto.first_name,
            last_name=dto.last_name,
            email=dto.email,
            phone_number=dto.phone_number,
            hashed_password=hashed_password,
            preferred_language=dto.preferred_language,
        )

        # Persist
        user = await self.repository.create(user)
        
        if self.audit_log_repo:
            await self.audit_log_repo.log_action(
                user_id=user.id,
                action="USER_REGISTER",
                metadata={"email": dto.email}
            )

        return RegisterResultDto(
            uuid=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            preferred_language=user.preferred_language,
        )
