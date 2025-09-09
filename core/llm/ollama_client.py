"""Client for interacting with a local Ollama server."""

import importlib.metadata
from typing import Any, Optional

import httpx
from ollama import AsyncClient
from packaging import version

from core.config import LLMProvider
from core.llm.base import BaseLLMClient
from core.llm.convo import Convo

try:  # pragma: no cover - optional dependency
    import tiktoken

    tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - optional dependency
    tokenizer = None  # type: ignore

try:  # pragma: no cover - best effort version detection
    _ollama_version = version.parse(importlib.metadata.version("ollama"))
except Exception:  # pragma: no cover - package metadata missing
    _ollama_version = version.parse("0")

# ``ollama`` 0.3.0+ accepts ``httpx.Timeout`` objects on the client. Older
# releases only allow primitive timeout values. We detect the installed version
# once at import time to pick the correct strategy.
OLLAMA_SUPPORTS_TIMEOUT_OBJECT = _ollama_version >= version.parse("0.3.0")


class OllamaClient(BaseLLMClient):
    """LLM client for the local Ollama server."""

    provider = LLMProvider.OLLAMA

    def _init_client(self) -> None:
        """Initialize the Ollama AsyncClient.

        ``ollama`` has changed its timeout semantics across releases. For
        versions prior to 0.3.0 the client only accepts primitive timeout values
        (floats) and an ``httpx.Timeout`` instance would raise ``TypeError``.
        Newer versions support the richer timeout configuration. We detect the
        installed version at import time and pick the appropriate strategy.
        """

        host = self.config.base_url or "http://localhost:11434"
        if OLLAMA_SUPPORTS_TIMEOUT_OBJECT:
            timeout = httpx.Timeout(
                connect=self.config.connect_timeout,
                read=self.config.read_timeout,
            )
            self.client = AsyncClient(host=host, timeout=timeout)
            self._use_request_timeout = False
        else:
            self.client = AsyncClient(host=host)
            self._use_request_timeout = True

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
            chat_kwargs: dict[str, Any] = {
                "model": self.config.model,
                "messages": convo.messages,
                "stream": True,
                "options": {"temperature": (self.config.temperature if temperature is None else temperature)},
                **kwargs,
            }
            if self._use_request_timeout:
                chat_kwargs["timeout"] = self.config.read_timeout
            try:
                stream = await self.client.chat(**chat_kwargs)
            except TypeError:  # pragma: no cover - very old ollama versions
                chat_kwargs.pop("timeout", None)
                stream = await self.client.chat(**chat_kwargs)

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
