"""Dashboard Backend - Database Connection & Session Management

PostgreSQL 연결 관리 (asyncpg via SQLAlchemy async).
AWS_MODE=mock 시에도 로컬 PostgreSQL에 동일 스키마로 동작.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from .config import settings

logger = logging.getLogger(__name__)

# --- Engine Setup ---
engine = create_async_engine(
    settings.database_url,
    echo=(settings.log_level == "DEBUG"),
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# --- Session Factory ---
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy ORM base class."""
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session injection."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> dict:
    """Check database connectivity."""
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            return {"status": "healthy", "message": "Database connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "message": str(e)}


async def init_db():
    """Initialize database tables (for development/testing)."""
    # In production, use Alembic migrations
    # For local mock mode, we create tables from init-schema.sql
    logger.info("Database engine initialized")


async def close_db():
    """Close database engine."""
    await engine.dispose()
    logger.info("Database engine closed")
