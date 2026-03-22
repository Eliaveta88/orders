"""Async SQLAlchemy engine and session factory."""

import os
from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/orders"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for models."""

    __allow_unmapped__ = True


async def get_async_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """DB session from middleware (`request.state.db`)."""
    yield request.state.db
