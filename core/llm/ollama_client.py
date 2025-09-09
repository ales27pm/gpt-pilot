from typing import Optional

from ollama import AsyncClient

from core.config import LLMProvider
from core.llm.base import BaseLLMClient
from core.llm.convo import Convo


class OllamaClient(BaseLLMClient):
    """LLM client for the local Ollama server."""

    provider = LLMProvider.OLLAMA

    def _init_client(self):
        self.client = AsyncClient(host=self.config.base_url or "http://localhost:11434")

    async def _make_request(
        self,
        convo: Convo,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> tuple[str, int, int]:
        stream = await self.client.chat(
            model=self.config.model,
            messages=convo.messages,
            stream=True,
            options={"temperature": self.config.temperature if temperature is None else temperature},
        )
        response = []
        async for chunk in stream:
            message = chunk.get("message", {})
            content = message.get("content")
            if not content:
                continue
            response.append(content)
            if self.stream_handler:
                await self.stream_handler(content)

        if self.stream_handler:
            await self.stream_handler(None)

        return "".join(response), 0, 0


__all__ = ["OllamaClient"]
