"""create shared memory table"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover
    Vector = None  # type: ignore

# revision identifiers, used by Alembic.
revision: str = "8a67f9e83b3e"
down_revision: Union[str, Sequence[str], None] = ("f708791b9270", "ff891d366761")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql" and Vector is not None:  # pragma: no branch
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.create_table(
            "shared_memory",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
            sa.Column("agent_type", sa.String(length=50), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("embedding", Vector(1536)),
        )
    else:
        op.create_table(
            "shared_memory",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("agent_type", sa.String(length=50), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("embedding", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("shared_memory")
