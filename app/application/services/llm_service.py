import logging
from typing import AsyncGenerator, Dict, List, Any
from uuid import UUID

from app.application.dtos.chat_dto import MessageCreateDto
from app.application.services.chat_service import ChatService

from app.domain.interfaces.llm_client import ILLMClient
from app.application.services.language_detection_service import LanguageDetectionService

from app.infrastructure.security.prompt_security import PromptSecurityValidator
from app.application.prompts.multilingual import MultilingualPromptBuilder

logger = logging.getLogger(__name__)

class LLMService:
    """Orchestrates interactions between the Chat history, RAG vectors, and Language Models."""

    def __init__(self, chat_service: ChatService, llm_client: ILLMClient):
        self.chat_service = chat_service
        self.llm_client = llm_client

    async def _build_messages(self, conversation_id: UUID, user_id: UUID, query: str, context: str) -> List[Dict[str, Any]]:
        """Constructs the full system-history-context message array for LLMs."""
        
        # Security Check & Sanitize
        is_safe, violations = PromptSecurityValidator.is_safe(query)
        if not is_safe:
            logger.warning(f"Prompt injection detected on query '{query}': {violations}")
        safe_query = PromptSecurityValidator.sanitize(query)
        
        detected_lang = LanguageDetectionService.detect_language(safe_query)
        
        # Fetch dynamic Multilingual Template from Registry
        system_prompt = MultilingualPromptBuilder.build_system_prompt(detected_lang, context)
        
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
            
        messages.append({"role": "user", "content": final_prompt})
        
        return messages

    async def generate_response(self, conversation_id: UUID, user_id: UUID, query: str, context: str, message_type: str = "text") -> str:
        """Synchronously block, execute LLM, and save response to database."""
        
        # Save User Message First
        user_msg = MessageCreateDto(sender="user", content=query, message_type=message_type)
        await self.chat_service.add_message(conversation_id, user_id, user_msg)
        
        # Build Context Arrays
        messages = await self._build_messages(conversation_id, user_id, query, context)
        
        # Execute LLM Call natively
        response = await self.llm_client.generate_response(messages)
        
        # Save AI Message
        ai_msg = MessageCreateDto(sender="ai", content=response, message_type="text")
        await self.chat_service.add_message(conversation_id, user_id, ai_msg)
        
        return response

    async def stream_response(self, conversation_id: UUID, user_id: UUID, query: str, context: str, message_type: str = "text") -> AsyncGenerator[str, None]:
        """Provides an asynchronous Generator directly streaming the underlying LLM's response block."""
        
        # Save User Message First
        user_msg = MessageCreateDto(sender="user", content=query, message_type=message_type)
        await self.chat_service.add_message(conversation_id, user_id, user_msg)
        
        # Build Context Arrays
        messages = await self._build_messages(conversation_id, user_id, query, context)
        
        # Stream response back
        full_response = ""
        try:
            async for chunk in self.llm_client.stream_response(messages):
                full_response += chunk
                yield chunk
                
        finally:
            if full_response.strip():
                ai_msg = MessageCreateDto(sender="ai", content=full_response, message_type="text")
                await self.chat_service.add_message(conversation_id, user_id, ai_msg)
