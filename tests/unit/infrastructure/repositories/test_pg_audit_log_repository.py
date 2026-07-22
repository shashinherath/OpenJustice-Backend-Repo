import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.infrastructure.repositories.pg_audit_log_repository import PgAuditLogRepository
from app.infrastructure.models.audit_log import AuditLog

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_log_action(mock_session):
    repo = PgAuditLogRepository(mock_session)
    user_id = uuid4()
    
    await repo.log_action(user_id, "LOGIN", "User", 1, {"ip": "127.0.0.1"})
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_recent_activities(mock_session):
    repo = PgAuditLogRepository(mock_session)
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [AuditLog(id=uuid4())]
    mock_session.execute.return_value = mock_result
    
    activities = await repo.get_recent_activities(limit=5)
    assert len(activities) == 1
