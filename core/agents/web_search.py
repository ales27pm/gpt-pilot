from dataclasses import asdict
from typing import List

from pydantic import BaseModel

from core.agents.base import BaseAgent
from core.agents.convo import AgentConvo
from core.agents.response import AgentResponse
from core.llm.parser import JSONParser
from core.log import get_logger
from core.web import BraveSearchError, brave_search

log = get_logger(__name__)


class WebQueries(BaseModel):
    queries: List[str]


class WebSearch(BaseAgent):
    """Agent responsible for performing web searches for the current task."""

    agent_type = "web-search"
    display_name = "Web search"

    async def run(self) -> AgentResponse:
        if self.current_state.specification.example_project:
            self.next_state.web = []
            return AgentResponse.done(self)

        current_task = self.current_state.current_task
        llm = self.get_llm(stream_output=False)
        convo = (
            AgentConvo(self)
            .template(
                "create_queries",
                task_description=current_task["description"],
            )
            .require_schema(WebQueries)
        )
        await self.send_message("Searching the web for relevant information...")
        queries: WebQueries = await llm(convo, parser=JSONParser(WebQueries))

        results: List[dict] = []
        for q in queries.queries:
            try:
                search_results = await brave_search(q)
            except BraveSearchError:
                log.warning("Web search failed", exc_info=True)
                continue
            results.extend(asdict(r) for r in search_results)

        self.next_state.web = results
        return AgentResponse.done(self)
