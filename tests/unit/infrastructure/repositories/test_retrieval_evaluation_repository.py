import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.infrastructure.repositories.retrieval_evaluation_repository import RetrievalEvaluationRepository
from app.infrastructure.models.retrieval_evaluation import RetrievalEvaluation

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_get_latest_evaluation(mock_session):
    repo = RetrievalEvaluationRepository(mock_session)
    mock_result = MagicMock()
    eval_model = RetrievalEvaluation(id=str(uuid4()))
    mock_result.scalar_one_or_none.return_value = eval_model
    mock_session.execute.return_value = mock_result
    
    res = await repo.get_latest_evaluation()
    assert res == eval_model

@pytest.mark.asyncio
async def test_get_similarity_distribution(mock_session):
    repo = RetrievalEvaluationRepository(mock_session)
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [
        ("0.8-1.0", 15),
        ("0.6-0.8", 5)
    ]
    mock_session.execute.return_value = mock_result
    
    dist = await repo.get_similarity_distribution()
    assert len(dist) == 5
    
    # Check that bins are populated
    for item in dist:
        if item["bin_label"] == "0.8-1.0":
            assert item["count"] == 15
        elif item["bin_label"] == "0.6-0.8":
            assert item["count"] == 5
        else:
            assert item["count"] == 0
