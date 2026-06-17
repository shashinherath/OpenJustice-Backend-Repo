import logging
from typing import AsyncGenerator, Dict, List, Any, Optional

from openai import AsyncOpenAI

from app.config import settings
from app.domain.interfaces.llm_client import ILLMClient

logger = logging.getLogger(__name__)


from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository

class OpenAIClient(ILLMClient):
    """Concrete implementation of ILLMClient utilizing native OpenAI endpoints."""

    def __init__(self, system_settings_repository: SystemSettingsRepository = None):
        self.system_settings_repository = system_settings_repository
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.current_api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL

    async def _ensure_client(self):
        if self.system_settings_repository:
            sys_settings = await self.system_settings_repository.get_settings()
            db_key = sys_settings.openai_api_key
            if db_key and db_key != self.current_api_key:
                self.current_api_key = db_key
                self.client = AsyncOpenAI(api_key=self.current_api_key)

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        model: Optional[str] = None
    ) -> str:
        temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.OPENAI_MAX_TOKENS
        active_model = model if model else self.model
        top_p = top_p if top_p is not None else 1.0
        frequency_penalty = frequency_penalty if frequency_penalty is not None else 0.0
        
        await self._ensure_client()
        
        try:
            response = await self.client.chat.completions.create(
                model=active_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                stream=False
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI Client Error (generate): {str(e)}", exc_info=True)
            # Default fallback message if network is down or quota hit, ensuring app doesnt violently crash
            return "I'm currently unable to connect to my intelligence servers. Please try again later."

    async def stream_response(
        self,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.OPENAI_MAX_TOKENS
        active_model = model if model else self.model
        top_p = top_p if top_p is not None else 1.0
        frequency_penalty = frequency_penalty if frequency_penalty is not None else 0.0
        
        await self._ensure_client()
        
        try:
            stream = await self.client.chat.completions.create(
                model=active_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content is not None:
                    yield content
        except Exception as e:
            logger.error(f"OpenAI Client Error (stream): {str(e)}", exc_info=True)
            yield "[Connection Interrupted. Please try again later.]"
