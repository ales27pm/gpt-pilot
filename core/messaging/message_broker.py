from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, DefaultDict


class MessageBroker:
    """A simple asynchronous message broker.

    The broker provides topic based publish/subscribe semantics using
    ``asyncio.Queue``. It can be used by agents to exchange messages without
    directly depending on each other.
    """

    def __init__(self) -> None:
        self._queues: DefaultDict[str, asyncio.Queue[Any]] = defaultdict(asyncio.Queue)

    async def publish(self, topic: str, message: Any) -> None:
        """Publish ``message`` to ``topic``."""
        await self._queues[topic].put(message)

    def subscribe(self, topic: str) -> asyncio.Queue[Any]:
        """Return a queue for consuming messages from ``topic``."""
        return self._queues[topic]

    async def get(self, topic: str) -> Any:
        """Get the next message for ``topic``."""
        return await self._queues[topic].get()
