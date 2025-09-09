from unittest.mock import AsyncMock, patch

import pytest
from httpx import HTTPError

from core.agents.external_docs import DocQueries, ExternalDocumentation, SelectedDocsets


@pytest.mark.asyncio
async def test_stores_documentation_snippets_for_task(agentcontext):
    sm, _, ui, mock_llm = agentcontext

    sm.current_state.tasks = [{"description": "Some VueJS task", "status": "todo"}]
    await sm.commit()

    with patch.object(
        ExternalDocumentation,
        "_get_available_docsets",
        AsyncMock(return_value=[("vuejs-api-ref", "VueJS API Reference")]),
    ), patch.object(
        ExternalDocumentation,
        "_fetch_snippets",
        AsyncMock(return_value=[("vuejs-api-ref", ["snippet"])]),
    ):
        ed = ExternalDocumentation(sm, ui)
        ed.get_llm = mock_llm(
            side_effect=[
                SelectedDocsets(docsets=["vuejs-api-ref"]),
                DocQueries(queries=["VueJS component model"]),
            ]
        )
        await ed.run()

    assert ed.next_state.docs[0]["key"] == "vuejs-api-ref"


@pytest.mark.asyncio
async def test_continues_without_docs_for_invalid_docset(agentcontext):
    sm, _, ui, mock_llm = agentcontext

    sm.current_state.tasks = [{"description": "Some VueJS task", "status": "todo"}]
    await sm.commit()

    ed = ExternalDocumentation(sm, ui)
    ed.get_llm = mock_llm(
        side_effect=[SelectedDocsets(docsets=["doesnt-exist"]), DocQueries(queries=["VueJS component model"])]
    )
    await ed.run()
    assert ed.next_state.docs == []


@pytest.mark.asyncio
async def test_continues_without_docs_if_api_is_down(agentcontext):
    sm, _, ui, _ = agentcontext

    sm.current_state.tasks = [{"description": "Future Task", "status": "todo"}]
    await sm.commit()

    ed = ExternalDocumentation(sm, ui)
    with patch("httpx.Client.get", side_effect=HTTPError("Failed")):
        await ed.run()

    assert ed.next_state.docs == []
