import pytest
from app.domain.exceptions.auth import (
    AuthenticationFailure,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    UserAlreadyExistsError,
)
from app.domain.exceptions.base import DomainError

def test_authentication_failure():
    err = AuthenticationFailure("auth failed")
    assert isinstance(err, DomainError)
    assert str(err) == "auth failed"

def test_invalid_credentials_error():
    err = InvalidCredentialsError()
    assert err.message == "Invalid credentials"
    assert str(err) == "Invalid credentials"
    
    err2 = InvalidCredentialsError("Custom error")
    assert err2.message == "Custom error"
    assert str(err2) == "Custom error"

def test_token_expired_error():
    err = TokenExpiredError()
    assert err.message == "Token has expired"
    
    err2 = TokenExpiredError("Custom token expired")
    assert err2.message == "Custom token expired"

def test_invalid_token_error():
    err = InvalidTokenError()
    assert err.message == "Could not validate credentials"
    
    err2 = InvalidTokenError("Bad token")
    assert err2.message == "Bad token"

def test_user_already_exists_error():
    err = UserAlreadyExistsError()
    assert err.message == "A user with this identifier already exists"
    
    err2 = UserAlreadyExistsError("Duplicate user")
    assert err2.message == "Duplicate user"
