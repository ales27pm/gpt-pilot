from core.db.setup import _async_to_sync_db_scheme


def test_asyncpg_scheme_is_converted_to_psycopg():
    url = "postgresql+asyncpg://user:pass@localhost/db"
    assert _async_to_sync_db_scheme(url) == "postgresql+psycopg://user:pass@localhost/db"
