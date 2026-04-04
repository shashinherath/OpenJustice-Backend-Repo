from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.chat_dto import ConversationCreateDto, MessageCreateDto
from app.application.services.chat_service import ChatService
from app.infrastructure.db.base import get_db
from app.presentation.schemas.chat_schema import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)

router = APIRouter(prefix="/chats", tags=["Chats"])


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


def get_current_user_id(request: Request) -> int:
    """Extract user ID from request state injected by auth_middleware."""
    user = getattr(request.state, "user", None)
    if user and "sub" in user:
        return int(user["sub"])
    return -1


@router.post(
    "", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    data: ConversationCreate,
    request: Request,
    service: ChatService = Depends(get_chat_service),
):
    """Create a new conversation thread."""
    user_id = get_current_user_id(request)
    dto = ConversationCreateDto(title=data.title, channel=data.channel)
    return await service.create_conversation(user_id, dto)


@router.get("", response_model=List[ConversationResponse])
async def get_conversations(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    service: ChatService = Depends(get_chat_service),
):
    """List all conversations for the current user."""
    user_id = get_current_user_id(request)
    return await service.get_user_conversations(user_id, skip, limit)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    request: Request,
    service: ChatService = Depends(get_chat_service),
):
    """Get a specific conversation and all its messages."""
    user_id = get_current_user_id(request)
    conversation = await service.get_conversation(conversation_id, user_id)
    messages = await service.get_messages(conversation_id, user_id)

    response = ConversationDetailResponse.model_validate(conversation)
    response.messages = [MessageResponse.model_validate(m) for m in messages]
    return response


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    conversation_id: int,
    data: MessageCreate,
    request: Request,
    service: ChatService = Depends(get_chat_service),
):
    """Add a new message to a conversation thread."""
    user_id = get_current_user_id(request)
    dto = MessageCreateDto(
        content=data.content, sender=data.sender, message_type=data.message_type
    )
    return await service.add_message(conversation_id, user_id, dto)
