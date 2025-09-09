from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, DefaultDict


class MessageBroker:
    """A simple asynchronous message broker.

    The broker provides topic based publish/subscribe semantics using
    ``asyncio.Queue``. Each subscriber receives its own queue so that every
    subscriber gets every published message. Queues have a configurable
    ``maxsize`` to avoid unbounded growth when subscribers are slow or
    unavailable.
    """

    def __init__(self, maxsize: int = 1000) -> None:
        self._maxsize = maxsize
        self._queues: DefaultDict[str, list[asyncio.Queue[Any]]] = defaultdict(list)

    async def publish(self, topic: str, message: Any) -> None:
        """Publish ``message`` to all subscribers of ``topic``."""
        for queue in self._queues[topic]:
            await queue.put(message)

    def subscribe(self, topic: str) -> asyncio.Queue[Any]:
        """Create and return a new queue for consuming messages from ``topic``."""
        queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=self._maxsize)
        self._queues[topic].append(queue)
        return queue

    async def get(self, queue: asyncio.Queue[Any]) -> Any:
        """Get the next message from the subscriber's ``queue``."""
        return await queue.get()

    def queue_length(self, queue: asyncio.Queue[Any]) -> int:
        """Return the current length of ``queue``."""
        return queue.qsize()
