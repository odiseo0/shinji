from typing import AsyncGenerator

from starlite import Response

from .session import AsyncSessionFactory, AsyncScopedSession


async def get_db() -> AsyncGenerator:
    """Dependency that yields an `AsyncSession` for accessing the database."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()


async def session_after_request(response: Response) -> Response:
    """
    Inspects `response` to determine if we should commit, or rollback the database
    transaction.
    Finally, calls `remove()` on the scoped session.

    Parameters
    ----------
    :response: Response

    Returns
    -------
    Response
    """
    if 200 <= response.status_code < 300:
        await AsyncScopedSession.commit()
    else:
        await AsyncScopedSession.rollback()

    await AsyncScopedSession.remove()

    return response
