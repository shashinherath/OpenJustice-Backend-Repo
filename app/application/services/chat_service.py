from uuid import UUID
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.chat_dto import (
    ConversationCreateDto,
    MessageCreateDto,
    ConversationResultDto,
    MessageResultDto,
)
from app.application.exceptions.app_errors import AppError
from app.domain.interfaces.chat_repository import IChatRepository
from app.infrastructure.models.conversation import Conversation
from app.infrastructure.models.message import Message
from app.infrastructure.repositories.chat_repository import ChatRepository


class ChatService:
    """Business logic for Chat operations."""

    def __init__(self, db: AsyncSession):
        self.repository: IChatRepository = ChatRepository(db)

    def _map_conversation(self, conversation: Conversation) -> ConversationResultDto:
        return ConversationResultDto(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            channel=conversation.channel,
            created_at=conversation.created_at,
        )

    def _map_message(self, message: Message) -> MessageResultDto:
        return MessageResultDto(
            id=message.id,
            conversation_id=message.conversation_id,
            sender=message.sender,
            content=message.content,
            message_type=message.message_type,
            created_at=message.created_at,
        )

    async def create_conversation(
        self, user_id: UUID, data: ConversationCreateDto
    ) -> ConversationResultDto:
        """Create a new conversation."""
        conversation = await self.repository.create_conversation(
            user_id=user_id, title=data.title, channel=data.channel
        )
        return self._map_conversation(conversation)

    async def get_user_conversations(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ConversationResultDto]:
        """Get all conversations for a specific user."""
        conversations = await self.repository.get_conversations_by_user(user_id, skip, limit)
        return [self._map_conversation(c) for c in conversations]

    async def get_conversation(
        self, conversation_id: UUID, user_id: UUID
    ) -> ConversationResultDto:
        """Get a specific conversation, ensuring the user owns it."""
        conversation = await self.repository.get_conversation(conversation_id)
        if not conversation:
            raise AppError(
                message="Conversation not found",
                status_code=404,
                error_code="NOT_FOUND",
            )
        if conversation.user_id != user_id:
            raise AppError(
                message="Permission denied",
                status_code=403,
                error_code="FORBIDDEN",
            )
        return self._map_conversation(conversation)

    async def add_message(
        self, conversation_id: UUID, user_id: UUID, data: MessageCreateDto
    ) -> MessageResultDto:
        """Add a message to a conversation."""
        # Ensure conversation exists and user owns it
        await self.get_conversation(conversation_id, user_id)

        message = await self.repository.add_message(
            conversation_id=conversation_id,
            sender=data.sender,
            content=data.content,
            message_type=data.message_type,
        )
        return self._map_message(message)

    async def get_messages(
        self, conversation_id: UUID, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[MessageResultDto]:
        """Fetch messages for a conversation."""
        # Ensure conversation exists and user owns it
        await self.get_conversation(conversation_id, user_id)
        messages = await self.repository.get_messages(conversation_id, skip, limit)
        return [self._map_message(m) for m in messages]
