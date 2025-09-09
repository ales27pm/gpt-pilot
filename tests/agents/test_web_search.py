from unittest.mock import patch

import pytest

from core.agents.web_search import WebQueries, WebSearch
from core.web import BraveSearchError, WebResult


@patch("core.agents.web_search.brave_search")
@pytest.mark.asyncio
async def test_web_search_stores_results(mock_search, agentcontext):
    sm, _, ui, mock_llm = agentcontext

    sm.current_state.tasks = [{"description": "Some task", "status": "todo"}]
    await sm.commit()

    mock_llm_return = WebQueries(queries=["test query"])
    ws = WebSearch(sm, ui)
    ws.get_llm = mock_llm(return_value=mock_llm_return)
    mock_search.return_value = [
        WebResult(url="http://example.com", title="Example", snippet="snippet", content="content")
    ]

    await ws.run()
    assert ws.next_state.web[0]["url"] == "http://example.com"


@patch("core.agents.web_search.brave_search")
@pytest.mark.asyncio
async def test_web_search_handles_errors(mock_search, agentcontext):
    sm, _, ui, mock_llm = agentcontext
    sm.current_state.tasks = [{"description": "task", "status": "todo"}]
    await sm.commit()

    ws = WebSearch(sm, ui)
    ws.get_llm = mock_llm(return_value=WebQueries(queries=["q"]))
    mock_search.side_effect = BraveSearchError("fail")

    await ws.run()
    assert ws.next_state.web == []
