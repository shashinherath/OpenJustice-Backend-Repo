from uuid import UUID
from pathlib import Path

from fastapi import Request

from app.presentation.schemas.chat_schema import MessageResponse


def build_public_audio_url(request: Request, audio_path: str | None) -> str | None:
    """Build a stable public URL for a persisted audio file."""
    if not audio_path:
        return None

    audio_file = Path(audio_path)
    if not audio_file.exists():
        return None

    return f"{str(request.base_url).rstrip('/')}/media/{audio_file.name}"


def map_message_response(
    request: Request,
    conversation_id: UUID,
    message,
) -> MessageResponse:
    """Convert a message DTO into an API response with a playable audio URL."""
    audio_url = build_public_audio_url(request, getattr(message, "audio_path", None))
    if audio_url is None and message.message_type == "voice":
        audio_url = (
            f"{str(request.base_url).rstrip('/')}/api/chats/{conversation_id}/messages/{message.id}/audio"
        )

    return MessageResponse.model_validate(message).model_copy(update={"audio_url": audio_url})
