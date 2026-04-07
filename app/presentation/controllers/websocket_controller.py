from uuid import UUID
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt

from app.application.services.chat_service import ChatService
from app.config import settings
from app.infrastructure.db.base import get_db
from app.infrastructure.websocket.connection_manager import (
    connection_manager,
    rate_limiter,
)
from app.infrastructure.external.openai_client import OpenAIClient
from app.application.services.llm_service import LLMService
from app.application.services.rag_service import RAGService
from app.infrastructure.repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


async def authenticate_websocket(websocket: WebSocket) -> UUID:
    """Authenticate WebSocket connection using JWT passed in query string."""
    token = websocket.query_params.get("token")

    if not token:
        logger.warning(
            f"WebSocket connection attempt without token from {websocket.client}"
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise JWTError("Invalid token payload")
        return UUID(user_id)
    except JWTError as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)


@router.websocket("/chat/{conversation_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket, conversation_id: UUID, db=Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat.
    Validates user access to the conversation before continuing the duplex connection.
    """
    await websocket.accept()
    user_id = None

    try:
        user_id = await authenticate_websocket(websocket)

        # Verify access to conversation
        chat_service = ChatService(db)
        try:
            await chat_service.get_conversation(conversation_id, user_id)
        except Exception:
            await websocket.send_json(
                {"type": "error", "message": "Conversation not found or access denied."}
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await connection_manager.connect(user_id, websocket)

        await websocket.send_json(
            {
                "type": "connection_established",
                "user_id": user_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        while True:
            data = await websocket.receive_json()

            if not await rate_limiter.is_allowed(user_id):
                await websocket.send_json(
                    {
                        "type": "error",
                        "error": "rate_limit_exceeded",
                        "message": "Too many messages. Please slow down.",
                    }
                )
                continue

            message_type = data.get("type")
            if message_type == "ping":
                await websocket.send_json({"type": "pong"})

            # Route message to intelligence logic
            elif message_type == "chat_message":
                msg_content = data.get("message", "")
                
                doc_repo = DocumentRepository(db)
                rag_service = RAGService(doc_repo)
                llm_service = LLMService(chat_service, rag_service, OpenAIClient())
                
                try:
                    async for chunk in llm_service.stream_response(conversation_id, user_id, msg_content):
                        await websocket.send_json(
                            {
                                "type": "chat_chunk",
                                "chunk": chunk,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                    
                    # Notify frontend that AI has finished typing
                    await websocket.send_json(
                        {
                            "type": "chat_completion",
                            "status": "complete",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                except Exception as e:
                    logger.error(f"WS LLM Error: {e}", exc_info=True)
                    await websocket.send_json({"type": "error", "message": "AI module encountered an error."})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected")
        if user_id:
            await connection_manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        if user_id:
             await connection_manager.disconnect(user_id, websocket)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
