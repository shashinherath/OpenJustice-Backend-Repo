import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.infrastructure.db.base import get_db
from app.presentation.controllers.document_controller import get_document_service, get_rag_service

mock_db = AsyncMock()
mock_doc_service = AsyncMock()
mock_rag_service = AsyncMock()

@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_document_service] = lambda: mock_doc_service
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    yield
    app.dependency_overrides.clear()

client = TestClient(app)
test_user_id = uuid4()
headers = {"Authorization": "Bearer fake_token"}

@pytest.fixture(autouse=True)
def auth_mock():
    with patch("app.presentation.middleware.auth_middleware.jwt_handler.verify_token") as mock_verify:
        mock_verify.return_value = {"sub": str(test_user_id)}
        yield mock_verify

def _mock_doc():
    doc = MagicMock()
    doc.id = uuid4()
    doc.title = "Test Doc"
    doc.document_type = "pdf"
    doc.language = "English"
    doc.source_url = None
    doc.storage_path = "/tmp/test.pdf"
    doc.status = "processed"
    doc.published_year = 2023
    doc.collection_id = "col1"
    doc.created_at = datetime.now(timezone.utc)
    return doc

def _mock_chunk():
    chunk = MagicMock()
    chunk.id = uuid4()
    chunk.document_id = uuid4()
    chunk.content = "Test content"
    chunk.language = "en"
    chunk.chunk_index = 0
    chunk.chunk_total = 1
    chunk.chunk_size = 12
    chunk.embedding_model = "test-model"
    chunk.metadata_ = {}
    return chunk

def test_process_document():
    doc_id = uuid4()
    mock_doc_service.get_document.return_value = _mock_doc()
    
    response = client.post(f"/api/documents/{doc_id}/process", headers=headers)
    assert response.status_code == 202

def test_upload_document():
    mock_doc_service.ingest_document.return_value = _mock_doc()
    
    response = client.post(
        "/api/documents",
        files={"file": ("test.pdf", b"data", "application/pdf")},
        data={"title": "Test Doc"},
        headers=headers
    )
    assert response.status_code == 201

def test_initialize_chunked_upload():
    response = client.post("/api/documents/chunked/initialize", headers=headers)
    assert response.status_code == 201

def test_upload_chunk(tmp_path):
    uid = "test1234"
    # Create the temp dir so it exists
    temp_dir = tmp_path / "uploads" / f"temp_{uid}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    with patch("app.presentation.controllers.document_controller.Path") as mock_path:
        mock_path.return_value = tmp_path / "uploads"
        
        response = client.post(
            "/api/documents/chunked/upload",
            data={"upload_id": uid, "chunk_index": 0},
            files={"file": ("chunk", b"data", "application/octet-stream")},
            headers=headers
        )
        assert response.status_code == 200

def test_complete_chunked_upload(tmp_path):
    uid = "test1234"
    temp_dir = tmp_path / "uploads" / f"temp_{uid}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    chunk_file = temp_dir / "chunk_0"
    chunk_file.write_text("data")
    
    mock_doc_service.ingest_document_from_bytes.return_value = _mock_doc()
    
    with patch("app.presentation.controllers.document_controller.Path") as mock_path:
        mock_path.return_value = tmp_path / "uploads"
        
        response = client.post(
            "/api/documents/chunked/complete",
            data={"upload_id": uid, "filename": "test.pdf", "total_chunks": 1},
            headers=headers
        )
        assert response.status_code == 201

def test_list_documents():
    mock_doc_service.list_documents.return_value = [_mock_doc()]
    response = client.get("/api/documents", headers=headers)
    assert response.status_code == 200

def test_get_document_stats():
    mock_doc_service.get_document_stats.return_value = {"processed": 10}
    response = client.get("/api/documents/stats", headers=headers)
    assert response.status_code == 200

def test_get_document():
    doc_id = uuid4()
    mock_doc_service.get_document.return_value = _mock_doc()
    response = client.get(f"/api/documents/{doc_id}", headers=headers)
    assert response.status_code == 200

def test_get_document_access(tmp_path):
    doc_id = uuid4()
    doc = _mock_doc()
    
    # Create a real temp file so FileResponse's os.stat doesn't fail
    temp_file = tmp_path / "test.pdf"
    temp_file.write_text("dummy")
    doc.storage_path = str(temp_file)
    
    mock_doc_service.get_document.return_value = doc
    
    response = client.get(f"/api/documents/{doc_id}/access", headers=headers)
    assert response.status_code in [200, 302]

def test_get_document_chunks():
    doc_id = uuid4()
    mock_doc_service.get_document_chunks.return_value = [_mock_chunk()]
    response = client.get(f"/api/documents/{doc_id}/chunks", headers=headers)
    assert response.status_code == 200

def test_delete_document():
    doc_id = uuid4()
    mock_doc_service.delete_document.return_value = None
    response = client.delete(f"/api/documents/{doc_id}", headers=headers)
    assert response.status_code == 200
