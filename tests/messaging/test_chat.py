import pytest

from core.messaging import Chat, MessageBroker


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {"role": "user", "content": "hi"},
    "hello",
    42,
    [1, 2, 3],
])
async def test_chat_publish_and_receive(payload):
    broker = MessageBroker()
    chat = Chat(broker)
    await chat.publish(payload)
    assert await chat.receive() == payload


@pytest.mark.asyncio
async def test_chat_multiple_subscribers():
    broker = MessageBroker()
    chat1 = Chat(broker)
    chat2 = Chat(broker)
    await chat1.publish("msg")
    assert await chat1.receive() == "msg"
    assert await chat2.receive() == "msg"


@pytest.mark.asyncio
async def test_chat_get_nowait():
    broker = MessageBroker()
    chat = Chat(broker)
    assert await chat.get_nowait() is None
    await chat.publish("msg")
    assert await chat.get_nowait() == "msg"


@pytest.mark.asyncio
async def test_chat_get_nowait_multiple_messages():
    broker = MessageBroker()
    chat = Chat(broker)
    await chat.publish("one")
    await chat.publish("two")
    assert await chat.get_nowait() == "one"
    assert await chat.get_nowait() == "two"
    assert await chat.get_nowait() is None
