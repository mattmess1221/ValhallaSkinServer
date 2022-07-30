from threading import RLock
from typing import Generator

from fastapi import Depends, HTTPException
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal
from .models import SecretSanity

secret_lock = RLock()


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db(session: Session = Depends(get_db_session)):
    secret = settings.secret_key
    with secret_lock:
        try:
            saved_secret = session.query(SecretSanity).one()
            if saved_secret.secret != secret:
                raise HTTPException(
                    500, "Sanity error! Secret does not match, did the secret change?"
                )
        except NoResultFound:
            session.add(SecretSanity(secret=secret))
            session.commit()
        except MultipleResultsFound:
            raise HTTPException(
                500, "Multiple secrets found. Something has gone terribly wrong."
            )

    yield session
