import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.infrastructure.repositories.ai_evaluation_repository import AIEvaluationRepository
from app.infrastructure.models.ai_evaluation import AIEvaluation

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_get_latest_global_metrics(mock_session):
    repo = AIEvaluationRepository(mock_session)
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.avg_accuracy = 0.854
    mock_row.avg_hallucination_rate = 0.023
    mock_row.global_avg_tokens = 512
    mock_result.fetchone.return_value = mock_row
    
    mock_session.execute.return_value = mock_result
    
    metrics = await repo.get_latest_global_metrics()
    assert metrics["accuracy"] == 0.85
    assert metrics["hallucination_rate"] == 0.02
    assert metrics["avg_tokens"] == 512

@pytest.mark.asyncio
async def test_get_latest_global_metrics_none(mock_session):
    repo = AIEvaluationRepository(mock_session)
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.avg_accuracy = None
    mock_result.fetchone.return_value = mock_row
    
    mock_session.execute.return_value = mock_result
    
    metrics = await repo.get_latest_global_metrics()
    assert metrics is None

@pytest.mark.asyncio
async def test_get_recent_runs(mock_session):
    repo = AIEvaluationRepository(mock_session)
    mock_result = MagicMock()
    
    run1 = AIEvaluation(id=str(uuid4()), model_name="gpt-4")
    run2 = AIEvaluation(id=str(uuid4()), model_name="gpt-4")
    run3 = AIEvaluation(id=str(uuid4()), model_name="gpt-3.5")
    
    mock_result.scalars().all.return_value = [run1, run2, run3]
    mock_session.execute.return_value = mock_result
    
    runs = await repo.get_recent_runs(limit=5)
    assert len(runs) == 2
    assert runs[0].model_name == "gpt-4"
    assert runs[1].model_name == "gpt-3.5"
