"""
Database session management module.
Configures the SQLAlchemy async engine and provides a dependency for database sessions.
"""

import logging
from typing import Annotated

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import Depends

from config.settings import DB_URL

logger = logging.getLogger(__name__)

engine = create_async_engine(
    DB_URL,
    pool_size=20,
    max_overflow=20,
    pool_timeout=30,
)
ASYNC_SESSION_LOCAL = async_sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False
)
logger.info("Database connected successfully")


async def get_db() -> AsyncSession:
    """
    Dependency for obtaining an asynchronous database session.
    Yields a session and automatically closes it after use.
    """
    async with ASYNC_SESSION_LOCAL() as session:
        yield session


# DBDep is a type hint for a database session injected into FastAPI endpoints.
# It uses Annotated to combine the type hint with the Depends function.
# Depends automatically creates/closes the session after the request.
DBDep = Annotated[AsyncSession, Depends(get_db)]
