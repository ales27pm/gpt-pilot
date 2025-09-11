import asyncio

import pytest

from core.messaging import Chat, MessageBroker


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"role": "user", "content": "hi"},
        "hello",
        42,
        [1, 2, 3],
    ],
)
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


# ---------------------------------------------------------------------------
# Additional tests to broaden coverage
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_chat_preserves_message_ordering_fifo():
    broker = MessageBroker()
    chat = Chat(broker)
    msgs = [f"m{i}" for i in range(20)]
    for m in msgs:
        await chat.publish(m)
    received = [await chat.receive() for _ in msgs]
    assert received == msgs


@pytest.mark.asyncio
async def test_chat_accepts_none_and_empty_payloads():
    broker = MessageBroker()
    chat = Chat(broker)

    for payload in [None, "", {}, [], 0, 0.0, False]:
        await chat.publish(payload)
        assert await chat.receive() is payload


@pytest.mark.asyncio
async def test_chat_multiple_messages_interleaved_subscribers_independent_reads():
    broker = MessageBroker()
    a = Chat(broker)
    b = Chat(broker)

    await a.publish("x1")
    await a.publish("x2")

    # Both should see same stream; each maintains its own cursor
    assert await a.receive() == "x1"
    assert await b.receive() == "x1"
    assert await a.receive() == "x2"
    assert await b.receive() == "x2"


@pytest.mark.asyncio
async def test_chat_get_nowait_empty_then_after_publish_then_empty_again():
    broker = MessageBroker()
    chat = Chat(broker)
    assert await chat.get_nowait() is None
    await chat.publish("v")
    assert await chat.get_nowait() == "v"
    assert await chat.get_nowait() is None


@pytest.mark.asyncio
async def test_chat_concurrent_publishers_and_single_consumer():
    broker = MessageBroker()
    chat_pub1 = Chat(broker)
    chat_pub2 = Chat(broker)
    consumer = Chat(broker)

    async def pub(instance, prefix):
        for i in range(10):
            await instance.publish(f"{prefix}{i}")

    await asyncio.gather(pub(chat_pub1, "a"), pub(chat_pub2, "b"))

    # Drain 20 messages; we only assert counts and membership due to concurrency ordering variability
    received = [await consumer.receive() for _ in range(20)]
    assert len(received) == 20
    assert set(received) == {f"a{i}" for i in range(10)} | {f"b{i}" for i in range(10)}


@pytest.mark.asyncio
async def test_chat_mutable_payload_not_copied_reference_semantics():
    broker = MessageBroker()
    chat = Chat(broker)
    payload = {"x": 1, "arr": [1]}
    await chat.publish(payload)
    msg = await chat.receive()
    assert msg is payload
    # Mutating after publish would reflect if references are shared; ensure it is the same object
    payload["x"] = 2
    payload["arr"].append(2)
    assert msg["x"] == 2
    assert msg["arr"] == [1, 2]


@pytest.mark.asyncio
async def test_chat_back_to_back_get_nowait_does_not_block_and_preserves_order():
    broker = MessageBroker()
    chat = Chat(broker)
    for i in range(5):
        await chat.publish(i)
    vals = [await chat.get_nowait() for _ in range(5)]
    assert vals == [0, 1, 2, 3, 4]
    assert await chat.get_nowait() is None


@pytest.mark.asyncio
async def test_chat_receive_can_be_cancelled_without_leaking_tasks():
    broker = MessageBroker()
    chat = Chat(broker)

    async def waiter():
        return await chat.receive()

    task = asyncio.create_task(waiter())
    await asyncio.sleep(0)  # let it start waiting
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Chat should still function after cancellation
    await chat.publish("ok")
    assert await chat.receive() == "ok"


@pytest.mark.asyncio
async def test_each_broker_is_isolated():
    broker1 = MessageBroker()
    broker2 = MessageBroker()
    c1 = Chat(broker1)
    c2 = Chat(broker2)

    await c1.publish("only-1")
    await c2.publish("only-2")

    assert await c1.receive() == "only-1"
    assert await c2.receive() == "only-2"
    # Cross reads should be empty for get_nowait
    assert await c1.get_nowait() is None
    assert await c2.get_nowait() is None


@pytest.mark.asyncio
async def test_chat_large_burst_publish_and_drain():
    broker = MessageBroker()
    chat = Chat(broker)
    total = 200
    for i in range(total):
        await chat.publish(i)
    items = [await chat.receive() for _ in range(total)]
    assert items[0] == 0
    assert items[-1] == total - 1
    assert len(items) == total
    assert await chat.get_nowait() is None


@pytest.mark.asyncio
async def test_chat_type_variety_roundtrip():
    broker = MessageBroker()
    chat = Chat(broker)
    samples = [
        {"nested": {"a": 1}},
        (1, 2, 3),
        {1, 2, 3},
        b"bytes",
        bytearray(b"buf"),
        complex(1, 2),
    ]
    for s in samples:
        await chat.publish(s)
    for s in samples:
        r = await chat.receive()
        # set and bytearray equality semantics hold; bytearray==bytearray compares content
        assert r == s


@pytest.mark.asyncio
async def test_chat_receive_timeout_simulation_using_wait_for():
    broker = MessageBroker()
    chat = Chat(broker)

    async def receive_with_timeout():
        return await asyncio.wait_for(chat.receive(), timeout=0.05)

    with pytest.raises(asyncio.TimeoutError):
        await receive_with_timeout()

    # Works when a message is present
    await chat.publish("ready")
    assert await receive_with_timeout() == "ready"
