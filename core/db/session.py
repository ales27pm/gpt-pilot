from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import DBConfig
from core.log import get_logger

log = get_logger(__name__)


class SessionManager:
    """
    Async-aware context manager for database session.

    Usage:

    >>> config = DBConfig(url="postgresql+asyncpg://postgres:postgres@localhost:5432/test")
    >>> async with DBSession(config) as session:
    ...     # Do something with the session
    """

    def __init__(self, config: DBConfig):
        """
        Initialize the session manager with the given configuration.

        :param config: Database configuration.
        """
        self.config = config
        self.engine = create_async_engine(
            self.config.url,
            echo=config.debug_sql,
            echo_pool="debug" if config.debug_sql else None,
            pool_pre_ping=True,
        )
        self.SessionClass = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        self.session = None

        event.listen(self.engine.sync_engine, "connect", self._on_connect)

    def _on_connect(self, dbapi_connection, _):
        """Connection event handler"""
        log.debug(f"Connected to database {self.config.url}")

        if self.config.url.startswith("postgresql"):
            try:
                dbapi_connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
            except Exception:
                log.debug("pgvector extension already installed or cannot be installed")

    async def start(self) -> AsyncSession:
        if self.session is not None:
            raise RuntimeError("Session already started; create a new SessionManager per task")

        self.session = self.SessionClass()
        return self.session

    async def close(self):
        if self.session is None:
            log.warning("Closing database session that was never opened", stack_info=True)
            return

        await self.session.close()
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.close()


__all__ = ["SessionManager"]
