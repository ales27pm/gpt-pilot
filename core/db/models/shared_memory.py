from __future__ import annotations

from typing import List
from uuid import uuid4

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover - optional dependency
    Vector = None  # type: ignore


class SharedMemory(Base):
    """Shared memory record stored in PostgreSQL with pgvector support."""

    __tablename__ = "shared_memory"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    if Vector is not None:  # pragma: no cover - depends on pgvector
        embedding: Mapped[List[float]] = mapped_column(Vector(1536))  # type: ignore[arg-type]
    else:
        from sqlalchemy import JSON

        embedding: Mapped[List[float]] = mapped_column(JSON)
