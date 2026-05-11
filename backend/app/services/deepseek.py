from typing import Optional, Type, TypeVar
import httpx
from pydantic import BaseModel
import json
from app.core.config import get_settings

T = TypeVar("T", bound=BaseModel)


class DeepSeekServiceError(Exception):
    """Raised when DeepSeek API returns an error or malformed response."""

    pass


settings = get_settings()


class DeepSeekService:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = "deepseek-chat"

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send chat completion request to DeepSeek API."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def structured_chat(
        self,
        messages: list[dict],
        response_model: Type[T],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> T:
        """Send chat completion request with structured output."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as e:
                raise DeepSeekServiceError(
                    f"Failed to parse DeepSeek response as JSON: {e}"
                ) from e
            return response_model.model_validate(parsed)

    async def count_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text) // 4


deepseek_service = DeepSeekService()