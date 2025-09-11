import pytest

from core.messaging import Chat, MessageBroker


@pytest.mark.asyncio
async def test_chat_publish_and_receive():
    broker = MessageBroker()
    chat = Chat(broker)
    await chat.publish({"role": "user", "content": "hi"})
    message = await chat.receive()
    assert message == {"role": "user", "content": "hi"}


@pytest.mark.asyncio
async def test_chat_get_nowait():
    broker = MessageBroker()
    chat = Chat(broker)
    assert await chat.get_nowait() is None
    await chat.publish("msg")
    assert await chat.get_nowait() == "msg"
