from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID
from datetime import datetime

@dataclass(frozen=True)
class ConversationCreateDto:
    title: str
    channel: str = "web"

@dataclass(frozen=True)
class MessageCreateDto:
    content: str
    sender: str = "user"
    message_type: str = "text"

@dataclass(frozen=True)
class MessageResultDto:
    id: UUID
    conversation_id: UUID
    sender: str
    content: str
    message_type: str
    created_at: datetime

@dataclass(frozen=True)
class ConversationResultDto:
    id: UUID
    user_id: UUID
    title: Optional[str]
    channel: Optional[str]
    created_at: datetime

@dataclass(frozen=True)
class ConversationDetailDto(ConversationResultDto):
    messages: list[MessageResultDto]
