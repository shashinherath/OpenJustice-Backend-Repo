import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
import uuid

from app.application.services.admin_retrieval_service import AdminRetrievalService
from app.infrastructure.models.system_settings import SystemSettings
from app.infrastructure.models.retrieval_log import RetrievalLog
from app.infrastructure.models.retrieved_document import RetrievedDocument
from app.infrastructure.models.llm_request import LLMRequest
from app.infrastructure.models.llm_response import LLMResponse
from app.infrastructure.models.document_chunk import DocumentChunk


class MockResult:
    def __init__(self, scalar_val=None, scalars_list=None, all_val=None, fetchall_val=None):
        self.scalar_val = scalar_val
        self.scalars_list = scalars_list or []
        self.all_val = all_val or []
        self.fetchall_val = fetchall_val or []

    def scalar_one_or_none(self):
        return self.scalar_val

    def scalars(self):
        m = MagicMock()
        m.all.return_value = self.scalars_list
        return m

    def all(self):
        return self.all_val

    def fetchall(self):
        return self.fetchall_val


@pytest.fixture
def mock_document_repo():
    repo = AsyncMock()
    session = AsyncMock()
    repo.db = session
    return repo


@pytest.fixture
def mock_system_settings_repo():
    repo = AsyncMock()
    repo.get_settings.return_value = SystemSettings(retrieval_similarity_threshold=0.7)
    return repo


@pytest.mark.asyncio
async def test_get_retrieval_monitoring_no_session():
    """Test when db session is not available."""
    repo = MagicMock()
    repo.db = None
    repo.session = None
    service = AdminRetrievalService(document_repo=repo)
    result = await service.get_retrieval_monitoring()
    assert result.metrics == []


@pytest.mark.asyncio
async def test_get_retrieval_monitoring_success(mock_document_repo, mock_system_settings_repo):
    """Test full execution of get_retrieval_monitoring with mock data."""
    
    session = mock_document_repo.db
    
    # We will use a side_effect for session.execute to return different MockResults based on call count or just a generic one
    
    call_count = 0
    def mock_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        # 1. Avg Similarity
        if call_count == 1:
            return MockResult(scalar_val=0.85)
        # 2. Avg Latency
        elif call_count == 2:
            return MockResult(scalar_val=150.0)
        # 3. P95 Latency
        elif call_count == 3:
            return MockResult(scalar_val=200.0)
        # 4. Hit Rate Metrics (logs)
        elif call_count == 4:
            log = RetrievalLog(id=uuid.uuid4(), created_at=datetime.now(timezone.utc), query="test query", top_k=5, retrieval_latency_ms=100)
            return MockResult(scalars_list=[log])
        # 5. Inside loop: docs for log
        elif call_count == 5:
            doc = RetrievedDocument(id=uuid.uuid4(), similarity_score=0.9, retrieval_log_id=uuid.uuid4())
            return MockResult(scalars_list=[doc])
        # 6. Any hits
        elif call_count == 6:
            return MockResult(scalar_val=1)
        # 7. Recent retrieval logs (for citation heuristic)
        elif call_count == 7:
            r_log = RetrievalLog(id=uuid.uuid4(), created_at=datetime.now(timezone.utc), query="test query")
            return MockResult(scalars_list=[r_log])
        # 8. LLMRequest match
        elif call_count == 8:
            req = LLMRequest(id=uuid.uuid4(), query="test query", created_at=datetime.now(timezone.utc))
            return MockResult(scalar_val=req)
        # 9. LLMResponse match
        elif call_count == 9:
            resp = LLMResponse(id=uuid.uuid4(), response_text="This is a significant response with overlap test word")
            return MockResult(scalar_val=resp)
        # 10. Document chunks match
        elif call_count == 10:
            chunk = DocumentChunk(id=uuid.uuid4(), content="This is a significant response with overlap test word")
            return MockResult(scalars_list=[chunk])
        # 11. Trend query
        elif call_count == 11:
            row = MagicMock()
            row.date = datetime.now(timezone.utc).date()
            row.avg_sim = 0.8
            return MockResult(fetchall_val=[row])
        # 12. Recent Checks
        elif call_count == 12:
            row = MagicMock()
            row.RetrievalLog = RetrievalLog(id=uuid.uuid4(), query="recent test", top_k=3, retrieval_latency_ms=50, created_at=datetime.now(timezone.utc))
            row.avg_sim = 0.9
            row.doc_count = 2
            return MockResult(all_val=[row])
        # 13. Per-query LLM match
        elif call_count == 13:
            req = LLMRequest(id=uuid.uuid4(), query="recent test", created_at=datetime.now(timezone.utc))
            return MockResult(scalar_val=req)
        # 14. Per-query LLMResponse match
        elif call_count == 14:
            resp = LLMResponse(id=uuid.uuid4(), response_text="Significant overlap words")
            return MockResult(scalar_val=resp)
        # 15. Per-query chunks
        elif call_count == 15:
            chunk = DocumentChunk(id=uuid.uuid4(), content="Significant overlap words")
            return MockResult(scalars_list=[chunk])
        
        return MockResult()

    session.execute.side_effect = mock_execute
    
    service = AdminRetrievalService(mock_document_repo, mock_system_settings_repo)
    result = await service.get_retrieval_monitoring()
    
    assert result is not None
    assert len(result.metrics) > 0
    assert result.metrics[0].value == "0.85"
