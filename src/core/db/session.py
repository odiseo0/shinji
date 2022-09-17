from asyncio import current_task

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)

from src.settings import settings


engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI, pool_size=40, max_overflow=10, pool_pre_ping=True
)
AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
AsyncScopedSession = async_scoped_session(AsyncSessionFactory, scopefunc=current_task)
