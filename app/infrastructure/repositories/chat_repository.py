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

    async def update_conversation(
        self, conversation_id: UUID, **kwargs
    ) -> Optional[Conversation]:
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        for key, value in kwargs.items():
            if hasattr(conversation, key) and value is not None:
                setattr(conversation, key, value)
                
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return False
            
        await self.db.delete(conversation)
        await self.db.commit()
        return True

    async def add_message(
        self,
        conversation_id: UUID,
        sender: str,
        content: str,
        message_type: str = "text",
        audio_path: str | None = None,
        language: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            sender=sender,
            content=content,
            message_type=message_type,
            audio_path=audio_path,
            language=language,
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

    async def get_user_message_count(self) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Message.id)).where(Message.sender == 'user')
        )
        return result.scalar_one_or_none() or 0

    async def get_whatsapp_requests_count(self) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.channel == 'whatsapp')
        )
        return result.scalar_one_or_none() or 0

    async def get_queries_per_day(self, days: int = 7) -> list[dict]:
        from sqlalchemy import func, cast, Date
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days - 1)
        result = await self.db.execute(
            select(
                cast(Message.created_at, Date).label('date'),
                func.count(Message.id).label('count')
            )
            .where(Message.sender == 'user', Message.created_at >= cutoff.date())
            .group_by(cast(Message.created_at, Date))
            .order_by(cast(Message.created_at, Date))
        )
        rows = result.all()
        counts_by_date = {row.date: row.count for row in rows}
        
        formatted = []
        for i in range(days):
            current_date = (cutoff + timedelta(days=i)).date()
            formatted.append({
                "date": current_date.strftime("%a"),
                "count": counts_by_date.get(current_date, 0)
            })
        return formatted

    async def get_voice_queries_count(self) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Message.id)).where(Message.message_type == 'voice')
        )
        return result.scalar_one_or_none() or 0
