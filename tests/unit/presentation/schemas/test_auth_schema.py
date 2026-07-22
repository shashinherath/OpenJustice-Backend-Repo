import pytest
from pydantic import ValidationError
from app.presentation.schemas.auth_schema import LoginRequest, RegisterRequest

def test_login_request_valid_email():
    req = LoginRequest(email="test@test.com", password="password123")
    assert req.email == "test@test.com"

def test_login_request_valid_phone():
    req = LoginRequest(phone_number="+15551234567", password="password123")
    assert req.phone_number == "+15551234567"

def test_login_request_invalid_phone():
    with pytest.raises(ValidationError):
        LoginRequest(phone_number="123", password="password123")

def test_login_request_missing_contact():
    with pytest.raises(ValidationError):
        LoginRequest(password="password123")

def test_register_request_valid_email():
    req = RegisterRequest(email="test@test.com", password="password123")
    assert req.email == "test@test.com"

def test_register_request_valid_phone():
    req = RegisterRequest(phone_number="+15551234567", password="password123")
    assert req.phone_number == "+15551234567"

def test_register_request_invalid_phone():
    with pytest.raises(ValidationError):
        RegisterRequest(phone_number="123", password="password123")

def test_register_request_missing_contact():
    with pytest.raises(ValidationError):
        RegisterRequest(password="password123")
