from __future__ import annotations

from typing import List, Tuple

import sqlalchemy as sa
from sqlalchemy import select

from core.db.models.shared_memory import SharedMemory as SharedMemoryModel
from core.db.session import SessionManager


class SharedMemory:
    """Vector-based shared memory accessible to all agents."""

    def __init__(self, session_manager: SessionManager, embedding_dim: int = 1536):
        self.session_manager = session_manager
        self.embedding_dim = embedding_dim

    @property
    def enabled(self) -> bool:
        # Search requires pgvector; storage works with JSON fallback
        return True

    def _validate_embedding(self, embedding: List[float]):
        if len(embedding) != self.embedding_dim:
            raise ValueError(f"Embedding length must be {self.embedding_dim}, got {len(embedding)}")

    async def add(self, agent_type: str, content: str, embedding: List[float]):
        self._validate_embedding(embedding)
        async with self.session_manager as session:
            record = SharedMemoryModel(agent_type=agent_type, content=content, embedding=embedding)
            session.add(record)
            await session.commit()
            return record

    async def search_with_scores(self, embedding: List[float], limit: int = 5) -> List[Tuple[SharedMemoryModel, float]]:
        """Return records with their cosine distances for advanced scoring."""

        self._validate_embedding(embedding)
        async with self.session_manager as session:
            try:
                dialect = self.session_manager.engine.dialect.name
            except Exception:
                dialect = ""
            embedding_col = SharedMemoryModel.embedding
            if hasattr(embedding_col, "cosine_distance") and dialect == "postgresql":
                stmt = (
                    select(SharedMemoryModel, embedding_col.cosine_distance(embedding).label("dist"))
                    .order_by("dist")
                    .limit(limit)
                )
            else:
                stmt = (
                    select(SharedMemoryModel, sa.literal(1.0).label("dist"))
                    .order_by(SharedMemoryModel.id.desc())
                    .limit(limit)
                )
            result = await session.execute(stmt)
            return [(row[0], float(row[1])) for row in result]

    async def search(self, embedding: List[float], limit: int = 5) -> List[SharedMemoryModel]:
        results = await self.search_with_scores(embedding, limit)
        return [record for record, _ in results]
