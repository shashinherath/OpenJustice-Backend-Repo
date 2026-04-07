import logging
from typing import AsyncGenerator, Dict, List, Any
from uuid import UUID

from app.application.dtos.chat_dto import MessageCreateDto
from app.application.services.chat_service import ChatService
from app.application.services.rag_service import RAGService
from app.domain.interfaces.llm_client import ILLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are OpenJustice, a highly capable and intelligent AI legal assistant specializing in providing precise, helpful, and highly accurate answers regarding the legal system.
Use the provided local legal context to answer the user's question securely. Provide clear, well-structured, and easily readable answers. If you don't know the answer or if the context doesn't exist, admit that you don't know instead of making things up.
"""

class LLMService:
    """Orchestrates interactions between the Chat history, RAG vectors, and Language Models."""

    def __init__(self, chat_service: ChatService, rag_service: RAGService, llm_client: ILLMClient):
        self.chat_service = chat_service
        self.rag_service = rag_service
        self.llm_client = llm_client

    async def _build_messages(self, conversation_id: UUID, user_id: UUID, query: str) -> List[Dict[str, Any]]:
        """Constructs the full system-history-context message array for LLMs."""
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # 1. Fetch recent conversation history limit to last 15 messages to save context windows
        history = await self.chat_service.get_messages(conversation_id, user_id, skip=0, limit=15)
        
        for msg in sorted(history, key=lambda x: x.created_at):
            # Skip the specific query we are answering if it's already in history
            if msg.content == query:
                continue
            role = "user" if msg.sender == "user" else "assistant"
            messages.append({"role": role, "content": msg.content})

        # 2. Extract RAG Context for this new query
        context = await self.rag_service.retrieve_context(query)
        
        # 3. Add Context and Final prompt
        final_prompt = query
        if context:
            final_prompt = f"LOCAL LEGAL CONTEXT:\n{context}\n\nUSER QUERY:\n{query}"
            
        messages.append({"role": "user", "content": final_prompt})
        
        return messages

    async def generate_response(self, conversation_id: UUID, user_id: UUID, query: str, message_type: str = "text") -> str:
        """Synchronously block, execute RAG, ask LLM, and save response to database."""
        
        # Save User Message First
        user_msg = MessageCreateDto(sender="user", content=query, message_type=message_type)
        await self.chat_service.add_message(conversation_id, user_id, user_msg)
        
        # Build Context Arrays
        messages = await self._build_messages(conversation_id, user_id, query)
        
        # Execute LLM Call natively
        response = await self.llm_client.generate_response(messages)
        
        # Save AI Message
        ai_msg = MessageCreateDto(sender="ai", content=response, message_type="text")
        await self.chat_service.add_message(conversation_id, user_id, ai_msg)
        
        return response

    async def stream_response(self, conversation_id: UUID, user_id: UUID, query: str, message_type: str = "text") -> AsyncGenerator[str, None]:
        """Provides an asynchronous Generator directly streaming the underlying LLM's response block."""
        
        # Save User Message First
        user_msg = MessageCreateDto(sender="user", content=query, message_type=message_type)
        await self.chat_service.add_message(conversation_id, user_id, user_msg)
        
        # Build Context Arrays
        messages = await self._build_messages(conversation_id, user_id, query)
        
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
