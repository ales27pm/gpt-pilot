from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, DefaultDict

from core.log import get_logger


PUBLISH_PUT_TIMEOUT = 0.5  # seconds


class MessageBroker:
    """A simple asynchronous message broker.

    The broker provides topic based publish/subscribe semantics using
    ``asyncio.Queue``. Each subscriber receives its own queue so that every
    subscriber gets every published message. Queues have a configurable
    ``maxsize`` to avoid unbounded growth when subscribers are slow or
    unavailable. Subscribers can be removed with :meth:`unsubscribe`.
    """

    def __init__(self, maxsize: int = 1000, publish_put_timeout: float = PUBLISH_PUT_TIMEOUT) -> None:
        self._maxsize = maxsize
        self._publish_put_timeout = publish_put_timeout
        self._queues: DefaultDict[str, list[asyncio.Queue[Any]]] = defaultdict(list)
        self._logger = get_logger(__name__)

    async def publish(self, topic: str, message: Any) -> None:
        """Publish ``message`` to all subscribers of ``topic``."""
        for queue in self._queues[topic]:
            try:
                await asyncio.wait_for(queue.put(message), timeout=self._publish_put_timeout)
            except asyncio.TimeoutError:
                self._logger.warning("dropping message on topic %s: slow consumer", topic)

    def subscribe(self, topic: str) -> asyncio.Queue[Any]:
        """Create and return a new bounded queue for ``topic`` messages."""
        queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=self._maxsize)
        self._queues[topic].append(queue)
        return queue

    def unsubscribe(self, topic: str, queue: asyncio.Queue[Any]) -> None:
        """Remove ``queue`` from ``topic``'s subscribers."""
        try:
            self._queues[topic].remove(queue)
            if not self._queues[topic]:
                del self._queues[topic]
        except (KeyError, ValueError):
            pass

    async def get(self, queue: asyncio.Queue[Any]) -> Any:
        """Get the next message from the subscriber's ``queue``."""
        return await queue.get()

    def queue_length(self, queue: asyncio.Queue[Any]) -> int:
        """Return the current length of ``queue``."""
        return queue.qsize()
