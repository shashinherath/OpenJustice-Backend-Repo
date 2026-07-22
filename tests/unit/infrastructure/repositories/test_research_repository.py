import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.infrastructure.repositories.research_repository import ResearchRepository
from app.infrastructure.models.research import ResearchMetric, EvaluationDataset, ExperimentNote, EvaluationDatasetItem

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_get_metrics(mock_session):
    repo = ResearchRepository(mock_session)
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [ResearchMetric(id=str(uuid4()))]
    mock_session.execute.return_value = mock_result
    
    res = await repo.get_metrics()
    assert len(res) == 1

@pytest.mark.asyncio
async def test_get_datasets(mock_session):
    repo = ResearchRepository(mock_session)
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [EvaluationDataset(id=str(uuid4()))]
    mock_session.execute.return_value = mock_result
    
    res = await repo.get_datasets()
    assert len(res) == 1

@pytest.mark.asyncio
async def test_get_notes(mock_session):
    repo = ResearchRepository(mock_session)
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [ExperimentNote(id=str(uuid4()))]
    mock_session.execute.return_value = mock_result
    
    res = await repo.get_notes()
    assert len(res) == 1

@pytest.mark.asyncio
async def test_add_metric(mock_session):
    repo = ResearchRepository(mock_session)
    metric = ResearchMetric(id=str(uuid4()))
    
    res = await repo.add_metric(metric)
    assert res == metric
    mock_session.add.assert_called_once_with(metric)

@pytest.mark.asyncio
async def test_create_evaluation_dataset(mock_session):
    repo = ResearchRepository(mock_session)
    dataset = EvaluationDataset(id=str(uuid4()))
    
    res = await repo.create_evaluation_dataset(dataset)
    assert res == dataset
    mock_session.add.assert_called_once_with(dataset)
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_get_dataset_by_id(mock_session):
    repo = ResearchRepository(mock_session)
    dataset = EvaluationDataset(id=str(uuid4()))
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = dataset
    mock_session.execute.return_value = mock_result
    
    res = await repo.get_dataset_by_id(dataset.id)
    assert res == dataset

@pytest.mark.asyncio
async def test_create_dataset_items(mock_session):
    repo = ResearchRepository(mock_session)
    items = [EvaluationDatasetItem(id=str(uuid4()))]
    
    await repo.create_dataset_items(items)
    mock_session.add_all.assert_called_once_with(items)
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_get_dataset_items(mock_session):
    repo = ResearchRepository(mock_session)
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [EvaluationDatasetItem(id=str(uuid4()))]
    mock_session.execute.return_value = mock_result
    
    res = await repo.get_dataset_items("some-id")
    assert len(res) == 1

@pytest.mark.asyncio
async def test_update_dataset_status(mock_session):
    repo = ResearchRepository(mock_session)
    await repo.update_dataset_status("some-id", "completed", "2026-07-22")
    mock_session.execute.assert_called_once()
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_delete_evaluation_dataset(mock_session):
    repo = ResearchRepository(mock_session)
    
    mock_result1 = MagicMock()
    mock_result2 = MagicMock()
    mock_result2.rowcount = 1
    mock_session.execute.side_effect = [mock_result1, mock_result2]
    
    res = await repo.delete_evaluation_dataset("some-id")
    assert res is True
    assert mock_session.execute.call_count == 2
    mock_session.flush.assert_called_once()
