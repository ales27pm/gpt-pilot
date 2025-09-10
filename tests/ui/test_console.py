import inspect
from unittest.mock import AsyncMock, patch

import pytest

from core.ui.base import AgentSource, UIClosedError
from core.ui.console import PlainConsoleUI


@pytest.mark.asyncio
async def test_send_message(capsys):
    src = AgentSource("Product Owner", "product-owner")
    ui = PlainConsoleUI()

    connected = await ui.start()
    assert connected is True
    await ui.send_message("Hello from the other side ♫", source=src)

    captured = capsys.readouterr()
    assert captured.out == "[Product Owner] Hello from the other side ♫\n"
    await ui.stop()


@pytest.mark.asyncio
async def test_stream(capsys):
    src = AgentSource("Product Owner", "product-owner")
    ui = PlainConsoleUI()

    await ui.start()
    for word in ["Hellø ", "fröm ", "the ", "other ", "šide ", "♫"]:
        await ui.send_stream_chunk(word, source=src)

    captured = capsys.readouterr()
    assert captured.out == "Hellø fröm the other šide ♫"
    await ui.stop()


@pytest.mark.asyncio
@patch("core.ui.console.PromptSession")
async def test_ask_question_simple(mock_PromptSession):
    prompt_async = mock_PromptSession.return_value.prompt_async = AsyncMock(return_value="awesome")
    ui = PlainConsoleUI()

    await ui.start()
    input = await ui.ask_question("Hello, how are you?")

    assert input.cancelled is False
    assert input.button is None
    assert input.text == "awesome"

    await ui.stop()

    prompt_async.assert_awaited_once()


@pytest.mark.asyncio
@patch("core.ui.console.PromptSession")
async def test_ask_question_with_buttons(mock_PromptSession):
    prompt_async = mock_PromptSession.return_value.prompt_async = AsyncMock(return_value="yes")
    ui = PlainConsoleUI()

    await ui.start()
    input = await ui.ask_question(
        "Are you sure?",
        buttons={"yes": "Yes, I'm sure", "no": "No, cancel"},
    )

    assert input.cancelled is False
    assert input.button == "yes"
    assert input.text is None

    await ui.stop()

    prompt_async.assert_awaited_once()


@pytest.mark.asyncio
@patch("core.ui.console.PromptSession")
async def test_ask_question_interrupted(mock_PromptSession):
    prompt_async = mock_PromptSession.return_value.prompt_async = AsyncMock(side_effect=KeyboardInterrupt)
    ui = PlainConsoleUI()

    await ui.start()
    with pytest.raises(UIClosedError):
        await ui.ask_question("Hello, how are you?")

    await ui.stop()

    prompt_async.assert_awaited_once()


@pytest.mark.asyncio
@patch("core.ui.console.PromptSession")
async def test_ask_question_with_hint_and_placeholder(mock_PromptSession, capsys):
    async def fake_prompt_async(*, default="", placeholder=None):
        return "hello"

    prompt_async = mock_PromptSession.return_value.prompt_async = AsyncMock(return_value="hello")
    prompt_async.__signature__ = inspect.signature(fake_prompt_async)
    ui = PlainConsoleUI()

    await ui.start()
    await ui.ask_question("Say something", hint="be polite", placeholder="type here")

    await ui.stop()

    prompt_async.assert_awaited_once_with(default="", placeholder="type here")
    captured = capsys.readouterr()
    assert captured.out == "Say something\nHint: be polite\n"


@pytest.mark.asyncio
@patch("core.ui.console.PromptSession")
async def test_ask_question_with_none_hint_and_placeholder(mock_PromptSession, capsys):
    async def fake_prompt_async(*, default="", placeholder=None):
        return "hello"

    prompt_async = mock_PromptSession.return_value.prompt_async = AsyncMock(return_value="hello")
    prompt_async.__signature__ = inspect.signature(fake_prompt_async)
    ui = PlainConsoleUI()

    await ui.start()
    await ui.ask_question("Say something", hint=None, placeholder=None)
    await ui.stop()

    # Ensure prompt was awaited and called with default placeholder handling
    prompt_async.assert_awaited_once()
    kwargs = prompt_async.await_args.kwargs
    assert kwargs.get("default") == ""
    # placeholder may not be supported or may be omitted for compatibility
    assert ("placeholder" not in kwargs) or (kwargs["placeholder"] is None)

    captured = capsys.readouterr()
    assert captured.out == "Say something\n"


@pytest.mark.asyncio
@patch("core.ui.console.PromptSession")
async def test_ask_question_with_empty_hint_and_placeholder(mock_PromptSession, capsys):
    async def fake_prompt_async(*, default="", placeholder=None):
        return "hello"

    prompt_async = mock_PromptSession.return_value.prompt_async = AsyncMock(return_value="hello")
    prompt_async.__signature__ = inspect.signature(fake_prompt_async)
    ui = PlainConsoleUI()

    await ui.start()
    await ui.ask_question("Say something", hint="", placeholder="")
    await ui.stop()

    prompt_async.assert_awaited_once_with(default="", placeholder="")
    captured = capsys.readouterr()
    assert captured.out == "Say something\n"


@pytest.mark.asyncio
@patch("core.ui.console.PromptSession")
async def test_ask_question_with_hint_and_buttons(mock_PromptSession, capsys):
    async def fake_prompt_async(*, default="", placeholder=None):
        return "yes"

    prompt_async = mock_PromptSession.return_value.prompt_async = AsyncMock(return_value="yes")
    prompt_async.__signature__ = inspect.signature(fake_prompt_async)
    ui = PlainConsoleUI()

    await ui.start()
    buttons = {"yes": "Yes", "no": "No"}
    await ui.ask_question(
        "Confirm?",
        buttons=buttons,
        hint="choose wisely",
        default="yes",
    )
    await ui.stop()

    prompt_async.assert_awaited_once_with(default="", placeholder=None)
    captured = capsys.readouterr()
    assert captured.out == "Confirm?\nHint: choose wisely\n  [yes]: Yes (default)\n  [no]: No\n"


@pytest.mark.asyncio
@patch("core.ui.console.PromptSession")
async def test_ask_question_non_verbose(mock_PromptSession, capsys):
    async def fake_prompt_async(*, default="", placeholder=None):
        return "ignored"

    prompt_async = mock_PromptSession.return_value.prompt_async = AsyncMock(return_value="ignored")
    prompt_async.__signature__ = inspect.signature(fake_prompt_async)
    ui = PlainConsoleUI()

    await ui.start()
    await ui.ask_question("Should not print", verbose=False)

    await ui.stop()

    prompt_async.assert_awaited_once_with(default="", placeholder=None)
    captured = capsys.readouterr()
    assert captured.out == ""


@pytest.mark.asyncio
@patch("core.ui.console.PromptSession")
async def test_ask_question_buttons_only_verbose_shows_message(mock_PromptSession, capsys):
    prompt_async = mock_PromptSession.return_value.prompt_async = AsyncMock(side_effect=["maybe", "yes"])
    ui = PlainConsoleUI()

    await ui.start()
    buttons = {"yes": "Yes", "no": "No"}
    await ui.ask_question("Confirm?", buttons=buttons, buttons_only=True)
    await ui.stop()

    assert prompt_async.await_count == 2
    captured = capsys.readouterr()
    assert captured.out == "Confirm?\n  [yes]: Yes\n  [no]: No\nPlease choose one of available options\n"


@pytest.mark.asyncio
@patch("core.ui.console.PromptSession")
async def test_ask_question_buttons_only_non_verbose_silent(mock_PromptSession, capsys):
    prompt_async = mock_PromptSession.return_value.prompt_async = AsyncMock(side_effect=["maybe", "yes"])
    ui = PlainConsoleUI()

    await ui.start()
    buttons = {"yes": "Yes", "no": "No"}
    await ui.ask_question("Confirm?", buttons=buttons, buttons_only=True, verbose=False)
    await ui.stop()

    assert prompt_async.await_count == 2
    captured = capsys.readouterr()
    assert captured.out == ""
