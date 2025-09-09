from __future__ import annotations

from typing import List, Union
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

try:  # pragma: no cover - optional dependency
    from pgvector.sqlalchemy import Vector as PGVector  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    PGVector = None  # type: ignore


def _dialect_name() -> str:
    try:
        bind = Base.metadata.bind
        return sa.inspect(bind).dialect.name if bind is not None else ""
    except Exception:  # pragma: no cover - engine not yet bound
        return ""


from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# Always use string UUIDs at ORM level to avoid premature dialect binding issues.
_ID_TYPE = String(36)
_ID_DEFAULT = lambda: str(uuid4())

# Store embeddings in JSON at ORM level; pgvector specifics handled in migrations.
Vector = None  # type: ignore
_EMBEDDING_TYPE = JSON


class SharedMemory(Base):
    """Shared memory record stored in PostgreSQL with pgvector support."""

    __tablename__ = "shared_memory"

    id: Mapped[Union[UUID, str]] = mapped_column(
        _ID_TYPE, primary_key=True, default=_ID_DEFAULT
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(_EMBEDDING_TYPE)

