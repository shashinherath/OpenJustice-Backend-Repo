import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.application.services.admin_cost_analytics_service import AdminCostAnalyticsService

class MockResult:
    def __init__(self, scalar_val=None, fetchall_val=None):
        self.scalar_val = scalar_val
        self.fetchall_val = fetchall_val or []

    def scalar(self):
        return self.scalar_val

    def fetchall(self):
        return self.fetchall_val


@pytest.fixture
def mock_chat_repo():
    repo = AsyncMock()
    session = AsyncMock()
    repo.db = session
    return repo


@pytest.fixture
def mock_llm_log_repo():
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_cost_analytics_no_session():
    repo = MagicMock()
    repo.db = None
    service = AdminCostAnalyticsService(repo, AsyncMock())
    result = await service.get_cost_analytics()
    assert result.cost_drivers == []


@pytest.mark.asyncio
async def test_get_cost_analytics_success(mock_chat_repo, mock_llm_log_repo):
    session = mock_chat_repo.db
    
    call_count = 0
    def mock_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        # 1. llm_query
        if call_count == 1:
            row1 = MagicMock(model_name="gpt-4o", prompt=1000, completion=2000, total=3000, recent_usage=1500, previous_usage=1500)
            row2 = MagicMock(model_name="text-embedding-3-small", prompt=0, completion=0, total=5000, recent_usage=5000, previous_usage=0)
            return MockResult(fetchall_val=[row1, row2])
        # 2. audio_query
        elif call_count == 2:
            row1 = MagicMock(audio_type="stt", duration=120, chars=0, recent_dur=60, prev_dur=60)
            row2 = MagicMock(audio_type="tts", duration=60, chars=500, recent_dur=60, prev_dur=0)
            return MockResult(fetchall_val=[row1, row2])
        # 3. wa_inbound
        elif call_count == 3:
            return MockResult(scalar_val=10)
        # 4. wa_outbound
        elif call_count == 4:
            return MockResult(scalar_val=20)
        # 5. daily_llm
        elif call_count == 5:
            row = MagicMock(date=datetime.now(timezone.utc).date(), model_name="gpt-4o", prompt=500, completion=1000, total=1500)
            return MockResult(fetchall_val=[row])
        # 6. daily_audio
        elif call_count == 6:
            row = MagicMock(date=datetime.now(timezone.utc).date(), audio_type="stt", duration=60, chars=0)
            return MockResult(fetchall_val=[row])
        # 7. daily_wa
        elif call_count == 7:
            row = MagicMock(date=datetime.now(timezone.utc).date(), sender="user", count=5)
            return MockResult(fetchall_val=[row])
        
        return MockResult()
        
    session.execute.side_effect = mock_execute
    
    service = AdminCostAnalyticsService(mock_chat_repo, mock_llm_log_repo)
    result = await service.get_cost_analytics()
    
    assert result is not None
    assert len(result.cost_drivers) > 0
    assert len(result.twilio_items) > 0
    assert len(result.daily_costs) == 7
