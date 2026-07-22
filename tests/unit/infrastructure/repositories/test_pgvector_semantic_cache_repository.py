import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.infrastructure.repositories.pgvector_semantic_cache_repository import PgVectorSemanticCacheRepository

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_get_similar_response(mock_session):
    repo = PgVectorSemanticCacheRepository(mock_session)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "cached response"
    mock_session.execute.return_value = mock_result
    
    # We pass a fake embedding
    res = await repo.get_similar_response([0.1, 0.2, 0.3])
    
    assert res == "cached response"
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_set_response(mock_session):
    repo = PgVectorSemanticCacheRepository(mock_session)
    
    await repo.set_response("test query", [0.1, 0.2, 0.3], "test response")
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
