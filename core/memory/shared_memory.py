from __future__ import annotations

from typing import List

from sqlalchemy import select

from core.db.models.shared_memory import SharedMemory as SharedMemoryModel, Vector
from core.db.session import SessionManager


class SharedMemory:
    """Vector-based shared memory accessible to all agents."""

    def __init__(self, session_manager: SessionManager, embedding_dim: int = 1536):
        self.session_manager = session_manager
        self.embedding_dim = embedding_dim

    @property
    def enabled(self) -> bool:
        return Vector is not None

    async def add(self, agent_type: str, content: str, embedding: List[float]):
        if not self.enabled:
            raise RuntimeError("pgvector is not available")
        if len(embedding) != self.embedding_dim:
            raise ValueError(
                f"Embedding length must be {self.embedding_dim}, got {len(embedding)}"
            )
        async with self.session_manager as session:
            record = SharedMemoryModel(
                agent_type=agent_type, content=content, embedding=embedding
            )
            session.add(record)
            await session.commit()
            return record

    async def search(self, embedding: List[float], limit: int = 5) -> List[SharedMemoryModel]:
        if not self.enabled:
            raise RuntimeError("pgvector is not available")
        if len(embedding) != self.embedding_dim:
            raise ValueError(
                f"Input embedding length {len(embedding)} does not match expected length {self.embedding_dim}"
            )
        stmt = (
            select(SharedMemoryModel)
            .order_by(SharedMemoryModel.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        async with self.session_manager as session:
            result = await session.execute(stmt)
            return list(result.scalars())
