from contextlib import contextmanager
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import DeclarativeBase, Session
from .config import settings


class Base(DeclarativeBase):
    pass


pool_mode = os.getenv("DB_POOL_MODE", "pooled")
if pool_mode not in {"pooled", "none"}:
    raise ValueError("DB_POOL_MODE debe ser pooled o none")
pool_options = (
    {"poolclass": NullPool}
    if pool_mode == "none"
    else {"pool_size": 5, "max_overflow": 5}
)
connect_options = (
    {"connect_timeout": 10}
    if settings.database_url.get_backend_name() == "postgresql"
    else {}
)
engine = create_engine(
    settings.database_url, pool_pre_ping=True, connect_args=connect_options, **pool_options
)


@contextmanager
def session_scope():
    with Session(engine) as session:
        with session.begin():
            yield session
