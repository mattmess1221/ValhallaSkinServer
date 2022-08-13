from threading import RLock

from fastapi import Depends, HTTPException
from sqlalchemy.engine import ScalarResult
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .config import settings
from .database import SessionLocal
from .models import SecretSanity

secret_lock = RLock()


async def get_db_session():
    async with SessionLocal() as db:
        async with db.begin():
            yield db


async def get_db(session: AsyncSession = Depends(get_db_session)):
    secret = settings.secret_key
    with secret_lock:
        result: ScalarResult = await session.scalars(select(SecretSanity))
        try:
            saved_secret: SecretSanity = result.one()
            if saved_secret.secret != secret:
                raise HTTPException(
                    500,
                    "Sanity error! Secret does not match, did the secret change?",
                )
        except NoResultFound:
            session.add(SecretSanity(secret=secret))
            await session.commit()
        except MultipleResultsFound:
            raise HTTPException(
                500, "Multiple secrets found. Something has gone terribly wrong."
            )

    yield session
