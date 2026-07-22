import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.infrastructure.repositories.pg_user_session_repository import PgUserSessionRepository

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_create_session(mock_session):
    repo = PgUserSessionRepository(mock_session)
    user_id = uuid4()
    session_token = uuid4()
    
    res = await repo.create_session(user_id, session_token, "web", "127.0.0.1", "Mozilla")
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_invalidate_session(mock_session):
    repo = PgUserSessionRepository(mock_session)
    session_token = uuid4()
    
    await repo.invalidate_session(session_token)
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
