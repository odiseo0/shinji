from typing import AsyncGenerator
from contextlib import contextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from .session import AsyncSessionFactory


async def get_db() -> AsyncGenerator:
    """Dependency that yields an `AsyncSession` for accessing the database."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()


@contextmanager
async def session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        return session
