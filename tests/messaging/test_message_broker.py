import asyncio

import pytest

from core.messaging import MessageBroker


@pytest.mark.asyncio
async def test_publish_and_get():
    broker = MessageBroker()
    await broker.publish("topic", {"value": 1})
    message = await asyncio.wait_for(broker.get("topic"), timeout=1)
    assert message == {"value": 1}
