import logging

from app.config import settings
from app.domain.interfaces.whatsapp_client import IWhatsAppClient
from sqlalchemy import select
from app.infrastructure.models.user import User
from app.infrastructure.models.conversation import Conversation
from app.application.services.temp_file_manager import TempFileManager
from app.application.services.speech_to_text_service import SpeechToTextService

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service to handle WhatsApp messaging logic."""

    def __init__(self, whatsapp_client: IWhatsAppClient, llm_service: "LLMService", db: "AsyncSession"):
        self.whatsapp_client = whatsapp_client
        self.llm_service = llm_service
        self.db = db

    async def handle_incoming_message(self, from_number: str, body: str = None, media_url: str = None) -> None:
        """
        Process an incoming WhatsApp message or Voice Note, securely execute STT/RAG/LLM 
        intelligence, and optionally bounce TTS AI audio natively back to Twilio networks.
        """
        logger.info(f"Received WhatsApp ping from {from_number}: Body={body}, Media={media_url}")
        
        has_voiced = False
        if media_url:
            has_voiced = True

            try:
                audio_path = await TempFileManager.download_twilio_audio(media_url)
                stt_service = SpeechToTextService()
                body = await stt_service.transcribe_audio(audio_path)
                logger.info(f"Interpreted WhatsApp Voice Note as: {body}")
            except Exception as e:
                logger.error(f"Whisper pipeline crashed on media payload: {e}")
                body = "(Inaudible media message received)"

        if not body and not media_url:
            return
        
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
            
        # 3. Synchronously Execute Intelligence
        try:
            # Execute intelligence RAG loop (LanguageDetection automatically translates prompt natively inside)
            reply_message = await self.llm_service.generate_response(
                conversation_id=conv.id, 
                user_id=user.id, 
                query=body
            )
            
            # 4. Synthesize Audio back out if user spoke
            if has_voiced:
                from app.application.services.text_to_speech_service import TextToSpeechService
                try:
                    tts_service = TextToSpeechService()
                    out_audio_path = await tts_service.synthesize_speech(reply_message)
                    
                    # Serve via the /media static mount using PUBLIC_BASE_URL
                    filename = out_audio_path.split("/")[-1].split("\\")[-1]
                    public_media_url = f"{settings.PUBLIC_BASE_URL}/media/{filename}"
                    
                    await self.whatsapp_client.send_message(
                        to=from_number,
                        body="🎤 Voice Note Response:",
                        media_url=public_media_url
                    )
                    return
                except Exception as e:
                    logger.error(f"Failed to generate TTS outbound response: {e}", exc_info=True)

            # Normal text fallback 
            await self.whatsapp_client.send_message(
                to=from_number,
                body=reply_message
            )
        except Exception as e:
            logger.error(f"Failed to generate LLM sequence for {from_number}: {e}", exc_info=True)
