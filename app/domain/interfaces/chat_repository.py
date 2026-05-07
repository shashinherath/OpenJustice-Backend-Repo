from uuid import UUID
from abc import ABC, abstractmethod
from typing import Optional

from app.infrastructure.models.conversation import Conversation
from app.infrastructure.models.message import Message


class IChatRepository(ABC):
    """Interface for conversational data access."""

    @abstractmethod
    async def create_conversation(
        self, user_id: UUID, title: str, channel: str = "web"
    ) -> Conversation:
        """Create a new conversation thread."""
        pass

    @abstractmethod
    async def get_conversations_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Conversation]:
        """Fetch all conversations belonging to a user."""
        pass

    @abstractmethod
    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Fetch a specific conversation by ID."""
        pass

    @abstractmethod
    async def update_conversation(
        self, conversation_id: UUID, **kwargs
    ) -> Optional[Conversation]:
        """Update a conversation by ID."""
        pass

    @abstractmethod
    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """Delete a conversation by ID."""
        pass

    @abstractmethod
    async def add_message(
        self, conversation_id: UUID, sender: str, content: str, message_type: str = "text"
    ) -> Message:
        """Add a new message to a conversation."""
        pass

    @abstractmethod
    async def get_messages(
        self, conversation_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Message]:
        """Fetch messages for a given conversation."""
        pass
