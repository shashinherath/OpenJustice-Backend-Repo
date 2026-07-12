"""Authentication service."""
from app.application.dtos.auth_dto import (
    LoginDto,
    LoginResultDto,
    RegisterDto,
    RegisterResultDto,
    LogoutDto,
)
from app.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.domain.interfaces.password_hasher import PasswordHasher
from app.domain.interfaces.token_issuer import AccessTokenIssuer
from app.domain.interfaces.user_repository import IUserRepository
from app.infrastructure.models.user import User
from app.domain.interfaces.user_session_repository import IUserSessionRepository
from app.domain.interfaces.audit_log_repository import IAuditLogRepository
from app.domain.interfaces.recaptcha_verifier import IRecaptchaVerifier
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
from datetime import datetime, timezone, timedelta
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
        system_settings_repo: SystemSettingsRepository = None,
        recaptcha_verifier: IRecaptchaVerifier = None,
    ) -> None:
        self.repository = repository
        self.password_hasher = password_hasher
        self.token_issuer = token_issuer
        self.user_session_repo = user_session_repo
        self.audit_log_repo = audit_log_repo
        self.system_settings_repo = system_settings_repo
        self.recaptcha_verifier = recaptcha_verifier

    async def login(self, dto: LoginDto) -> LoginResultDto:
        """Authenticate a user and return a login result."""
        if self.recaptcha_verifier:
            is_human = await self.recaptcha_verifier.verify(
                token=dto.recaptcha_token,
                ip_address=dto.ip_address
            )
            if not is_human:
                raise InvalidCredentialsError("Bot activity detected or invalid captcha.")

        user = None
        if dto.email:
            user = await self.repository.get_by_email(dto.email)
        elif dto.phone_number:
            user = await self.repository.get_by_phone(dto.phone_number)

        if not user or not user.hashed_password:
            raise InvalidCredentialsError()

        # Check Lockout
        sys_settings = None
        if self.system_settings_repo:
            sys_settings = await self.system_settings_repo.get_settings()
        
        now = datetime.now(timezone.utc)
        if user.locked_until and user.locked_until > now:
            raise InvalidCredentialsError(f"Account is temporarily locked. Try again later.")
        elif user.locked_until and user.locked_until <= now:
            user.locked_until = None
            user.failed_login_attempts = 0
            if hasattr(self.repository, 'db'):
                await self.repository.db.commit()

        if not self.password_hasher.verify_password(dto.password, user.hashed_password):
            user.failed_login_attempts += 1
            if sys_settings and user.failed_login_attempts >= sys_settings.account_lockout_threshold:
                user.locked_until = now + timedelta(minutes=15)
                if self.audit_log_repo:
                    await self.audit_log_repo.log_action(user.id, "ACCOUNT_LOCKED", {"attempts": user.failed_login_attempts})
            if hasattr(self.repository, 'db'):
                await self.repository.db.commit()
            raise InvalidCredentialsError()

        # Reset failed attempts on success
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
            if hasattr(self.repository, 'db'):
                await self.repository.db.commit()

        token = self.token_issuer.create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role,
                "preferred_language": user.preferred_language,
            },
            expires_delta=timedelta(minutes=sys_settings.jwt_expiry_minutes) if sys_settings else None
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
        if self.recaptcha_verifier:
            is_human = await self.recaptcha_verifier.verify(
                token=dto.recaptcha_token,
                ip_address=dto.ip_address
            )
            if not is_human:
                raise InvalidCredentialsError("Bot activity detected or invalid captcha.")

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

    async def logout(self, dto: LogoutDto) -> None:
        """Log out a user and clean up session data."""
        if self.audit_log_repo:
            await self.audit_log_repo.log_action(
                user_id=dto.user_id,
                action="USER_LOGOUT",
                metadata={"channel": dto.channel, "ip_address": dto.ip_address}
            )
