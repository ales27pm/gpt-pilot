"""Client for interacting with a local Ollama server."""

from typing import Any, Optional

import httpx
from ollama import AsyncClient

try:  # pragma: no cover - optional dependency
    import tiktoken

    tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - optional dependency
    tokenizer = None  # type: ignore

from core.config import LLMProvider
from core.llm.base import BaseLLMClient
from core.llm.convo import Convo


class OllamaClient(BaseLLMClient):
    """LLM client for the local Ollama server."""

    provider = LLMProvider.OLLAMA

    def _init_client(self) -> None:
        """Initialize the Ollama AsyncClient.

        Older versions of ``ollama`` only accept primitive timeout values on the
        client. Passing an ``httpx.Timeout`` instance can raise ``TypeError`` at
        runtime, so we avoid setting timeouts here and instead specify them per
        request for maximum compatibility.
        """

        self.client = AsyncClient(
            host=self.config.base_url or "http://localhost:11434",
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

        response_chunks: list[str] = []
        try:
            request_timeout = self.config.read_timeout
            try:
                stream = await self.client.chat(
                    model=self.config.model,
                    messages=convo.messages,
                    stream=True,
                    options={"temperature": (self.config.temperature if temperature is None else temperature)},
                    timeout=request_timeout,
                    **kwargs,
                )
            except TypeError:  # pragma: no cover - older ollama versions
                # ``timeout`` is not supported; retry without it.
                stream = await self.client.chat(
                    model=self.config.model,
                    messages=convo.messages,
                    stream=True,
                    options={"temperature": (self.config.temperature if temperature is None else temperature)},
                    **kwargs,
                )

            async for chunk in stream:
                message = chunk.get("message", {})
                content = message.get("content")
                if not content:
                    continue

                response_chunks.append(content)
                if self.stream_handler:
                    await self.stream_handler(content)
        except httpx.HTTPError:
            # Propagate connection/timeout errors to caller
            raise
        finally:
            if self.stream_handler:
                await self.stream_handler(None)

        full_response = "".join(response_chunks)

        def _count_tokens(text: str) -> int:
            if tokenizer is None:
                return len(text.split())
            return len(tokenizer.encode(text))

        prompt_tokens = sum(_count_tokens(msg.get("content", "")) for msg in convo.messages)
        completion_tokens = _count_tokens(full_response)

        return full_response, prompt_tokens, completion_tokens


__all__ = ["OllamaClient"]
