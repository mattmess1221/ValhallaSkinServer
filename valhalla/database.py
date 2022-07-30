from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

engine_args = {}
if settings.database_url.startswith("sqlite:///"):
    engine_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

