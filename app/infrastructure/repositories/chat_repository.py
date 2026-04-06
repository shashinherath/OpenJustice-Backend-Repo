from uuid import UUID
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.chat_repository import IChatRepository
from app.infrastructure.models.conversation import Conversation
from app.infrastructure.models.message import Message


class ChatRepository(IChatRepository):
    """Data access layer for Chat operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self, user_id: UUID, title: str, channel: str = "web"
    ) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title, channel=channel)
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def get_conversations_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalars().first()

    async def add_message(
        self, conversation_id: UUID, sender: str, content: str, message_type: str = "text"
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            sender=sender,
            content=content,
            message_type=message_type,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(
        self, conversation_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
