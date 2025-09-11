from dataclasses import asdict
from typing import List

from pydantic import BaseModel, ConfigDict, StrictStr

from core.agents.base import BaseAgent
from core.agents.convo import AgentConvo
from core.agents.response import AgentResponse
from core.llm.parser import JSONParser
from core.log import get_logger
from core.web import BraveSearchError, brave_search

log = get_logger(__name__)


class WebQueries(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    queries: List[StrictStr]


class WebSearch(BaseAgent):
    """Agent responsible for performing web searches for the current task."""

    agent_type = "web-search"
    display_name = "Web search"

    MAX_CONTENT_LENGTH = 2000

    async def run(self) -> AgentResponse:
        if self.current_state.specification.example_project:
            self.next_state.web = []
            return AgentResponse.done(self)

        current_task = self.current_state.current_task or {}
        task_desc = current_task.get("description") or ""
        if not task_desc:
            log.warning("WebSearch: missing task description; skipping web search")
            self.next_state.web = []
            return AgentResponse.done(self)

        llm = self.get_llm(stream_output=False)
        convo = (
            AgentConvo(self)
            .template(
                "create_queries",
                task_description=task_desc,
            )
            .require_schema(WebQueries)
        )
        await self.send_message("Searching the web for relevant information...")
        queries: WebQueries = await llm(convo, parser=JSONParser(WebQueries))

        raw_queries = getattr(queries, "queries", None) or []
        deduped_queries = list(dict.fromkeys([q for q in raw_queries if isinstance(q, str) and q.strip()]))
        if not deduped_queries:
            self.next_state.web = []
            return AgentResponse.done(self)

        results: List[dict] = []
        for q in deduped_queries:
            try:
                search_results = await brave_search(q)
            except BraveSearchError:
                log.warning("Web search failed", exc_info=True)
                continue
            for r in search_results:
                data = asdict(r)
                if len(data.get("content", "")) > self.MAX_CONTENT_LENGTH:
                    data["content"] = data["content"][: self.MAX_CONTENT_LENGTH]
                results.append(data)

        if not results:
            await self.send_message("Web search failed to retrieve any results.")

        self.next_state.web = results
        return AgentResponse.done(self)
