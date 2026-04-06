import logging
from fastapi import APIRouter, Form, Depends, Response, BackgroundTasks

from app.application.services.whatsapp_service import WhatsAppService
from app.infrastructure.external.twilio_client import TwilioWhatsAppClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


def get_whatsapp_service() -> WhatsAppService:
    """Dependency injection for WhatsAppService."""
    # In a larger application with a DI framework, this would be managed there.
    client = TwilioWhatsAppClient()
    return WhatsAppService(whatsapp_client=client)


@router.post("/webhook")
async def twilio_webhook(
    background_tasks: BackgroundTasks,
    Body: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
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
        body=Body
    )
    
    # Return empty TwiML response. Twilio interprets this as "Received OK, no immediate reply".
    return Response(content="<Response></Response>", media_type="application/xml")
