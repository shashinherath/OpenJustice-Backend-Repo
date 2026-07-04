import logging
from typing import AsyncGenerator, Dict, List, Any
from uuid import UUID
import time
import tiktoken
import re
import traceback

from app.application.services.system_error_logger import log_system_error

from app.application.dtos.chat_dto import MessageCreateDto
from app.application.services.chat_service import ChatService

from app.domain.interfaces.llm_client import ILLMClient
from app.application.services.language_detection_service import LanguageDetectionService

from app.infrastructure.security.prompt_security import PromptSecurityValidator
from app.application.prompts.multilingual import MultilingualPromptBuilder
from app.domain.interfaces.semantic_cache_repository import ISemanticCacheRepository
from app.domain.interfaces.llm_log_repository import ILLMLogRepository
from app.domain.interfaces.citation_repository import ICitationRepository
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
from langchain_openai import OpenAIEmbeddings
from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Orchestrates interactions between the Chat history, RAG vectors, and Language Models."""

    # Disclaimers are now natively handled by the MultilingualPromptBuilder.

    def __init__(self, chat_service: ChatService, llm_client: ILLMClient, semantic_cache: ISemanticCacheRepository = None, llm_log_repository: ILLMLogRepository = None, citation_repository: ICitationRepository = None, system_settings_repository: SystemSettingsRepository = None):
        self.chat_service = chat_service
        self.llm_client = llm_client
        self.semantic_cache = semantic_cache
        self.llm_log_repository = llm_log_repository
        self.citation_repository = citation_repository
        self.system_settings_repository = system_settings_repository
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL, 
            api_key=settings.OPENAI_API_KEY
        )

    def _count_tokens(self, text: str) -> int:
        """Approximates token count for telemetry."""
        try:
            encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
            return len(encoding.encode(text))
        except Exception:
            return int(len(text.split()) * 1.3)

    async def _build_messages(self, conversation_id: UUID, user_id: UUID, query: str, context: str) -> List[Dict[str, Any]]:
        """Constructs the full system-history-context message array for LLMs."""
        
        system_settings = None
        if self.system_settings_repository:
            system_settings = await self.system_settings_repository.get_settings()

        # Security Check & Sanitize
        safe_query = query
        if system_settings is None or system_settings.prompt_validation_enabled:
            is_safe, violations = PromptSecurityValidator.is_safe(query)
            if not is_safe:
                logger.warning(f"Prompt injection detected on query '{query}': {violations}")
            safe_query = PromptSecurityValidator.sanitize(query)
        
        detected_lang = LanguageDetectionService.detect_language(safe_query)
        
        # Enforce System Settings
        fallback_notice = ""
        is_fallback = False
        if system_settings:
            if detected_lang not in system_settings.enabled_languages:
                logger.info(f"Language '{detected_lang}' is disabled. Falling back to default '{system_settings.default_language}'.")
                detected_lang = system_settings.default_language
                is_fallback = True
                fallback_notice = f"\n\n[SYSTEM NOTICE: The user queried in a language that is currently disabled in the system. You must process their query but respond ONLY in the configured default language (Language code: {detected_lang}).]"
        
        # Fetch dynamic Multilingual Template from Registry
        system_prompt = MultilingualPromptBuilder.build_system_prompt(detected_lang, context)
        
        # Add fallback notice if applicable
        system_prompt += fallback_notice
        
        # Security Marker added to prevent system instruction leakage
        system_prompt += "\n\n[SECURITY_MARKER: OpenJustice_2025]"

        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 1. Fetch recent conversation history limit to last 6 messages to save context windows
        history = await self.chat_service.get_messages(conversation_id, user_id, skip=0, limit=6)
        
        for msg in sorted(history, key=lambda x: x.created_at):
            # Skip the specific query we are answering if it's already in history
            if msg.content == query:
                continue
            role = "user" if msg.sender == "user" else "assistant"
            messages.append({"role": role, "content": msg.content})

        final_prompt = safe_query
        if context:
            final_prompt = f"USER QUERY:\n{safe_query}"
            
        if is_fallback:
            language_map = {"en": "English", "si": "Sinhala", "ta": "Tamil"}
            default_lang_name = language_map.get(detected_lang, detected_lang)
            final_prompt = f"[CRITICAL INSTRUCTION: You MUST respond entirely in {default_lang_name}. DO NOT respond in the language of the query below.]\n\n{final_prompt}"
            
        messages.append({"role": "user", "content": final_prompt})
        
        return messages

    async def generate_response(
        self,
        conversation_id: UUID,
        user_id: UUID,
        query: str,
        context: str,
        message_type: str = "text",
        save_ai_message: bool = True,
        user_audio_path: str | None = None,
    ) -> str:
        """Synchronously block, execute LLM, and save response to database. Checks Semantic Cache first."""
        
        detected_lang = LanguageDetectionService.detect_language(query)
        
        # Save User Message First
        user_msg = MessageCreateDto(
            sender="user",
            content=query,
            message_type=message_type,
            audio_path=user_audio_path,
            language=detected_lang,
        )
        await self.chat_service.add_message(conversation_id, user_id, user_msg)
        
        # Check Semantic Cache
        query_embedding = None
        if self.semantic_cache:
            try:
                # Update embeddings key if dynamic settings exist
                if self.system_settings_repository:
                    sys_settings = await self.system_settings_repository.get_settings()
                    if sys_settings.openai_api_key and sys_settings.openai_api_key != getattr(self.embeddings, 'api_key', settings.OPENAI_API_KEY):
                        self.embeddings = OpenAIEmbeddings(
                            model=self.embeddings.model,
                            api_key=sys_settings.openai_api_key
                        )
                
                # Measure latency for embedding
                emb_start = time.perf_counter()
                query_embedding = await self.embeddings.aembed_query(query)
                emb_latency = int((time.perf_counter() - emb_start) * 1000)
                
                # Log Embedding Telemetry
                if self.llm_log_repository:
                    try:
                        emb_tokens = self._count_tokens(query)
                        await self.llm_log_repository.log_request(
                            user_id=user_id,
                            model_name=self.embeddings.model,
                            query=query,
                            context="Semantic Cache Generation",
                            prompt_version="v1",
                            temperature=0.0,
                            prompt_tokens=emb_tokens,
                            completion_tokens=0,
                            total_tokens=emb_tokens,
                            latency_ms=emb_latency,
                            status="success",
                            error_message=None
                        )
                    except Exception as e:
                        logger.error(f"Embedding telemetry failed: {e}")
                cached_response = await self.semantic_cache.get_similar_response(
                    query_embedding, 
                    similarity_threshold=settings.CACHE_SIMILARITY_THRESHOLD
                )
                if cached_response:
                    logger.info(f"Semantic Cache Hit for query: {query}")
                    # Save AI Message from cache
                    if save_ai_message:
                        ai_msg = MessageCreateDto(sender="ai", content=cached_response, message_type="text")
                        await self.chat_service.add_message(conversation_id, user_id, ai_msg)
                    return cached_response
            except Exception as e:
                logger.error(f"Semantic Cache check failed: {e}", exc_info=True)

        # Build Context Arrays
        # Language is already detected earlier for saving the message
        messages = await self._build_messages(conversation_id, user_id, query, context)
        
        # Fetch dynamic AI parameters
        ai_model = None
        ai_temp = None
        ai_tokens = None
        ai_top_p = None
        ai_freq_pen = None
        
        if self.system_settings_repository:
            system_settings = await self.system_settings_repository.get_settings()
            ai_model = system_settings.ai_model_name
            ai_temp = system_settings.ai_temperature
            ai_tokens = system_settings.ai_max_tokens
            ai_top_p = system_settings.ai_top_p
            ai_freq_pen = system_settings.ai_frequency_penalty

        # Execute LLM Call natively
        start_time = time.perf_counter()
        try:
            response = await self.llm_client.generate_response(
                messages=messages,
                temperature=ai_temp,
                max_tokens=ai_tokens,
                top_p=ai_top_p,
                frequency_penalty=ai_freq_pen,
                model=ai_model
            )
        except Exception as e:
            await log_system_error(
                error_type="LLM",
                message="LLM provider generated an error during request.",
                details=f"Model: {ai_model or settings.OPENAI_MODEL}\n{traceback.format_exc()}"
            )
            raise
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log LLM Telemetry
        if self.llm_log_repository:
            try:
                prompt_text = "".join([m["content"] for m in messages])
                prompt_tokens = self._count_tokens(prompt_text)
                completion_tokens = self._count_tokens(response)
                total_tokens = prompt_tokens + completion_tokens
                
                req_id = await self.llm_log_repository.log_request(
                    user_id=user_id,
                    model_name=ai_model or settings.OPENAI_MODEL,
                    query=query,
                    context=context,
                    prompt_version="v1",
                    temperature=ai_temp if ai_temp is not None else settings.OPENAI_TEMPERATURE,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    latency_ms=latency_ms,
                    status="success",
                    error_message=None
                )
                await self.llm_log_repository.log_response(
                    llm_request_id=req_id,
                    response_text=response,
                    confidence_level="High"
                )
            except Exception as e:
                logger.error(f"LLM telemetry logging failed: {e}", exc_info=True)
                
        # Citation UUID logging removed since LLM now returns Act/Section text natively.
        
        # Save to Semantic Cache
        if self.semantic_cache and query_embedding:
            try:
                await self.semantic_cache.set_response(query, query_embedding, response)
            except Exception as e:
                logger.error(f"Semantic Cache save failed: {e}", exc_info=True)
        
        if save_ai_message:
            ai_msg = MessageCreateDto(sender="ai", content=response, message_type="text")
            await self.chat_service.add_message(conversation_id, user_id, ai_msg)

        return response

    async def stream_response(self, conversation_id: UUID, user_id: UUID, query: str, context: str, message_type: str = "text") -> AsyncGenerator[str, None]:
        """Provides an asynchronous Generator directly streaming the underlying LLM's response block. Checks Semantic Cache first."""
        
        detected_lang = LanguageDetectionService.detect_language(query)
        
        # Save User Message First
        user_msg = MessageCreateDto(sender="user", content=query, message_type=message_type, language=detected_lang)
        await self.chat_service.add_message(conversation_id, user_id, user_msg)
        
        # Check Semantic Cache
        query_embedding = None
        if self.semantic_cache:
            try:
                # Measure latency for embedding
                emb_start = time.perf_counter()
                query_embedding = await self.embeddings.aembed_query(query)
                emb_latency = int((time.perf_counter() - emb_start) * 1000)
                
                # Log Embedding Telemetry
                if self.llm_log_repository:
                    try:
                        emb_tokens = self._count_tokens(query)
                        await self.llm_log_repository.log_request(
                            user_id=user_id,
                            model_name=self.embeddings.model,
                            query=query,
                            context="Semantic Cache Streaming",
                            prompt_version="v1",
                            temperature=0.0,
                            prompt_tokens=emb_tokens,
                            completion_tokens=0,
                            total_tokens=emb_tokens,
                            latency_ms=emb_latency,
                            status="success",
                            error_message=None
                        )
                    except Exception as e:
                        logger.error(f"Embedding telemetry failed: {e}")
                cached_response = await self.semantic_cache.get_similar_response(
                    query_embedding, 
                    similarity_threshold=settings.CACHE_SIMILARITY_THRESHOLD
                )
                if cached_response:
                    logger.info(f"Semantic Cache Hit for stream query: {query}")
                    ai_msg = MessageCreateDto(sender="ai", content=cached_response, message_type="text")
                    await self.chat_service.add_message(conversation_id, user_id, ai_msg)
                    # Yield it as a single chunk to satisfy the streaming interface
                    yield cached_response
                    return
            except Exception as e:
                logger.error(f"Semantic Cache check failed: {e}", exc_info=True)

        # Build Context Arrays
        # Language is already detected earlier for saving the message
        messages = await self._build_messages(conversation_id, user_id, query, context)
        
        # Fetch dynamic AI parameters
        ai_model = None
        ai_temp = None
        ai_tokens = None
        ai_top_p = None
        ai_freq_pen = None
        
        if self.system_settings_repository:
            system_settings = await self.system_settings_repository.get_settings()
            ai_model = system_settings.ai_model_name
            ai_temp = system_settings.ai_temperature
            ai_tokens = system_settings.ai_max_tokens
            ai_top_p = system_settings.ai_top_p
            ai_freq_pen = system_settings.ai_frequency_penalty

        # Stream response back
        full_response = ""
        start_time = time.perf_counter()
        try:
            async for chunk in self.llm_client.stream_response(
                messages=messages,
                temperature=ai_temp,
                max_tokens=ai_tokens,
                top_p=ai_top_p,
                frequency_penalty=ai_freq_pen,
                model=ai_model
            ):
                full_response += chunk
                yield chunk
        except Exception as e:
            await log_system_error(
                error_type="LLM",
                message="LLM provider generated an error during streaming.",
                details=f"Model: {ai_model or settings.OPENAI_MODEL}\n{traceback.format_exc()}"
            )
            raise
                
        finally:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            if full_response.strip():
                ai_msg = MessageCreateDto(sender="ai", content=full_response, message_type="text")
                saved_msg = await self.chat_service.add_message(conversation_id, user_id, ai_msg)
                
                # Citation UUID logging removed since LLM now returns Act/Section text natively.
                
                # Log LLM Telemetry
                if self.llm_log_repository:
                    try:
                        prompt_text = "".join([m["content"] for m in messages])
                        prompt_tokens = self._count_tokens(prompt_text)
                        completion_tokens = self._count_tokens(full_response)
                        total_tokens = prompt_tokens + completion_tokens
                        
                        req_id = await self.llm_log_repository.log_request(
                            user_id=user_id,
                            model_name=ai_model or settings.OPENAI_MODEL,
                            query=query,
                            context=context,
                            prompt_version="v1",
                            temperature=ai_temp if ai_temp is not None else settings.OPENAI_TEMPERATURE,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                            latency_ms=latency_ms,
                            status="success",
                            error_message=None
                        )
                        await self.llm_log_repository.log_response(
                            llm_request_id=req_id,
                            response_text=full_response,
                            confidence_level="High"
                        )
                    except Exception as e:
                        logger.error(f"LLM telemetry stream logging failed: {e}", exc_info=True)
                
                # Save to Semantic Cache
                if self.semantic_cache and query_embedding:
                    try:
                        await self.semantic_cache.set_response(query, query_embedding, full_response)
                    except Exception as e:
                        logger.error(f"Semantic Cache save failed: {e}", exc_info=True)
