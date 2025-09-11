from __future__ import annotations

import asyncio
from typing import Any, Optional

from .message_broker import MessageBroker


class Chat:
    """Lightweight chat channel backed by :class:`MessageBroker`.

    The class provides a tiny abstraction over a broker topic so that agents
    and the orchestrator can exchange chat style messages without depending on
    a concrete transport.  Messages are published to a single topic and every
    instance maintains its own subscription queue.
    """

    def __init__(self, broker: MessageBroker, topic: str = "chat") -> None:
        self._broker = broker
        self._topic = topic
        self._queue: asyncio.Queue[Any] = broker.subscribe(topic)

    async def publish(self, message: Any) -> None:
        """Publish ``message`` to the chat topic."""
        await self._broker.publish(self._topic, message)

    async def receive(self) -> Any:
        """Wait for and return the next chat message."""
        return await self._broker.get(self._queue)

    async def get_nowait(self) -> Optional[Any]:
        """Return the next message if available, otherwise ``None``."""
        if self._broker.queue_length(self._queue):
            return await self.receive()
        return None
