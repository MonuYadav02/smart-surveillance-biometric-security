"""
Database Configuration and Setup
"""

import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    future=True
)

# Create session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create declarative base
Base = declarative_base()

# Metadata
metadata = MetaData()

async def create_tables():
    """Create database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

async def get_db():
    """Get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()