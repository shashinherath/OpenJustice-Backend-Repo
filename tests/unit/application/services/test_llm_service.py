import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import time

from app.application.services.llm_service import LLMService
from app.infrastructure.models.system_settings import SystemSettings
from app.application.dtos.chat_dto import MessageCreateDto

@pytest.fixture
def mock_chat_service():
    return AsyncMock()

@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    # For streaming
    async def mock_stream(*args, **kwargs):
        yield "Hello"
        yield " World"
    client.stream_response = mock_stream
    return client

@pytest.fixture
def mock_semantic_cache():
    return AsyncMock()

@pytest.fixture
def mock_llm_log_repo():
    return AsyncMock()

@pytest.fixture
def mock_sys_settings_repo():
    repo = AsyncMock()
    repo.get_settings.return_value = SystemSettings(
        prompt_validation_enabled=True,
        enabled_languages=["en"],
        default_language="en",
        ai_model_name="gpt-4o",
        ai_temperature=0.7,
        ai_max_tokens=1000,
        ai_top_p=1.0,
        ai_frequency_penalty=0.0
    )
    return repo


@pytest.fixture
def llm_service(mock_chat_service, mock_llm_client, mock_semantic_cache, mock_llm_log_repo, mock_sys_settings_repo):
    with patch("app.application.services.llm_service.OpenAIEmbeddings") as mock_embeddings:
        mock_emb_instance = AsyncMock()
        mock_embeddings.return_value = mock_emb_instance
        service = LLMService(
            chat_service=mock_chat_service,
            llm_client=mock_llm_client,
            semantic_cache=mock_semantic_cache,
            llm_log_repository=mock_llm_log_repo,
            system_settings_repository=mock_sys_settings_repo
        )
        service.embeddings = mock_emb_instance
        yield service


def test_count_tokens(llm_service):
    """Test token counting."""
    assert llm_service._count_tokens("Hello world") > 0


@pytest.mark.asyncio
async def test_build_messages(llm_service, mock_chat_service):
    """Test message building with context and history."""
    conv_id = uuid4()
    user_id = uuid4()
    
    mock_msg = MagicMock()
    mock_msg.created_at = time.time()
    mock_msg.sender = "user"
    mock_msg.content = "previous message"
    
    mock_chat_service.get_messages.return_value = [mock_msg]
    
    messages = await llm_service._build_messages(
        conversation_id=conv_id,
        user_id=user_id,
        query="new query",
        context="some context"
    )
    
    assert len(messages) > 0
    assert messages[0]["role"] == "system"
    assert "some context" in messages[0]["content"]


@pytest.mark.asyncio
async def test_generate_response_cache_hit(llm_service, mock_semantic_cache, mock_chat_service):
    """Test generate_response when cache hits."""
    conv_id = uuid4()
    user_id = uuid4()
    
    llm_service.embeddings.aembed_query.return_value = [0.1, 0.2, 0.3]
    mock_semantic_cache.get_similar_response.return_value = "Cached Answer"
    
    response = await llm_service.generate_response(
        conversation_id=conv_id,
        user_id=user_id,
        query="test query",
        context="test context"
    )
    
    assert response == "Cached Answer"
    mock_semantic_cache.get_similar_response.assert_called_once()


@pytest.mark.asyncio
async def test_generate_response_cache_miss(llm_service, mock_semantic_cache, mock_llm_client):
    """Test generate_response when cache misses."""
    conv_id = uuid4()
    user_id = uuid4()
    
    llm_service.embeddings.aembed_query.return_value = [0.1, 0.2, 0.3]
    mock_semantic_cache.get_similar_response.return_value = None
    mock_llm_client.generate_response.return_value = "LLM Answer"
    
    response = await llm_service.generate_response(
        conversation_id=conv_id,
        user_id=user_id,
        query="test query",
        context="test context"
    )
    
    assert response == "LLM Answer"
    mock_llm_client.generate_response.assert_called_once()
    mock_semantic_cache.set_response.assert_called_once()


@pytest.mark.asyncio
async def test_stream_response_cache_hit(llm_service, mock_semantic_cache):
    """Test stream_response when cache hits."""
    conv_id = uuid4()
    user_id = uuid4()
    
    llm_service.embeddings.aembed_query.return_value = [0.1, 0.2, 0.3]
    mock_semantic_cache.get_similar_response.return_value = "Cached Stream"
    
    chunks = []
    async for chunk in llm_service.stream_response(
        conversation_id=conv_id,
        user_id=user_id,
        query="test query",
        context="test context"
    ):
        chunks.append(chunk)
        
    assert "".join(chunks) == "Cached Stream"


@pytest.mark.asyncio
async def test_stream_response_cache_miss(llm_service, mock_semantic_cache, mock_llm_client):
    """Test stream_response when cache misses."""
    conv_id = uuid4()
    user_id = uuid4()
    
    llm_service.embeddings.aembed_query.return_value = [0.1, 0.2, 0.3]
    mock_semantic_cache.get_similar_response.return_value = None
    
    chunks = []
    async for chunk in llm_service.stream_response(
        conversation_id=conv_id,
        user_id=user_id,
        query="test query",
        context="test context"
    ):
        chunks.append(chunk)
        
    assert "".join(chunks) == "Hello World"
