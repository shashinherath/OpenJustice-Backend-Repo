from uuid import UUID
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.chat_dto import ConversationCreateDto, MessageCreateDto
from app.application.exceptions.app_errors import AppError
from app.domain.interfaces.chat_repository import IChatRepository
from app.infrastructure.models.conversation import Conversation
from app.infrastructure.models.message import Message
from app.infrastructure.repositories.chat_repository import ChatRepository


class ChatService:
    """Business logic for Chat operations."""

    def __init__(self, db: AsyncSession):
        self.repository: IChatRepository = ChatRepository(db)

    async def create_conversation(
        self, user_id: UUID, data: ConversationCreateDto
    ) -> Conversation:
        """Create a new conversation."""
        return await self.repository.create_conversation(
            user_id=user_id, title=data.title, channel=data.channel
        )

    async def get_user_conversations(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Conversation]:
        """Get all conversations for a specific user."""
        return await self.repository.get_conversations_by_user(user_id, skip, limit)

    async def get_conversation(self, conversation_id: UUID, user_id: UUID) -> Conversation:
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
        return conversation

    async def add_message(
        self, conversation_id: UUID, user_id: UUID, data: MessageCreateDto
    ) -> Message:
        """Add a message to a conversation."""
        # Ensure conversation exists and user owns it
        await self.get_conversation(conversation_id, user_id)
        
        return await self.repository.add_message(
            conversation_id=conversation_id,
            sender=data.sender,
            content=data.content,
            message_type=data.message_type,
        )

    async def get_messages(
        self, conversation_id: UUID, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        """Fetch messages for a conversation."""
        # Ensure conversation exists and user owns it
        await self.get_conversation(conversation_id, user_id)
        return await self.repository.get_messages(conversation_id, skip, limit)
