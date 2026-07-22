import pytest
from unittest.mock import patch, AsyncMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.presentation.middleware.error_handler import setup_error_handlers
from app.application.exceptions import AppError
from app.domain.exceptions import AuthenticationFailure, UserAlreadyExistsError, InvalidCredentialsError

app = FastAPI()
setup_error_handlers(app)

@app.get("/app-error")
async def trigger_app_error():
    raise AppError(message="Test App Error", error_code="TEST_ERR", status_code=400)

@app.get("/user-exists")
async def trigger_user_exists():
    raise UserAlreadyExistsError(message="User exists")

@app.get("/auth-fail")
async def trigger_auth_fail():
    raise InvalidCredentialsError("Auth fail")

@app.get("/unhandled")
async def trigger_unhandled():
    raise Exception("Unknown error")

client = TestClient(app, raise_server_exceptions=False)

def test_app_error_handler():
    response = client.get("/app-error")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "TEST_ERR"

def test_user_already_exists_handler():
    response = client.get("/user-exists")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "USER_ALREADY_EXISTS"

@patch("app.presentation.middleware.error_handler.log_system_error", new_callable=AsyncMock)
def test_authentication_failure_handler(mock_log):
    mock_log.return_value = None
    response = client.get("/auth-fail")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"
    mock_log.assert_called_once()

@patch("app.presentation.middleware.error_handler.log_system_error", new_callable=AsyncMock)
def test_unhandled_exception_handler(mock_log):
    mock_log.return_value = None
    response = client.get("/unhandled")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
    mock_log.assert_called_once()
