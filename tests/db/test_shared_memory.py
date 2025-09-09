import pytest
from sqlalchemy import select

from core.config import DBConfig
from core.db.models import SharedMemory
from core.db.session import SessionManager
from core.db.setup import run_migrations


@pytest.mark.asyncio
async def test_bulk_insert_generates_unique_ids(tmp_path):
    db_cfg = DBConfig(url=f"sqlite+aiosqlite:///{tmp_path}/test.db")
    run_migrations(db_cfg)
    manager = SessionManager(db_cfg)
    async with manager as db:
        records = [
            {"agent_type": "a", "content": "foo", "embedding": [0.0]},
            {"agent_type": "b", "content": "bar", "embedding": [0.1]},
        ]
        await db.execute(SharedMemory.__table__.insert(), records)
        await db.commit()

        q = await db.execute(select(SharedMemory.id))
        ids = [row[0] for row in q]

        assert len(ids) == 2
        assert len(set(ids)) == 2
        assert all(isinstance(i, str) and len(i) == 36 for i in ids)
