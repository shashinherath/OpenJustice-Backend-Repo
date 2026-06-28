import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.services.llm_service import LLMService
    from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain.interfaces.whatsapp_client import IWhatsAppClient
from app.application.services.language_detection_service import LanguageDetectionService
from app.application.services.temp_file_manager import TempFileManager
from app.application.services.speech_to_text_service import SpeechToTextService
from app.application.services.text_to_speech_service import TextToSpeechService
from app.application.services.retrieval_service import RetrievalService
from app.infrastructure.repositories.document_repository import DocumentRepository
from sqlalchemy import select
from app.infrastructure.models.user import User
from app.infrastructure.models.conversation import Conversation
from app.infrastructure.repositories.pg_retrieval_log_repository import PgRetrievalLogRepository
from app.domain.interfaces.audio_log_repository import IAudioLogRepository
import time
import mimetypes

# Ensure Windows/FastAPI serves .ogg with correct audio MIME type for Twilio
mimetypes.add_type('audio/ogg', '.ogg')

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service to handle WhatsApp messaging logic."""

    def __init__(self, whatsapp_client: IWhatsAppClient, llm_service: "LLMService", db: "AsyncSession", audio_log_repository: IAudioLogRepository = None, system_settings_repository: "SystemSettingsRepository" = None):
        self.whatsapp_client = whatsapp_client
        self.llm_service = llm_service
        self.db = db
        self.audio_log_repository = audio_log_repository
        self.system_settings_repository = system_settings_repository
        # Initialize retrieval service mapping strictly to DB session
        self.retrieval_log_repo = PgRetrievalLogRepository(db)
        from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
        
        repo_to_use = system_settings_repository or SystemSettingsRepository(db)
        
        self.retrieval_service = RetrievalService(
            DocumentRepository(db), 
            log_repository=self.retrieval_log_repo,
            system_settings_repository=repo_to_use
        )

    async def handle_incoming_message(self, from_number: str, body: str = None, media_url: str = None) -> None:
        """
        Process an incoming WhatsApp message or Voice Note, securely execute STT/RAG/LLM 
        intelligence, and optionally bounce TTS AI audio natively back to Twilio networks.
        """
        logger.info(f"Received WhatsApp ping from {from_number}: Body={body}, Media={media_url}")
        
        if not body and not media_url:
            return
            
        audio_path = None
        out_audio_path = None
        
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
            
        has_voiced = False
        if media_url:
            has_voiced = True

            try:
                sid = None
                token = None
                if self.system_settings_repository:
                    sys_settings = await self.system_settings_repository.get_settings()
                    sid = sys_settings.twilio_account_sid
                    token = sys_settings.twilio_auth_token
                    
                audio_path = await TempFileManager.download_twilio_audio(media_url, twilio_sid=sid, twilio_token=token)
                stt_service = SpeechToTextService(system_settings_repository=self.system_settings_repository)
                
                start_time = time.perf_counter()
                body = await stt_service.transcribe_audio(audio_path)
                stt_latency = time.perf_counter() - start_time
                
                logger.info(f"Interpreted WhatsApp Voice Note as: {body}")
                
                if self.audio_log_repository:
                    await self.audio_log_repository.log_audio_request(
                        user_id=user.id,
                        audio_type="stt",
                        language="auto",
                        duration_seconds=stt_latency,
                        provider="OpenAI Whisper"
                    )
            except Exception as e:
                logger.error(f"Whisper pipeline crashed on media payload: {e}")
                body = "(Inaudible media message received)"
            
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
            # 3a. Retrieve intelligent Context explicitly to maintain separation of concerns
            chunks, confidence = await self.retrieval_service.retrieve(query=body)
            context = "\n\n---\n\n".join([f"REFERENCE TEXT:\n{c.content}" for c in chunks])
            
            # 3b. Execute LLM using the extracted Context
            reply_message = await self.llm_service.generate_response(
                conversation_id=conv.id, 
                user_id=user.id, 
                query=body,
                context=context
            )
            
            # 4. Synthesize Audio back out if user spoke
            if has_voiced:
                try:
                    tts_service = TextToSpeechService(system_settings_repository=self.system_settings_repository)
                    
                    start_time = time.perf_counter()
                    out_audio_path = await tts_service.synthesize_speech(reply_message)
                    tts_latency = time.perf_counter() - start_time
                    
                    if self.audio_log_repository:
                        await self.audio_log_repository.log_audio_request(
                            user_id=user.id,
                            audio_type="tts",
                            language=None,
                            duration_seconds=tts_latency,
                            provider="OpenAI TTS"
                        )
                    
                    # Serve via the /temp static mount using PUBLIC_BASE_URL
                    filename = out_audio_path.split("/")[-1].split("\\")[-1]
                    public_media_url = f"{settings.PUBLIC_BASE_URL}/temp/{filename}"
                    
                    await self.whatsapp_client.send_message(
                        to=from_number,
                        media_url=public_media_url
                    )
                    
                    if audio_path:
                        TempFileManager.delete_file_immediately(audio_path)
                    if out_audio_path:
                        TempFileManager.schedule_deletion(out_audio_path, delay_seconds=120)
                        
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
            
        if audio_path:
            TempFileManager.delete_file_immediately(audio_path)
        if out_audio_path:
            TempFileManager.schedule_deletion(out_audio_path, delay_seconds=120)
