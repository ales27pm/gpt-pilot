"""Add web column to project_states

Revision ID: da904e0f1c0e
Revises: 8a67f9e83b3e
Create Date: 2025-09-09 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da904e0f1c0e"
down_revision: Union[str, None] = "b760f66138c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("project_states", schema=None) as batch_op:
        batch_op.add_column(sa.Column("web", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("project_states", schema=None) as batch_op:
        batch_op.drop_column("web")
