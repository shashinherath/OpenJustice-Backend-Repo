import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.application.services.chat_service import ChatService
from app.application.dtos.chat_dto import ConversationCreateDto, MessageCreateDto, ConversationUpdateDto
from app.application.exceptions.app_errors import AppError
from app.infrastructure.models.conversation import Conversation
from app.infrastructure.models.message import Message

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def chat_service(mock_db):
    service = ChatService(mock_db)
    service.repository = AsyncMock()
    return service

def _mock_conv(user_id=None, cid=None):
    return Conversation(
        id=cid or uuid4(),
        user_id=user_id or uuid4(),
        title="Test",
        channel="web",
        is_archived=False,
        is_pinned=False
    )

def _mock_msg():
    return Message(
        id=uuid4(),
        conversation_id=uuid4(),
        sender="user",
        content="Hi",
        message_type="text"
    )

@pytest.mark.asyncio
async def test_create_conversation(chat_service):
    user_id = uuid4()
    chat_service.repository.create_conversation.return_value = _mock_conv(user_id=user_id)
    
    dto = ConversationCreateDto(title="Test", channel="web")
    res = await chat_service.create_conversation(user_id, dto)
    
    assert res.title == "Test"
    chat_service.repository.create_conversation.assert_called_once()

@pytest.mark.asyncio
async def test_get_user_conversations(chat_service):
    user_id = uuid4()
    chat_service.repository.get_conversations_by_user.return_value = [_mock_conv(user_id=user_id)]
    
    res = await chat_service.get_user_conversations(user_id)
    assert len(res) == 1

@pytest.mark.asyncio
async def test_get_conversation_success(chat_service):
    user_id = uuid4()
    cid = uuid4()
    chat_service.repository.get_conversation.return_value = _mock_conv(user_id=user_id, cid=cid)
    
    res = await chat_service.get_conversation(cid, user_id)
    assert res.id == cid

@pytest.mark.asyncio
async def test_get_conversation_not_found(chat_service):
    chat_service.repository.get_conversation.return_value = None
    
    with pytest.raises(AppError) as exc:
        await chat_service.get_conversation(uuid4(), uuid4())
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_get_conversation_forbidden(chat_service):
    user_id = uuid4()
    cid = uuid4()
    chat_service.repository.get_conversation.return_value = _mock_conv(user_id=uuid4(), cid=cid)
    
    with pytest.raises(AppError) as exc:
        await chat_service.get_conversation(cid, user_id)
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_update_conversation(chat_service):
    user_id = uuid4()
    cid = uuid4()
    chat_service.repository.get_conversation.return_value = _mock_conv(user_id=user_id, cid=cid)
    chat_service.repository.update_conversation.return_value = _mock_conv(user_id=user_id, cid=cid)
    
    dto = ConversationUpdateDto(title="New", is_archived=True, is_pinned=True)
    res = await chat_service.update_conversation(user_id, cid, dto)
    assert res.id == cid
    chat_service.repository.update_conversation.assert_called_once()

@pytest.mark.asyncio
async def test_delete_conversation(chat_service):
    user_id = uuid4()
    cid = uuid4()
    chat_service.repository.get_conversation.return_value = _mock_conv(user_id=user_id, cid=cid)
    
    await chat_service.delete_conversation(user_id, cid)
    chat_service.repository.delete_conversation.assert_called_once_with(cid)

@pytest.mark.asyncio
async def test_archive_conversation(chat_service):
    user_id = uuid4()
    cid = uuid4()
    chat_service.repository.get_conversation.return_value = _mock_conv(user_id=user_id, cid=cid)
    chat_service.repository.update_conversation.return_value = _mock_conv(user_id=user_id, cid=cid)
    
    await chat_service.archive_conversation(user_id, cid)
    chat_service.repository.update_conversation.assert_called_once_with(cid, is_archived=True)

@pytest.mark.asyncio
async def test_pin_conversation(chat_service):
    user_id = uuid4()
    cid = uuid4()
    chat_service.repository.get_conversation.return_value = _mock_conv(user_id=user_id, cid=cid)
    chat_service.repository.update_conversation.return_value = _mock_conv(user_id=user_id, cid=cid)
    
    await chat_service.pin_conversation(user_id, cid)
    chat_service.repository.update_conversation.assert_called_once_with(cid, is_pinned=True)

@pytest.mark.asyncio
async def test_add_message(chat_service):
    user_id = uuid4()
    cid = uuid4()
    chat_service.repository.get_conversation.return_value = _mock_conv(user_id=user_id, cid=cid)
    chat_service.repository.add_message.return_value = _mock_msg()
    
    dto = MessageCreateDto(sender="user", content="Hi", message_type="text")
    res = await chat_service.add_message(cid, user_id, dto)
    
    assert res.content == "Hi"
    chat_service.repository.add_message.assert_called_once()

@pytest.mark.asyncio
async def test_get_messages(chat_service):
    user_id = uuid4()
    cid = uuid4()
    chat_service.repository.get_conversation.return_value = _mock_conv(user_id=user_id, cid=cid)
    chat_service.repository.get_messages.return_value = [_mock_msg()]
    
    res = await chat_service.get_messages(cid, user_id)
    assert len(res) == 1
