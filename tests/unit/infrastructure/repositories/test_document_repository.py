import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.models.document import Document
from app.infrastructure.models.document_chunk import DocumentChunk

class MockResult:
    def __init__(self, val=None, all_val=None, scalar_val=None):
        self.val = val
        self.all_val = all_val or []
        self.scalar_val = scalar_val

    def scalars(self):
        m = MagicMock()
        m.first.return_value = self.val
        m.all.return_value = self.all_val
        return m

    def all(self):
        return self.all_val

    def scalar_one_or_none(self):
        return self.scalar_val

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def repo(mock_session):
    return DocumentRepository(mock_session)

@pytest.mark.asyncio
async def test_create(repo, mock_session):
    doc = Document(id=uuid4(), title="Test Doc")
    res = await repo.create(doc)
    mock_session.add.assert_called_once_with(doc)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(doc)
    assert res == doc

@pytest.mark.asyncio
async def test_get_by_id(repo, mock_session):
    doc = Document(id=uuid4(), title="Test Doc")
    mock_session.execute.return_value = MockResult(val=doc)
    res = await repo.get_by_id(doc.id)
    assert res == doc

@pytest.mark.asyncio
async def test_list_documents(repo, mock_session):
    docs = [Document(id=uuid4(), title="Test Doc")]
    mock_session.execute.return_value = MockResult(all_val=docs)
    res = await repo.list_documents(search_query="Test", language="en", status="Processed", collection_id="A", letter="T")
    assert len(res) == 1
    assert res[0].title == "Test Doc"

@pytest.mark.asyncio
async def test_get_total_count(repo, mock_session):
    mock_session.execute.return_value = MockResult(scalar_val=10)
    res = await repo.get_total_count()
    assert res == 10

@pytest.mark.asyncio
async def test_get_status_counts(repo, mock_session):
    mock_session.execute.return_value = MockResult(all_val=[("Processed", 5), ("Pending", 2)])
    res = await repo.get_status_counts()
    assert res["processed"] == 5
    assert res["total"] == 7

@pytest.mark.asyncio
async def test_get_collection_counts(repo, mock_session):
    mock_session.execute.return_value = MockResult(all_val=[("col1", 5)])
    res = await repo.get_collection_counts()
    assert res[0]["collection_id"] == "col1"
    assert res[0]["count"] == 5

@pytest.mark.asyncio
async def test_get_letter_counts(repo, mock_session):
    mock_session.execute.return_value = MockResult(all_val=[("A", 2), ("B", 3), (None, 1)])
    res = await repo.get_letter_counts("col")
    assert len(res) == 2
    assert res[0]["letter"] == "A"

@pytest.mark.asyncio
async def test_delete(repo, mock_session):
    doc = Document(id=uuid4(), title="Test Doc")
    mock_session.execute.return_value = MockResult(val=doc)
    res = await repo.delete(doc.id)
    assert res is True
    mock_session.delete.assert_called_once_with(doc)

@pytest.mark.asyncio
async def test_delete_not_found(repo, mock_session):
    mock_session.execute.return_value = MockResult(val=None)
    res = await repo.delete(uuid4())
    assert res is False

@pytest.mark.asyncio
async def test_get_total_chunks_count(repo, mock_session):
    mock_session.execute.return_value = MockResult(scalar_val=50)
    res = await repo.get_total_chunks_count()
    assert res == 50

@pytest.mark.asyncio
async def test_update_status(repo, mock_session):
    doc = Document(id=uuid4(), title="Test Doc")
    mock_session.execute.return_value = MockResult(val=doc)
    res = await repo.update_status(doc.id, "Failed")
    assert res.status == "Failed"
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_chunks_by_document_id(repo, mock_session):
    chunk = DocumentChunk(id=uuid4())
    mock_session.execute.return_value = MockResult(all_val=[chunk])
    res = await repo.get_chunks_by_document_id(uuid4())
    assert len(res) == 1

@pytest.mark.asyncio
async def test_delete_chunks_by_document_id(repo, mock_session):
    await repo.delete_chunks_by_document_id(uuid4())
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_save_chunks(repo, mock_session):
    chunks = [DocumentChunk(id=uuid4())]
    await repo.save_chunks(chunks)
    mock_session.add_all.assert_called_once_with(chunks)
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_search_similar_chunks(repo, mock_session):
    chunk = DocumentChunk(id=uuid4())
    mock_session.execute.return_value = MockResult(all_val=[(chunk, 0.2)])
    res = await repo.search_similar_chunks([0.1, 0.2])
    assert len(res) == 1
    assert res[0].similarity == 0.8

@pytest.mark.asyncio
async def test_get_knowledge_metrics(repo, mock_session):
    row1 = MagicMock(document_id=uuid4(), document_title="Test", collection_id="C1", chunk_count=10, embedding_model="M", status="Processed")
    row2 = MagicMock(document_id=uuid4(), document_title=None, collection_id=None, chunk_count=0, embedding_model=None, status="Failed")
    
    mock_session.execute.return_value = [row1, row2]
    res = await repo.get_knowledge_metrics()
    assert len(res) == 2
    assert res[0]["status"] == "Active"
    assert res[1]["status"] == "Failed"
