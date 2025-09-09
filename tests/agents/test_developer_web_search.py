from unittest.mock import AsyncMock

import pytest

from core.agents.developer import Developer
from core.agents.response import AgentResponse, ResponseType
from core.db.models.specification import Complexity


@pytest.mark.asyncio
async def test_developer_requests_web_search(agentcontext):
    sm, _, ui, _ = agentcontext
    sm.current_state.tasks = [{"description": "Task", "status": "todo"}]
    sm.current_state.docs = []
    sm.current_state.web = None
    sm.current_state.specification.complexity = Complexity.MODERATE
    await sm.commit()

    dev = Developer(sm, ui)
    response = await dev.run()
    assert response.type == ResponseType.WEB_SEARCH_REQUIRED


@pytest.mark.asyncio
async def test_developer_requests_web_search_complex(agentcontext):
    sm, _, ui, _ = agentcontext
    sm.current_state.tasks = [{"description": "Task", "status": "todo"}]
    sm.current_state.docs = []
    sm.current_state.web = None
    sm.current_state.specification.complexity = Complexity.HARD
    await sm.commit()

    dev = Developer(sm, ui)
    response = await dev.run()
    assert response.type == ResponseType.WEB_SEARCH_REQUIRED


@pytest.mark.asyncio
async def test_developer_skips_web_search_simple(agentcontext):
    sm, _, ui, _ = agentcontext
    sm.current_state.tasks = [{"description": "Task", "status": "todo"}]
    sm.current_state.docs = []
    sm.current_state.web = None
    sm.current_state.specification.complexity = Complexity.SIMPLE
    await sm.commit()

    dev = Developer(sm, ui)
    dev.breakdown_current_task = AsyncMock(return_value=AgentResponse.done(dev))
    response = await dev.run()
    assert response.type == ResponseType.DONE


@pytest.mark.asyncio
async def test_developer_skips_when_web_present(agentcontext):
    sm, _, ui, _ = agentcontext
    sm.current_state.tasks = [{"description": "Task", "status": "todo"}]
    sm.current_state.docs = []
    sm.current_state.web = []
    sm.current_state.specification.complexity = Complexity.MODERATE
    await sm.commit()

    dev = Developer(sm, ui)
    dev.breakdown_current_task = AsyncMock(return_value=AgentResponse.done(dev))
    response = await dev.run()
    assert response.type == ResponseType.DONE
