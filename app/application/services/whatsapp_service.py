import logging

from app.domain.interfaces.whatsapp_client import IWhatsAppClient

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service to handle WhatsApp messaging logic."""

    def __init__(self, whatsapp_client: IWhatsAppClient, llm_service: "LLMService", db: "AsyncSession"):
        self.whatsapp_client = whatsapp_client
        self.llm_service = llm_service
        self.db = db

    async def handle_incoming_message(self, from_number: str, body: str) -> None:
        """
        Process an incoming WhatsApp message, securely execute RAG/LLM intelligence, 
        and bounce AI output natively to Twilio networks.
        """
        logger.info(f"Received WhatsApp message from {from_number}: {body}")
        
        from sqlalchemy import select
        from app.infrastructure.models.user import User
        from app.infrastructure.models.conversation import Conversation
        
        # 1. Lookup or create User dynamically from WhatsApp tag
        phone = from_number.replace('whatsapp:', '').strip()
        result = await self.db.execute(select(User).where(User.phone_number == phone))
        user = result.scalars().first()
        
        if not user:
            # Generate a seamless auto-user for mobile execution tracking 
            user = User(phone_number=phone, hashed_password="whatsapp_auto_user_system", role="user")
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
        # 2. Get or create their mobile channel conversation
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.user_id == user.id, 
                Conversation.channel == "whatsapp"
            )
        )
        conv = result.scalars().first()
        
        if not conv:
            conv = Conversation(user_id=user.id, title="WhatsApp Channel", channel="whatsapp")
            self.db.add(conv)
            await self.db.commit()
            await self.db.refresh(conv)
            
        # 3. Synchronously Execute RAG LLM
        try:
            # Execute intelligence loop
            reply_message = await self.llm_service.generate_response(
                conversation_id=conv.id, 
                user_id=user.id, 
                query=body
            )
            
            # Post back to Twilio Mobile API
            await self.whatsapp_client.send_message(
                to=from_number,
                body=reply_message
            )
        except Exception as e:
            logger.error(f"Failed to generate LLM sequence for {from_number}: {e}")
