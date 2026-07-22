import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.presentation.middleware.auth_middleware import AuthMiddleware
from app.config import settings

app = FastAPI()
app.add_middleware(AuthMiddleware)

@app.get("/api/protected")
def protected_route(request: Request):
    user = getattr(request.state, "user", None)
    return {"message": "success", "user": user}

@app.get("/api/auth/login")
def public_route():
    return {"message": "public"}

client = TestClient(app)

def test_auth_middleware_public_path():
    response = client.get("/api/auth/login")
    assert response.status_code == 200

def test_auth_middleware_no_token():
    response = client.get("/api/protected")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"

def test_auth_middleware_valid_bearer_token():
    with patch("app.presentation.middleware.auth_middleware.jwt_handler.verify_token") as mock_verify:
        mock_verify.return_value = {"sub": "user123"}
        response = client.get("/api/protected", headers={"Authorization": "Bearer validtoken"})
        assert response.status_code == 200
        assert response.json()["user"] == {"sub": "user123"}

def test_auth_middleware_invalid_token():
    with patch("app.presentation.middleware.auth_middleware.jwt_handler.verify_token") as mock_verify:
        mock_verify.side_effect = Exception("Expired")
        response = client.get("/api/protected", headers={"Authorization": "Bearer invalidtoken"})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_TOKEN"

def test_auth_middleware_token_in_query():
    with patch("app.presentation.middleware.auth_middleware.jwt_handler.verify_token") as mock_verify:
        mock_verify.return_value = {"sub": "user123"}
        response = client.get("/api/protected?token=querytoken")
        assert response.status_code == 200

def test_auth_middleware_options_request():
    response = client.options("/api/protected")
    assert response.status_code != 401 # Should pass middleware and hit FastAPI which might return 405 or 200

@pytest.mark.asyncio
async def test_auth_middleware_non_http_websocket():
    # Simulate a lifespan scope to cover line 35-37
    middleware = AuthMiddleware(app)
    
    called = False
    async def mock_app(scope, receive, send):
        nonlocal called
        called = True
        
    middleware.app = mock_app
    
    scope = {"type": "lifespan"}
    await middleware(scope, None, None)
    
    assert called is True
