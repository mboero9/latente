import os
import pytest
from sqlalchemy import delete

# Base exclusiva de pruebas: nunca usar aquí una URL de producción.
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL", "sqlite:////tmp/latente-tests.sqlite"
)
os.environ["DATA_MODE"] = "demo"

from app.db import Base, engine, session_scope  # noqa: E402
from app import models  # noqa: E402, F401


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.create_all(engine)
    with session_scope() as s:
        for table in reversed(Base.metadata.sorted_tables):
            s.execute(delete(table))
    yield


@pytest.fixture
def db():
    with session_scope() as s:
        yield s


@pytest.fixture
def postgres():
    if engine.dialect.name != "postgresql":
        pytest.skip("Requiere TEST_DATABASE_URL PostgreSQL")
