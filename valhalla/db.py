from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .database import SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db: AsyncSession
    async with SessionLocal() as db:
        yield db
