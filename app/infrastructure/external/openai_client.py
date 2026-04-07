import logging
from typing import AsyncGenerator, Dict, List, Any

from openai import AsyncOpenAI

from app.config import settings
from app.domain.interfaces.llm_client import ILLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(ILLMClient):
    """Concrete implementation of ILLMClient utilizing native OpenAI endpoints."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def generate_response(
        self, messages: List[Dict[str, Any]], temperature: float = None, max_tokens: int = None
    ) -> str:
        temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.OPENAI_MAX_TOKENS
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI Client Error (generate): {str(e)}", exc_info=True)
            # Default fallback message if network is down or quota hit, ensuring app doesnt violently crash
            return "I'm currently unable to connect to my intelligence servers. Please try again later."

    async def stream_response(
        self, messages: List[Dict[str, Any]], temperature: float = None, max_tokens: int = None
    ) -> AsyncGenerator[str, None]:
        temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.OPENAI_MAX_TOKENS
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content is not None:
                    yield content
        except Exception as e:
            logger.error(f"OpenAI Client Error (stream): {str(e)}", exc_info=True)
            yield "[Connection Interrupted. Please try again later.]"
