import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.application.dtos.auth_dto import LoginResultDto, RegisterResultDto
from app.infrastructure.db.base import get_db
from app.infrastructure.models.system_settings import SystemSettings

async def override_get_db():
    yield AsyncMock()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture
def mock_auth_service():
    with patch("app.presentation.controllers.auth_controller.AuthService") as mock:
        service_instance = AsyncMock()
        mock.return_value = service_instance
        yield service_instance

@pytest.fixture
def mock_user_service():
    with patch("app.presentation.controllers.auth_controller.UserService") as mock:
        service_instance = AsyncMock()
        mock.return_value = service_instance
        yield service_instance

@pytest.fixture
def mock_system_settings():
    with patch("app.presentation.controllers.auth_controller.SystemSettingsRepository") as mock:
        repo_instance = AsyncMock()
        mock_settings = SystemSettings(jwt_expiry_minutes=60)
        repo_instance.get_settings.return_value = mock_settings
        mock.return_value = repo_instance
        yield repo_instance

from app.infrastructure.security.jwt_handler import jwt_handler

@pytest.fixture
def auth_headers():
    token = jwt_handler.create_access_token(data={"sub": str(uuid4())})
    return {"Authorization": f"Bearer {token}"}


def test_login_success(mock_auth_service, mock_system_settings):
    user_id = uuid4()
    mock_auth_service.login.return_value = LoginResultDto(
        access_token="test_token_123", uuid=user_id, first_name="Test",
        last_name="User", role="user", preferred_language="en"
    )
    response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200

def test_register_success(mock_auth_service):
    user_id = uuid4()
    mock_auth_service.register.return_value = RegisterResultDto(
        uuid=user_id, first_name="Test", last_name="User", role="user", preferred_language="en"
    )
    response = client.post("/api/auth/register", json={
        "first_name": "Test", "last_name": "User", "email": "test@example.com", "password": "password123"
    })
    assert response.status_code == 201

def test_verify_email(mock_auth_service):
    response = client.post("/api/auth/verify-email", json={"token": "test-token"})
    assert response.status_code == 200

def test_resend_verification(mock_auth_service):
    response = client.post("/api/auth/resend-verification", json={"email": "test@example.com"})
    assert response.status_code == 200

def test_logout(mock_auth_service, auth_headers):
    response = client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == 200

def test_get_current_user_profile(mock_user_service, auth_headers):
    mock_user_service.get_profile.return_value = {
        "uuid": str(uuid4()), "first_name": "John", "last_name": "Doe",
        "role": "admin", "preferred_language": "en", "avatar_url": None, "email": "j@example.com"
    }
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200

def test_update_current_user_profile(mock_user_service, auth_headers):
    mock_user_service.update_profile.return_value = {
        "uuid": str(uuid4()), "first_name": "Jane", "last_name": "Doe",
        "role": "admin", "preferred_language": "en", "avatar_url": None, "email": "j@example.com"
    }
    response = client.patch("/api/auth/users/me", json={"first_name": "Jane"}, headers=auth_headers)
    assert response.status_code == 200

@patch("app.presentation.controllers.auth_controller._get_storage_handler")
def test_upload_current_user_avatar(mock_storage, mock_user_service, auth_headers):
    mock_user_service.upload_avatar.return_value = {
        "uuid": str(uuid4()), "first_name": "Jane", "last_name": "Doe",
        "role": "admin", "preferred_language": "en", "avatar_url": "http://img", "email": "j@example.com"
    }
    response = client.post(
        "/api/auth/users/me/avatar",
        files={"file": ("test.png", b"data", "image/png")},
        headers=auth_headers
    )
    assert response.status_code == 200

def test_change_user_password(mock_user_service, auth_headers):
    response = client.post("/api/auth/change-password", json={
        "current_password": "old_password_123",
        "new_password": "new_password_123"
    }, headers=auth_headers)
    assert response.status_code == 200
