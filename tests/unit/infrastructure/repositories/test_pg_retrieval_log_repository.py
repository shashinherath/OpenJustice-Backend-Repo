import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.infrastructure.repositories.pg_retrieval_log_repository import PgRetrievalLogRepository
from app.infrastructure.models.retrieval_log import RetrievalLog

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_log_retrieval(mock_session):
    repo = PgRetrievalLogRepository(mock_session)
    
    res = await repo.log_retrieval(
        conversation_id=uuid4(),
        query="test query",
        language="en",
        top_k=5,
        retrieved_chunks=[{"chunk_id": uuid4(), "similarity_score": 0.95}],
        latency_ms=100
    )
    
    assert mock_session.add.call_count == 2 # 1 log + 1 doc
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_retrieval_logs(mock_session):
    repo = PgRetrievalLogRepository(mock_session)
    
    mock_count_result = MagicMock()
    mock_count_result.scalar_one_or_none.return_value = 10
    
    mock_logs_result = MagicMock()
    mock_logs_result.unique().scalars().all.return_value = [RetrievalLog(id=uuid4())]
    
    mock_session.execute.side_effect = [mock_count_result, mock_logs_result]
    
    total, logs = await repo.get_logs()
    
    assert total == 10
    assert len(logs) == 1

@pytest.mark.asyncio
async def test_get_retrieval_stats(mock_session):
    repo = PgRetrievalLogRepository(mock_session)
    
    mock_stats_result = MagicMock()
    mock_stats_result.first.return_value = (50, 120.5) # count, avg
    
    mock_session.execute.return_value = mock_stats_result
    
    stats = await repo.get_stats()
    
    assert stats["completed"] == 50
    assert stats["avg_latency"] == 120.5
