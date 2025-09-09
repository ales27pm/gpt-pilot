import pytest

from core.agents.developer import Developer
from core.agents.response import ResponseType
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
