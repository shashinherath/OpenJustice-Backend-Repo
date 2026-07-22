import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.infrastructure.repositories.chat_repository import ChatRepository
from app.infrastructure.models.conversation import Conversation
from app.infrastructure.models.message import Message

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def repository(mock_db):
    return ChatRepository(mock_db)

@pytest.mark.asyncio
async def test_create_conversation(repository, mock_db):
    user_id = uuid4()
    title = "Test Conversation"
    
    conversation = await repository.create_conversation(user_id, title)
    
    assert conversation.user_id == user_id
    assert conversation.title == title
    assert conversation.channel == "web"
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_get_conversations_by_user(repository, mock_db):
    user_id = uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [Conversation(id=uuid4()), Conversation(id=uuid4())]
    mock_db.execute.return_value = mock_result
    
    conversations = await repository.get_conversations_by_user(user_id)
    
    assert len(conversations) == 2
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_conversation(repository, mock_db):
    conv_id = uuid4()
    mock_conv = Conversation(id=conv_id)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_conv
    mock_db.execute.return_value = mock_result
    
    conversation = await repository.get_conversation(conv_id)
    
    assert conversation is not None
    assert conversation.id == conv_id
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_update_conversation(repository, mock_db):
    conv_id = uuid4()
    mock_conv = Conversation(id=conv_id, title="Old Title")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_conv
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_conversation(conv_id, title="New Title")
    
    assert updated is not None
    assert updated.title == "New Title"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_update_conversation_not_found(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_conversation(uuid4(), title="New Title")
    
    assert updated is None

@pytest.mark.asyncio
async def test_delete_conversation(repository, mock_db):
    conv_id = uuid4()
    mock_conv = Conversation(id=conv_id)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_conv
    mock_db.execute.return_value = mock_result
    
    result = await repository.delete_conversation(conv_id)
    
    assert result is True
    mock_db.delete.assert_called_once_with(mock_conv)
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_delete_conversation_not_found(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    result = await repository.delete_conversation(uuid4())
    
    assert result is False

@pytest.mark.asyncio
async def test_add_message(repository, mock_db):
    conv_id = uuid4()
    
    message = await repository.add_message(
        conversation_id=conv_id,
        sender="user",
        content="Hello",
        message_type="text",
        audio_path=None,
        language="en"
    )
    
    assert message.conversation_id == conv_id
    assert message.sender == "user"
    assert message.content == "Hello"
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_get_messages(repository, mock_db):
    conv_id = uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [Message(id=uuid4()), Message(id=uuid4())]
    mock_db.execute.return_value = mock_result
    
    messages = await repository.get_messages(conv_id)
    
    assert len(messages) == 2
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_user_message_count(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 42
    mock_db.execute.return_value = mock_result
    
    count = await repository.get_user_message_count()
    
    assert count == 42

@pytest.mark.asyncio
async def test_get_whatsapp_requests_count(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 10
    mock_db.execute.return_value = mock_result
    
    count = await repository.get_whatsapp_requests_count()
    
    assert count == 10

@pytest.mark.asyncio
async def test_get_queries_per_day(repository, mock_db):
    mock_result = MagicMock()
    
    row1 = MagicMock()
    row1.date = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    row1.count = 5
    
    mock_result.all.return_value = [row1]
    mock_db.execute.return_value = mock_result
    
    days = 7
    results = await repository.get_queries_per_day(days)
    
    assert len(results) == days
    assert all("date" in r and "count" in r for r in results)

@pytest.mark.asyncio
async def test_get_voice_queries_count(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 15
    mock_db.execute.return_value = mock_result
    
    count = await repository.get_voice_queries_count()
    
    assert count == 15
