import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.security_event_repository import SecurityEventRepository
from app.infrastructure.models.security_event import SecurityEvent

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def repository(mock_db):
    return SecurityEventRepository(mock_db)

@pytest.mark.asyncio
async def test_get_recent_events(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [SecurityEvent(), SecurityEvent()]
    mock_db.execute.return_value = mock_result
    
    events = await repository.get_recent_events(limit=5)
    
    assert len(events) == 2
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_priority_alerts(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [SecurityEvent()]
    mock_db.execute.return_value = mock_result
    
    events = await repository.get_priority_alerts(limit=3)
    
    assert len(events) == 1
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_count_by_area(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 10
    mock_db.execute.return_value = mock_result
    
    count = await repository.get_count_by_area("Authentication", hours=24)
    
    assert count == 10
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_count_by_condition(repository, mock_db):
    from sqlalchemy import text
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 5
    mock_db.execute.return_value = mock_result
    
    condition = SecurityEvent.severity == "High"
    count = await repository.get_count_by_condition(condition, hours=12)
    
    assert count == 5
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_create(repository, mock_db):
    event = SecurityEvent(id=uuid4(), area="Test Area", source="Test Source", detail="Test Detail", severity="Medium")
    
    created = await repository.create(event)
    
    assert created == event
    mock_db.add.assert_called_once_with(event)
    mock_db.flush.assert_called_once()
    mock_db.refresh.assert_called_once_with(event)

@pytest.mark.asyncio
async def test_get_total_count(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 100
    mock_db.execute.return_value = mock_result
    
    count = await repository.get_total_count()
    
    assert count == 100
    mock_db.execute.assert_called_once()
