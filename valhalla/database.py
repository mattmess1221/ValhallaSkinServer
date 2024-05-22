from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker[AsyncSession](engine)
