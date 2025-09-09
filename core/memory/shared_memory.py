from __future__ import annotations

from typing import List

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
            raise ValueError(
                f"Embedding length must be {self.embedding_dim}, got {len(embedding)}"
            )

    async def add(self, agent_type: str, content: str, embedding: List[float]):
        self._validate_embedding(embedding)
        async with self.session_manager as session:
            record = SharedMemoryModel(
                agent_type=agent_type, content=content, embedding=embedding
            )
            session.add(record)
            await session.commit()
            return record

    async def search(self, embedding: List[float], limit: int = 5) -> List[SharedMemoryModel]:
        self._validate_embedding(embedding)
        async with self.session_manager as session:
            # Prefer engine dialect detection to avoid None bind on async sessions
            try:
                dialect = self.session_manager.engine.dialect.name
            except Exception:
                dialect = ""
            # Detect pgvector by attribute presence on the column expression
            embedding_col = SharedMemoryModel.embedding
            if hasattr(embedding_col, "cosine_distance") and dialect == "postgresql":
                stmt = (
                    select(SharedMemoryModel)
                    .order_by(embedding_col.cosine_distance(embedding))
                    .limit(limit)
                )
            else:
                stmt = select(SharedMemoryModel).order_by(SharedMemoryModel.id.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars())
