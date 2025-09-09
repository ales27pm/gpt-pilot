from __future__ import annotations

from typing import List
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import JSON, String, Text
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


# Always use string UUIDs at ORM level to avoid premature dialect binding issues.
_ID_TYPE = String(36)


def _generate_id() -> str:
    """Return a random UUID4 string."""
    return str(uuid4())


_ID_DEFAULT = _generate_id

# Store embeddings in JSON at ORM level; pgvector specifics handled in migrations.
Vector = None  # type: ignore
_EMBEDDING_TYPE = JSON


class SharedMemory(Base):
    """Shared memory record stored in PostgreSQL with pgvector support."""

    __tablename__ = "shared_memory"

    id: Mapped[str] = mapped_column(
        _ID_TYPE,
        primary_key=True,
        default=_ID_DEFAULT,
        # Rely on SQLAlchemy's Python-side default generation for cross-dialect
        # compatibility. PostgreSQL uses `gen_random_uuid()` via migrations, but
        # emitting it here would break SQLite tests.
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(_EMBEDDING_TYPE, nullable=False)
