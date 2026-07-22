import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.pg_system_error_repository import PgSystemErrorRepository
from app.infrastructure.models.system_error import SystemError

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def repository(mock_db):
    return PgSystemErrorRepository(mock_db)

@pytest.mark.asyncio
async def test_log_error(repository, mock_db):
    def mock_add(obj):
        obj.id = uuid4()
    mock_db.add.side_effect = mock_add
    
    error_id = await repository.log_error(
        error_type="api",
        message="test error",
        details="stack trace"
    )
    
    assert error_id is not None
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_get_errors(repository, mock_db):
    mock_db.scalar.return_value = 50
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [SystemError(id=uuid4()), SystemError(id=uuid4())]
    mock_db.execute.return_value = mock_result
    
    total, errors = await repository.get_errors()
    
    assert total == 50
    assert len(errors) == 2
    mock_db.scalar.assert_called_once()
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_stats(repository, mock_db):
    mock_result = MagicMock()
    mock_result.__iter__.return_value = [
        ("api", 10),
        ("db", 5),
        ("custom", 2)
    ]
    mock_db.execute.return_value = mock_result
    
    stats = await repository.get_stats()
    
    assert stats["total"] == 17
    assert stats["api"] == 10
    assert stats["db"] == 5
    assert stats["custom"] == 2
    mock_db.execute.assert_called_once()
