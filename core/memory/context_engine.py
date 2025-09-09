from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import List

from core.memory.shared_memory import SharedMemory


@dataclass
class ContextItem:
    """Represents a piece of context with an associated relevance score."""

    content: str
    agent_type: str
    score: float


class ContextEngine:
    """Advanced context retrieval using pgvector similarity and heuristics."""

    def __init__(self, memory: SharedMemory, decay: float = 0.01):
        self.memory = memory
        self.decay = decay

    async def gather(
        self,
        query_embedding: List[float],
        *,
        agent_type: str | None = None,
        limit: int = 5,
    ) -> List[ContextItem]:
        """Return relevant context items ordered by a composite score.

        The score combines cosine similarity from pgvector with an exponential
        decay factor that prefers more recent entries. Results matching the
        requested agent type receive a small boost.
        """

        records = await self.memory.search_with_scores(query_embedding, limit * 4)
        items: List[ContextItem] = []
        for idx, (rec, dist) in enumerate(records):
            similarity = 1.0 - dist
            recency = exp(-self.decay * idx)
            score = similarity * recency
            if agent_type and rec.agent_type == agent_type:
                score *= 1.1
            items.append(ContextItem(rec.content, rec.agent_type, score))

        items.sort(key=lambda i: i.score, reverse=True)
        return items[:limit]


__all__ = ["ContextEngine", "ContextItem"]
