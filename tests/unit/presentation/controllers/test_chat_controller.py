import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.presentation.controllers.chat_controller import get_chat_service, get_current_user_id
from app.infrastructure.db.base import get_db

# Mocks
mock_chat_service = AsyncMock()
mock_db = AsyncMock()
test_user_id = uuid4()

def override_get_chat_service():
    return mock_chat_service

async def override_get_db():
    return mock_db

@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_chat_service] = override_get_chat_service
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

@pytest.fixture(autouse=True)
def auth_mock():
    with patch("app.presentation.middleware.auth_middleware.jwt_handler.verify_token") as mock_verify:
        mock_verify.return_value = {"sub": str(test_user_id)}
        with patch("app.presentation.controllers.chat_controller.get_current_user_id") as mock_get_user:
            mock_get_user.return_value = test_user_id
            yield

@pytest.fixture(autouse=True)
def reset_mocks():
    mock_chat_service.reset_mock()
    mock_db.reset_mock()

headers = {"Authorization": "Bearer test"}

def _mock_conv(cid=None):
    return MagicMock(
        id=cid or uuid4(),
        title="Test",
        channel="web",
        user_id=uuid4(),
        is_archived=False,
        is_pinned=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

def _mock_msg(mid=None, cid=None):
    return MagicMock(
        id=mid or uuid4(),
        conversation_id=cid or uuid4(),
        sender="user",
        content="Hi",
        message_type="text",
        created_at=datetime.now(timezone.utc),
        audio_url=None,
        model=None,
        tokens_used=None,
        audio_latency=None,
        stt_latency=None,
        cost=None,
        metadata_=None
    )

def test_create_conversation():
    mock_chat_service.create_conversation.return_value = _mock_conv()
    response = client.post("/api/chats", json={"title": "Test", "channel": "web"}, headers=headers)
    assert response.status_code == 201

def test_get_conversations():
    mock_chat_service.get_user_conversations.return_value = [_mock_conv()]
    response = client.get("/api/chats", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_conversation():
    cid = uuid4()
    mock_chat_service.get_conversation.return_value = _mock_conv(cid)
    mock_chat_service.get_messages.return_value = []
    
    response = client.get(f"/api/chats/{cid}", headers=headers)
    assert response.status_code == 200

def test_create_message():
    cid = uuid4()
    mock_chat_service.add_message.return_value = _mock_msg(cid=cid)
    
    response = client.post(f"/api/chats/{cid}/messages", json={
        "content": "Hi", "sender": "user", "message_type": "text"
    }, headers=headers)
    assert response.status_code == 201

def test_update_conversation():
    cid = uuid4()
    mock_chat_service.update_conversation.return_value = _mock_conv(cid)
    
    response = client.patch(f"/api/chats/{cid}", json={"title": "New"}, headers=headers)
    assert response.status_code == 200

def test_delete_conversation():
    cid = uuid4()
    mock_chat_service.delete_conversation.return_value = None
    
    response = client.delete(f"/api/chats/{cid}", headers=headers)
    assert response.status_code == 204

def test_archive_conversation():
    cid = uuid4()
    mock_chat_service.archive_conversation.return_value = _mock_conv(cid)
    
    response = client.patch(f"/api/chats/{cid}/archive", headers=headers)
    assert response.status_code == 200

def test_pin_conversation():
    cid = uuid4()
    mock_chat_service.pin_conversation.return_value = _mock_conv(cid)
    
    response = client.patch(f"/api/chats/{cid}/pin", headers=headers)
    assert response.status_code == 200

@patch("app.presentation.controllers.chat_controller.RetrievalService")
@patch("app.presentation.controllers.chat_controller.LLMService")
def test_complete_message(mock_llm_cls, mock_retrieval_cls):
    cid = uuid4()
    
    mock_retrieval = AsyncMock()
    mock_retrieval.retrieve.return_value = ([], 0.0)
    mock_retrieval_cls.return_value = mock_retrieval
    
    mock_llm = MagicMock()
    async def mock_stream(*args, **kwargs):
        yield "Streaming"
    mock_llm.stream_response = mock_stream
    mock_llm_cls.return_value = mock_llm
    
    response = client.post(f"/api/chats/{cid}/messages/complete", json={
        "query": "test query",
        "context": "test context"
    }, headers=headers)
    
    assert response.status_code == 200

@patch("app.presentation.controllers.chat_controller.TempFileManager")
@patch("app.presentation.controllers.chat_controller.SpeechToTextService")
@patch("app.presentation.controllers.chat_controller.TextToSpeechService")
@patch("app.presentation.controllers.chat_controller.RetrievalService")
@patch("app.presentation.controllers.chat_controller.LLMService")
@patch("app.presentation.controllers.chat_controller.PgAudioLogRepository")
def test_voice_message(mock_audio_repo, mock_llm_cls, mock_retrieval_cls, mock_tts_cls, mock_stt_cls, mock_tfm, tmp_path):
    cid = uuid4()
    
    mock_audio_repo_inst = MagicMock()
    mock_audio_repo_inst.log_audio_request = AsyncMock()
    mock_audio_repo.return_value = mock_audio_repo_inst
    
    mock_tfm.save_upload_file = AsyncMock(return_value="/tmp/in.ogg")
    
    # Create a real dummy file so FileResponse doesn't crash on os.stat
    dummy_ai_file = tmp_path / "ai.ogg"
    dummy_ai_file.write_text("dummy")
    
    with patch("app.presentation.controllers.chat_controller._persist_audio", AsyncMock(return_value=str(dummy_ai_file))):
        mock_stt = AsyncMock()
        mock_stt.transcribe_audio.return_value = "query"
        mock_stt_cls.return_value = mock_stt
        
        mock_retrieval = AsyncMock()
        mock_retrieval.retrieve.return_value = ([], 0.0)
        mock_retrieval_cls.return_value = mock_retrieval
        
        mock_llm = AsyncMock()
        mock_llm.generate_response.return_value = "reply"
        mock_llm_cls.return_value = mock_llm
        
        mock_tts = AsyncMock()
        mock_tts.synthesize_speech.return_value = "/tmp/out.ogg"
        mock_tts_cls.return_value = mock_tts
        
        response = client.post(
            f"/api/chats/{cid}/messages/voice",
            files={"file": ("test.ogg", b"audio data", "audio/ogg")},
            headers=headers
        )
        assert response.status_code == 200
