import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.infrastructure.external.openai_client import OpenAIClient
from app.config import settings

@pytest.fixture
def mock_sys_repo():
    repo = AsyncMock()
    mock_settings = MagicMock()
    mock_settings.openai_api_key = "test-db-key"
    repo.get_settings.return_value = mock_settings
    return repo

@pytest.mark.asyncio
async def test_ensure_client_updates_key(mock_sys_repo):
    client = OpenAIClient(system_settings_repository=mock_sys_repo)
    client.current_api_key = "old-key"
    
    await client._ensure_client()
    
    assert client.current_api_key == "test-db-key"

@pytest.mark.asyncio
async def test_generate_response_success():
    client = OpenAIClient()
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response text"
    
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        resp = await client.generate_response([{"role": "user", "content": "hi"}])
        
        assert resp == "Response text"
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_response_error():
    client = OpenAIClient()
    
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("API error")
        
        resp = await client.generate_response([{"role": "user", "content": "hi"}])
        
        assert "unable to connect" in resp

@pytest.mark.asyncio
async def test_stream_response_success():
    client = OpenAIClient()
    
    mock_stream = AsyncMock()
    
    # Create chunks
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta.content = "Part 1 "
    
    chunk2 = MagicMock()
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta.content = "Part 2"
    
    async def stream_generator():
        yield chunk1
        yield chunk2
        
    mock_stream.__aiter__.side_effect = lambda: stream_generator()
    
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = stream_generator()
        
        chunks = []
        async for c in client.stream_response([{"role": "user", "content": "hi"}]):
            chunks.append(c)
            
        assert chunks == ["Part 1 ", "Part 2"]

@pytest.mark.asyncio
async def test_stream_response_error():
    client = OpenAIClient()
    
    with patch.object(client.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("Stream error")
        
        chunks = []
        async for c in client.stream_response([{"role": "user", "content": "hi"}]):
            chunks.append(c)
            
        assert "Connection Interrupted" in chunks[0]
