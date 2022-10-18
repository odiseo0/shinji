from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, AsyncGenerator

from .session import AsyncSessionFactory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator:
    """Dependency that yields an `AsyncSession` for accessing the database."""
    async with AsyncSessionFactory() as db:
        try:
            yield db
        finally:
            await db.close()


@contextmanager
async def session() -> AsyncSession:
    async with AsyncSessionFactory() as db:
        return db
