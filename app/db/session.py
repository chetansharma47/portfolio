"""Async engine and session handling.

Serverless invocations are short lived and each one may land on a fresh
container, so connections are not pooled in production: NullPool hands the
work to the Neon pooler instead of holding sockets open between requests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings


def _build_url_and_connect_args() -> tuple[str, dict]:
    """asyncpg rejects libpq query params such as sslmode/channel_binding."""
    url = settings.database_url
    connect_args: dict = {}

    if url.startswith("postgresql+asyncpg://"):
        parts = urlsplit(url)
        if parts.query:
            url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", parts.fragment))
        connect_args["ssl"] = "require"
        connect_args["statement_cache_size"] = 0  # required behind a pgbouncer pooler

    return url, connect_args


def create_engine() -> AsyncEngine:
    url, connect_args = _build_url_and_connect_args()
    kwargs: dict = {
        "echo": settings.db_echo,
        "future": True,
        "connect_args": connect_args,
    }
    if settings.is_serverless or url.startswith("sqlite"):
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = settings.db_pool_size
        kwargs["max_overflow"] = settings.db_max_overflow
        kwargs["pool_pre_ping"] = True

    return create_async_engine(url, **kwargs)


engine: AsyncEngine = create_engine()

SessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a session that rolls back on error."""
    async with SessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
