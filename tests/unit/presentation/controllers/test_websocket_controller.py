import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect

from app.main import app
from app.infrastructure.db.base import get_db

@pytest.fixture
def override_db():
    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield mock_db
    app.dependency_overrides.clear()

@pytest.fixture
def client(override_db):
    return TestClient(app)

def test_websocket_dummy():
    assert True
