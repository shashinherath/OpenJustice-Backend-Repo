import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import datetime, timezone, timedelta

from app.application.services.auth_service import AuthService
from app.application.dtos.auth_dto import LoginDto, RegisterDto
from app.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.infrastructure.models.user import User

@pytest.fixture
def mock_user_repo():
    return AsyncMock()

@pytest.fixture
def mock_password_hasher():
    hasher = MagicMock()
    hasher.verify_password.return_value = True
    hasher.hash_password.return_value = "hashed_pw"
    return hasher

@pytest.fixture
def mock_token_issuer():
    issuer = MagicMock()
    issuer.create_access_token.return_value = "mocked_jwt_token"
    return issuer

@pytest.fixture
def auth_service(mock_user_repo, mock_password_hasher, mock_token_issuer):
    return AuthService(
        repository=mock_user_repo,
        password_hasher=mock_password_hasher,
        token_issuer=mock_token_issuer
    )

@pytest.mark.asyncio
async def test_login_success(auth_service, mock_user_repo):
    """Test successful login with email."""
    # Arrange
    user_id = uuid.uuid4()
    mock_user = User(
        id=user_id,
        email="test@example.com",
        hashed_password="hashed_pw",
        role="user",
        preferred_language="en",
        is_email_verified=True,
        failed_login_attempts=0,
        locked_until=None
    )
    mock_user_repo.get_by_email.return_value = mock_user

    dto = LoginDto(
        email="test@example.com",
        phone_number=None,
        password="password123"
    )

    # Act
    result = await auth_service.login(dto)

    # Assert
    assert result.access_token == "mocked_jwt_token"
    assert result.uuid == user_id
    assert result.role == "user"
    mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
    auth_service.password_hasher.verify_password.assert_called_once_with("password123", "hashed_pw")


@pytest.mark.asyncio
async def test_login_unverified_email(auth_service, mock_user_repo):
    """Test login failure when email is not verified."""
    # Arrange
    mock_user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed_pw",
        is_email_verified=False
    )
    mock_user_repo.get_by_email.return_value = mock_user

    dto = LoginDto(
        email="test@example.com",
        phone_number=None,
        password="password123"
    )

    # Act & Assert
    with pytest.raises(InvalidCredentialsError, match="verify your email"):
        await auth_service.login(dto)


@pytest.mark.asyncio
async def test_register_success(auth_service, mock_user_repo, mock_password_hasher):
    """Test successful registration."""
    # Arrange
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.get_by_phone.return_value = None
    
    # Mock create to return the user with an ID
    def mock_create(user):
        user.id = uuid.uuid4()
        return user
    mock_user_repo.create.side_effect = mock_create

    dto = RegisterDto(
        first_name="John",
        last_name="Doe",
        email="new@example.com",
        phone_number=None,
        password="password123",
        preferred_language="en"
    )

    # Act
    result = await auth_service.register(dto)

    # Assert
    assert result.uuid is not None
    assert result.first_name == "John"
    assert result.preferred_language == "en"
    mock_user_repo.get_by_email.assert_called_once_with("new@example.com")
    mock_password_hasher.hash_password.assert_called_once_with("password123")


@pytest.mark.asyncio
async def test_register_existing_user(auth_service, mock_user_repo):
    """Test registration failure when email already exists."""
    # Arrange
    mock_user_repo.get_by_email.return_value = User(email="existing@example.com")

    dto = RegisterDto(
        first_name="Jane",
        last_name="Doe",
        email="existing@example.com",
        phone_number=None,
        password="password123",
        preferred_language="en"
    )

    # Act & Assert
    with pytest.raises(UserAlreadyExistsError, match="email already exists"):
        await auth_service.register(dto)
