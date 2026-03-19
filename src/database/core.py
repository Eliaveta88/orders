"""Async SQLAlchemy engine and session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# TODO: Load from config
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/orders"

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

    pass
