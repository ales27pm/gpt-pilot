"""create shared memory table"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

try:  # pragma: no cover - optional dependency
    from pgvector.sqlalchemy import Vector  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Vector = None  # type: ignore

# revision identifiers, used by Alembic.
revision: str = "8a67f9e83b3e"
down_revision: Union[str, Sequence[str], None] = ("f708791b9270", "ff891d366761")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    use_pgvector = bind.dialect.name == "postgresql" and Vector is not None

    if use_pgvector:  # pragma: no branch
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    id_col = sa.Column(
        "id", sa.String(length=36), primary_key=True, nullable=False
    )
    embedding_col = sa.Column(
        "embedding",
        Vector(1536) if use_pgvector else sa.JSON(),
        nullable=False,
    )
    op.create_table(
        "shared_memory",
        id_col,
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        embedding_col,
    )
    if use_pgvector:  # pragma: no branch
        # Ensure idempotency if migration is accidentally re-run
        op.execute(
            "DO $$ BEGIN "
            "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_shared_memory_embedding_dims') THEN "
            "ALTER TABLE shared_memory ADD CONSTRAINT ck_shared_memory_embedding_dims CHECK (vector_dims(embedding) = 1536); "
            "END IF; "
            "END $$;"
        )


def downgrade() -> None:
    bind = op.get_bind()
    use_pgvector = bind.dialect.name == "postgresql" and Vector is not None

    op.drop_table("shared_memory")
    if use_pgvector:  # pragma: no branch
        op.execute("DROP EXTENSION IF EXISTS vector")
