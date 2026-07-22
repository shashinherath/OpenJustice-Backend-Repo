import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.infrastructure.repositories.pg_audio_log_repository import PgAudioLogRepository
from app.infrastructure.models.audio_request import AudioRequest

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_audio_log_request(mock_session):
    repo = PgAudioLogRepository(mock_session)
    user_id = uuid4()
    
    # We mock the session.add and flush
    res = await repo.log_audio_request(user_id, "speech", "en", 1.5, "openai")
    
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_audio_get_logs(mock_session):
    repo = PgAudioLogRepository(mock_session)
    
    mock_count_result = MagicMock()
    mock_count_result.scalar_one_or_none.return_value = 5
    
    mock_logs_result = MagicMock()
    mock_logs_result.scalars().all.return_value = [AudioRequest(id=uuid4())]
    
    mock_session.execute.side_effect = [mock_count_result, mock_logs_result]
    
    total, logs = await repo.get_logs()
    
    assert total == 5
    assert len(logs) == 1

@pytest.mark.asyncio
async def test_audio_get_stats(mock_session):
    repo = PgAudioLogRepository(mock_session)
    
    mock_stats_result = MagicMock()
    mock_stats_result.first.return_value = (10, 2.5) # count, avg
    
    mock_session.execute.return_value = mock_stats_result
    
    stats = await repo.get_stats()
    
    assert stats["completed"] == 10
    assert stats["avg_latency"] == 2500.0
