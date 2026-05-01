import logging
from fastapi import APIRouter, Form, Depends, Response, BackgroundTasks

from app.application.services.whatsapp_service import WhatsAppService
from app.infrastructure.external.twilio_client import TwilioWhatsAppClient

from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.base import get_db
from app.application.services.llm_service import LLMService
from app.application.services.chat_service import ChatService
from app.application.services.rag_service import RAGService
from app.infrastructure.external.openai_client import OpenAIClient
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.pgvector_semantic_cache_repository import PgVectorSemanticCacheRepository
from app.infrastructure.repositories.pg_llm_log_repository import PgLLMLogRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


def get_whatsapp_service(db: AsyncSession = Depends(get_db)) -> WhatsAppService:
    """Dependency injection for WhatsAppService."""
    client = TwilioWhatsAppClient()
    
    chat_svc = ChatService(db)
    semantic_cache = PgVectorSemanticCacheRepository(db)
    llm_log_repo = PgLLMLogRepository(db)
    
    llm_service = LLMService(chat_svc, OpenAIClient(), semantic_cache=semantic_cache, llm_log_repository=llm_log_repo)
    return WhatsAppService(whatsapp_client=client, llm_service=llm_service, db=db)


@router.post("/webhook")
async def twilio_webhook(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(""),
    MediaUrl0: str = Form(None),
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """
    Webhook endpoint to receive incoming WhatsApp messages from Twilio.
    
    Args:
        Body: The text content of the message.
        From: The sender's WhatsApp number.
        To: The Twilio sandbox number.
        background_tasks: FastAPI background tasks to process without blocking Twilio.
        whatsapp_service: The injected service dependency.
    """
    logger.info(f"Incoming webhook from Twilio: From={From}, Body={Body}")
    
    # Run the handler in the background to ensure we return a 200 OK
    # to Twilio immediately. Twilio expects a response within 15 seconds.
    background_tasks.add_task(
        whatsapp_service.handle_incoming_message,
        from_number=From,
        body=Body,
        media_url=MediaUrl0
    )
    
    # Return empty TwiML response. Twilio interprets this as "Received OK, no immediate reply".
    return Response(content="<Response></Response>", media_type="application/xml")
