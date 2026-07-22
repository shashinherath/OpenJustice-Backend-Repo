import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.application.services.whatsapp_service import WhatsAppService
from app.infrastructure.models.user import User
from app.infrastructure.models.conversation import Conversation
from app.infrastructure.models.document_chunk import DocumentChunk
from app.infrastructure.models.system_settings import SystemSettings

class MockResult:
    def __init__(self, val):
        self.val = val

    def scalars(self):
        m = MagicMock()
        m.first.return_value = self.val
        return m

@pytest.fixture
def mock_whatsapp_client():
    return AsyncMock()

@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    service.generate_response.return_value = "Mock LLM Reply"
    return service

@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db

@pytest.fixture
def mock_system_settings_repo():
    repo = AsyncMock()
    repo.get_settings.return_value = SystemSettings(
        twilio_account_sid="test_sid",
        twilio_auth_token="test_token"
    )
    return repo

@pytest.fixture
def whatsapp_service(mock_whatsapp_client, mock_llm_service, mock_db, mock_system_settings_repo):
    with patch("app.application.services.whatsapp_service.RetrievalService") as mock_rs:
        mock_rs_instance = AsyncMock()
        mock_rs_instance.retrieve.return_value = ([DocumentChunk(content="chunk")], 0.9)
        mock_rs.return_value = mock_rs_instance
        service = WhatsAppService(
            whatsapp_client=mock_whatsapp_client,
            llm_service=mock_llm_service,
            db=mock_db,
            system_settings_repository=mock_system_settings_repo
        )
        service.retrieval_service = mock_rs_instance
        yield service

@pytest.mark.asyncio
async def test_handle_incoming_message_empty(whatsapp_service):
    """Test empty message drops out early."""
    await whatsapp_service.handle_incoming_message(from_number="123")
    whatsapp_service.db.execute.assert_not_called()

@pytest.mark.asyncio
async def test_handle_incoming_message_text(whatsapp_service, mock_db, mock_whatsapp_client):
    """Test standard text message."""
    
    call_count = 0
    def db_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # User lookup
            user = User(id=uuid4(), phone_number="123")
            return MockResult(user)
        elif call_count == 2:
            # Conversation lookup
            conv = Conversation(id=uuid4())
            return MockResult(conv)
        return MockResult(None)
        
    mock_db.execute.side_effect = db_execute
    
    await whatsapp_service.handle_incoming_message(from_number="whatsapp:123", body="Hello")
    
    mock_whatsapp_client.send_message.assert_called_once_with(to="whatsapp:123", body="Mock LLM Reply")

@pytest.mark.asyncio
@patch("app.application.services.whatsapp_service.TempFileManager")
@patch("app.application.services.whatsapp_service.SpeechToTextService")
@patch("app.application.services.whatsapp_service.TextToSpeechService")
async def test_handle_incoming_message_audio(
    mock_tts_cls, mock_stt_cls, mock_temp_file, whatsapp_service, mock_db, mock_whatsapp_client
):
    """Test voice note flow."""
    mock_temp_file.download_twilio_audio = AsyncMock(return_value="/tmp/audio.ogg")
    
    mock_stt = AsyncMock()
    mock_stt.transcribe_audio.return_value = "transcribed text"
    mock_stt_cls.return_value = mock_stt
    
    mock_tts = AsyncMock()
    mock_tts.synthesize_speech.return_value = "/tmp/reply.ogg"
    mock_tts_cls.return_value = mock_tts
    
    call_count = 0
    def db_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MockResult(None) # user miss
        elif call_count == 2:
            return MockResult(None) # conv miss
        return MockResult(None)
        
    mock_db.execute.side_effect = db_execute
    
    await whatsapp_service.handle_incoming_message(from_number="whatsapp:123", media_url="http://audio")
    
    # Assert client sent media message
    mock_whatsapp_client.send_message.assert_called_once()
    args, kwargs = mock_whatsapp_client.send_message.call_args
    assert "media_url" in kwargs
    assert "/temp/reply.ogg" in kwargs["media_url"]
