from uuid import UUID
import uuid
from typing import List
from pathlib import Path
import os
import shutil

from fastapi import APIRouter, Depends, Request, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import StreamingResponse, FileResponse

from app.application.dtos.chat_dto import ConversationCreateDto, MessageCreateDto, ConversationUpdateDto
from app.application.services.chat_service import ChatService
from app.config import settings
from app.infrastructure.db.base import get_db
from app.presentation.schemas.chat_schema import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    MessageCompleteRequest,
)
from app.presentation.mappers.chat_mapper import map_message_response

# Services for AI Response
from app.infrastructure.external.openai_client import OpenAIClient
from app.application.services.llm_service import LLMService
from app.application.services.retrieval_service import RetrievalService
from app.application.services.speech_to_text_service import SpeechToTextService
from app.application.services.text_to_speech_service import TextToSpeechService
from app.application.services.temp_file_manager import TempFileManager
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.pgvector_semantic_cache_repository import PgVectorSemanticCacheRepository
from app.infrastructure.repositories.pg_llm_log_repository import PgLLMLogRepository
from app.infrastructure.repositories.pg_retrieval_log_repository import PgRetrievalLogRepository
from app.infrastructure.repositories.pg_citation_repository import PgCitationRepository
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository

# Services for AI Response
from app.infrastructure.external.openai_client import OpenAIClient
from app.application.services.llm_service import LLMService
from app.application.services.retrieval_service import RetrievalService
from app.application.services.speech_to_text_service import SpeechToTextService
from app.application.services.text_to_speech_service import TextToSpeechService
from app.application.services.temp_file_manager import TempFileManager
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.pgvector_semantic_cache_repository import PgVectorSemanticCacheRepository
from app.infrastructure.repositories.pg_llm_log_repository import PgLLMLogRepository
from app.infrastructure.repositories.pg_retrieval_log_repository import PgRetrievalLogRepository
from app.infrastructure.repositories.pg_citation_repository import PgCitationRepository

router = APIRouter(prefix="/chats", tags=["Chats"])


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


from fastapi import HTTPException

def get_current_user_id(request: Request) -> UUID:
    """Extract user ID from request state injected by auth_middleware."""
    user = getattr(request.state, "user", None)
    if user and "sub" in user:
        return UUID(user["sub"])
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def _persist_audio_file(source_path: str, prefix: str) -> str:
    """Copy an audio file into the persistent media directory and return its path."""
    os.makedirs(settings.AUDIO_MEDIA_DIR, exist_ok=True)
    suffix = Path(source_path).suffix or ".ogg"
    target_path = Path(settings.AUDIO_MEDIA_DIR) / f"{prefix}_{uuid.uuid4().hex}{suffix}"
    shutil.copy2(source_path, target_path)
    return str(target_path)


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
    conversation_id: UUID,
    request: Request,
    service: ChatService = Depends(get_chat_service),
):
    """Get a specific conversation and all its messages."""
    user_id = get_current_user_id(request)
    conversation = await service.get_conversation(conversation_id, user_id)
    messages = await service.get_messages(conversation_id, user_id)

    response = ConversationDetailResponse.model_validate(conversation)
    response.messages = [
        map_message_response(request, conversation_id, message)
        for message in messages
    ]
    return response


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    conversation_id: UUID,
    data: MessageCreate,
    request: Request,
    service: ChatService = Depends(get_chat_service),
):
    """Add a new message to a conversation thread."""
    user_id = get_current_user_id(request)
    dto = MessageCreateDto(
        content=data.content,
        sender=data.sender,
        message_type=data.message_type,
    )
    return await service.add_message(conversation_id, user_id, dto)


@router.get("/{conversation_id}/messages/{message_id}/audio")
async def get_message_audio(
    conversation_id: UUID,
    message_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
):
    """Return a playable audio file for a voice message, or synthesize one on demand."""
    user_id = get_current_user_id(request)
    await service.get_conversation(conversation_id, user_id)
    messages = await service.get_messages(conversation_id, user_id)
    message = next((item for item in messages if item.id == message_id), None)
    if not message or message.message_type != "voice":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice message not found")

    if getattr(message, "audio_path", None) and os.path.exists(message.audio_path):
        return FileResponse(
            path=message.audio_path,
            media_type="audio/ogg",
            filename="voice-note.ogg",
        )

    tts_service = TextToSpeechService()
    synthesized_path = await tts_service.synthesize_speech(message.content or "")
    return FileResponse(
        path=synthesized_path,
        media_type="audio/ogg",
        filename="voice-note.ogg",
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    data: ConversationUpdate,
    request: Request,
    service: ChatService = Depends(get_chat_service),
):
    """Update conversation details like title, archived status, or pinned status."""
    user_id = get_current_user_id(request)
    dto = ConversationUpdateDto(
        title=data.title,
        is_archived=data.is_archived,
        is_pinned=data.is_pinned,
    )
    return await service.update_conversation(user_id, conversation_id, dto)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    request: Request,
    service: ChatService = Depends(get_chat_service),
):
    """Delete a conversation thread completely."""
    user_id = get_current_user_id(request)
    await service.delete_conversation(user_id, conversation_id)


@router.patch("/{conversation_id}/archive", response_model=ConversationResponse)
async def archive_conversation(
    conversation_id: UUID,
    request: Request,
    service: ChatService = Depends(get_chat_service),
):
    """Archive a conversation."""
    user_id = get_current_user_id(request)
    return await service.archive_conversation(user_id, conversation_id)


@router.patch("/{conversation_id}/pin", response_model=ConversationResponse)
async def pin_conversation(
    conversation_id: UUID,
    request: Request,
    service: ChatService = Depends(get_chat_service),
):
    """Pin a conversation."""
    user_id = get_current_user_id(request)
    return await service.pin_conversation(user_id, conversation_id)


@router.post("/{conversation_id}/messages/complete")
async def complete_message(
    conversation_id: UUID,
    data: MessageCompleteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
):
    """Generate an AI reply based on user query and conversation context, streaming the response."""
    user_id = get_current_user_id(request)
    
    doc_repo = DocumentRepository(db)
    retrieval_log_repo = PgRetrievalLogRepository(db)
    retrieval_service = RetrievalService(doc_repo, log_repository=retrieval_log_repo)
    
    semantic_cache = PgVectorSemanticCacheRepository(db)
    llm_log_repo = PgLLMLogRepository(db)
    citation_repo = PgCitationRepository(db)
    
    llm_service = LLMService(
        service, 
        OpenAIClient(), 
        semantic_cache=semantic_cache, 
        llm_log_repository=llm_log_repo,
        citation_repository=citation_repo,
        system_settings_repository=SystemSettingsRepository(db)
    )

    # Note: Stream response expects to save the user message automatically via query.
    # However, retrieval service can be used optionally here to supplement context.
    # We will run retrieval first.
    chunks, confidence = await retrieval_service.retrieve(query=data.query)
    context = data.context
    if chunks:
        context_add = "\n\n---\n\n".join([f"REFERENCE TEXT:\n{c.content}" for c in chunks])
        context = f"{context}\n\n{context_add}"

    async def event_generator():
        async for chunk in llm_service.stream_response(conversation_id, user_id, data.query, context):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")


@router.post("/{conversation_id}/messages/voice")
async def voice_message(
    conversation_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
):
    """Process an uploaded voice note, generate an AI reply, and return the synthesized audio response."""
    user_id = get_current_user_id(request)
    
    # 1. Save uploaded file
    in_audio_path = await TempFileManager.save_upload_file(file)
    user_audio_path = _persist_audio_file(in_audio_path, "voice_user")
    
    # 2. Transcribe
    stt_service = SpeechToTextService()
    query = await stt_service.transcribe_audio(in_audio_path)
    
    # 3. Retrieve context
    doc_repo = DocumentRepository(db)
    retrieval_log_repo = PgRetrievalLogRepository(db)
    retrieval_service = RetrievalService(doc_repo, log_repository=retrieval_log_repo)
    
    chunks, confidence = await retrieval_service.retrieve(query=query)
    context = ""
    if chunks:
        context = "\n\n---\n\n".join([f"REFERENCE TEXT:\n{c.content}" for c in chunks])
        
    # 4. Generate LLM Response
    semantic_cache = PgVectorSemanticCacheRepository(db)
    llm_log_repo = PgLLMLogRepository(db)
    citation_repo = PgCitationRepository(db)
    
    llm_service = LLMService(
        service, 
        OpenAIClient(), 
        semantic_cache=semantic_cache, 
        llm_log_repository=llm_log_repo,
        citation_repository=citation_repo,
        system_settings_repository=SystemSettingsRepository(db)
    )
    
    ai_reply = await llm_service.generate_response(
        conversation_id,
        user_id,
        query,
        context,
        message_type="voice",
        save_ai_message=False,
        user_audio_path=user_audio_path,
    )
    
    # 5. Synthesize Audio
    tts_service = TextToSpeechService()
    out_audio_path = await tts_service.synthesize_speech(ai_reply)
    ai_audio_path = _persist_audio_file(out_audio_path, "voice_ai")

    await service.add_message(
        conversation_id,
        user_id,
        MessageCreateDto(
            sender="ai",
            content=ai_reply,
            message_type="voice",
            audio_path=ai_audio_path,
        ),
    )
    
    # 6. Return audio natively
    return FileResponse(
        path=ai_audio_path,
        media_type="audio/ogg",
        filename="response.ogg"
    )
