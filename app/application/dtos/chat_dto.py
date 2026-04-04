from pydantic import BaseModel


class ConversationCreateDto(BaseModel):
    title: str
    channel: str = "web"


class MessageCreateDto(BaseModel):
    content: str
    sender: str = "user"
    message_type: str = "text"
