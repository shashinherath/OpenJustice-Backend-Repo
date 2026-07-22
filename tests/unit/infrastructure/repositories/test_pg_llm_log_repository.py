import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.infrastructure.repositories.pg_llm_log_repository import PgLLMLogRepository
from app.infrastructure.models.llm_request import LLMRequest
from app.infrastructure.models.llm_response import LLMResponse

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def repository(mock_db):
    return PgLLMLogRepository(mock_db)

@pytest.mark.asyncio
async def test_log_request(repository, mock_db):
    user_id = uuid4()
    
    def mock_add(obj):
        obj.id = uuid4()
    mock_db.add.side_effect = mock_add
    
    req_id = await repository.log_request(
        user_id=user_id,
        model_name="gpt-4",
        query="test query",
        context="test context",
        prompt_version="1.0",
        temperature=0.7,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        latency_ms=100,
        status="success",
        error_message=None
    )
    
    assert req_id is not None
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()

@pytest.mark.asyncio
async def test_log_response(repository, mock_db):
    req_id = uuid4()
    
    await repository.log_response(
        llm_request_id=req_id,
        response_text="test response",
        confidence_level="high"
    )
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_error_count(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 5
    mock_db.execute.return_value = mock_result
    
    count = await repository.get_error_count()
    
    assert count == 5
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_logs(repository, mock_db):
    # Setup for multiple execute calls (one for count, one for logs)
    count_result = MagicMock()
    count_result.scalar_one_or_none.return_value = 10
    
    logs_result = MagicMock()
    logs_result.scalars.return_value.all.return_value = [LLMRequest(id=uuid4()), LLMRequest(id=uuid4())]
    
    mock_db.execute.side_effect = [count_result, logs_result]
    
    total, logs = await repository.get_logs()
    
    assert total == 10
    assert len(logs) == 2
    assert mock_db.execute.call_count == 2

@pytest.mark.asyncio
async def test_get_stats(repository, mock_db):
    mock_result = MagicMock()
    # status, count, prompt_tokens, completion_tokens, avg_latency
    mock_result.__iter__.return_value = [
        ("success", 10, 100, 200, 50.0),
        ("error", 2, 20, 0, 10.0),
        ("pending", 1, 10, 10, 5.0),
        ("reviewed", 3, 30, 60, 20.0)
    ]
    mock_db.execute.return_value = mock_result
    
    stats = await repository.get_stats()
    
    assert stats["completed"] == 10
    assert stats["failed"] == 2
    assert stats["pending"] == 1
    assert stats["reviewed"] == 3
    assert stats["total_tokens"] == 160 + 270 # 300+20+20+90 = 430
    assert stats["latency_count"] == 16
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_update_log_status(repository, mock_db):
    log_id = uuid4()
    mock_log = LLMRequest(id=log_id, status="pending")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_log
    mock_db.execute.return_value = mock_result
    
    result = await repository.update_log_status(log_id, "success")
    
    assert result is True
    assert mock_log.status == "success"
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_log_status_not_found(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    result = await repository.update_log_status(uuid4(), "success")
    
    assert result is False

@pytest.mark.asyncio
async def test_delete_log(repository, mock_db):
    log_id = uuid4()
    mock_log = LLMRequest(id=log_id)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_log
    mock_db.execute.return_value = mock_result
    
    result = await repository.delete_log(log_id)
    
    assert result is True
    mock_db.delete.assert_called_once_with(mock_log)
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_log_not_found(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    result = await repository.delete_log(uuid4())
    
    assert result is False

@pytest.mark.asyncio
async def test_get_responses_today_count(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 25
    mock_db.execute.return_value = mock_result
    
    count = await repository.get_responses_today_count()
    
    assert count == 25
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_avg_response_time(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 150.5
    mock_db.execute.return_value = mock_result
    
    avg_time = await repository.get_avg_response_time()
    
    assert avg_time == 150.5
    mock_db.execute.assert_called_once()
