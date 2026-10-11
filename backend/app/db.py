from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session
from .config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=5
)


@contextmanager
def session_scope():
    with Session(engine) as session:
        with session.begin():
            yield session
