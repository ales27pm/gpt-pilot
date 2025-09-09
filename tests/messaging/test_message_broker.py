import asyncio

import pytest

from core.messaging import MessageBroker


@pytest.mark.asyncio
async def test_publish_and_get():
    broker = MessageBroker()
    queue = broker.subscribe("topic")
    await broker.publish("topic", {"value": 1})
    message = await asyncio.wait_for(broker.get(queue), timeout=1)
    assert message == {"value": 1}


@pytest.mark.asyncio
async def test_multiple_subscribers_receive_same_message():
    broker = MessageBroker()
    queue1 = broker.subscribe("topic")
    queue2 = broker.subscribe("topic")
    await broker.publish("topic", {"value": 1})
    msg1 = await asyncio.wait_for(broker.get(queue1), timeout=1)
    msg2 = await asyncio.wait_for(broker.get(queue2), timeout=1)
    assert msg1 == {"value": 1}
    assert msg2 == {"value": 1}


@pytest.mark.asyncio
async def test_multiple_topics_are_isolated():
    broker = MessageBroker()
    queue_a = broker.subscribe("a")
    queue_b = broker.subscribe("b")
    await broker.publish("a", {"topic": "a"})
    await broker.publish("b", {"topic": "b"})
    msg_a = await asyncio.wait_for(broker.get(queue_a), timeout=1)
    msg_b = await asyncio.wait_for(broker.get(queue_b), timeout=1)
    assert msg_a == {"topic": "a"}
    assert msg_b == {"topic": "b"}


@pytest.mark.asyncio
async def test_unsubscribe_stops_receiving_messages():
    broker = MessageBroker()
    queue = broker.subscribe("topic")
    broker.unsubscribe("topic", queue)
    await broker.publish("topic", {"value": 1})
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(broker.get(queue), timeout=0.1)
