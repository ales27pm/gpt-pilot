"""Client for interacting with a local Ollama server."""

from typing import Any, Optional

import httpx
from ollama import AsyncClient

from core.config import LLMProvider
from core.llm.base import BaseLLMClient
from core.llm.convo import Convo


class OllamaClient(BaseLLMClient):
    """LLM client for the local Ollama server."""

    provider = LLMProvider.OLLAMA

    def _init_client(self) -> None:
        timeout = httpx.Timeout(
            connect=self.config.connect_timeout,
            read=self.config.read_timeout,
        )
        self.client = AsyncClient(
            host=self.config.base_url or "http://localhost:11434",
            timeout=timeout,
        )

    async def _make_request(
        self,
        convo: Convo,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> tuple[str, int, int]:
        """Stream a chat completion from the local Ollama server."""

        kwargs: dict[str, Any] = {}
        if json_mode:
            kwargs["format"] = "json"

        stream = await self.client.chat(
            model=self.config.model,
            messages=convo.messages,
            stream=True,
            options={"temperature": (self.config.temperature if temperature is None else temperature)},
            **kwargs,
        )

        response_chunks: list[str] = []
        async for chunk in stream:
            message = chunk.get("message", {})
            content = message.get("content")
            if not content:
                continue

            response_chunks.append(content)
            if self.stream_handler:
                await self.stream_handler(content)

        if self.stream_handler:
            await self.stream_handler(None)

        full_response = "".join(response_chunks)

        # Ollama currently does not return token usage, so approximate using
        # whitespace tokenization.
        prompt_tokens = sum(len(msg.get("content", "").split()) for msg in convo.messages)
        completion_tokens = len(full_response.split())

        return full_response, prompt_tokens, completion_tokens


__all__ = ["OllamaClient"]
