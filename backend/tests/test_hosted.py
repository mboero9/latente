from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.config import Settings
from app.db import engine, session_scope
from app.main import app
from app.models import WorkerState, utcnow
from app import worker


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
def test_provider_database_urls_use_installed_driver(monkeypatch, scheme):
    monkeypatch.setenv("DATABASE_URL", f"{scheme}://app:p%40ss@db:5432/football?sslmode=require")
    url = Settings().database_url
    assert url.drivername == "postgresql+psycopg"
    assert url.password == "p@ss" and url.query["sslmode"] == "require"


def test_cron_health_accepts_interval_but_detects_missed_run(monkeypatch):
    monkeypatch.setenv("WORKER_EXPECTED_INTERVAL_SECONDS", "1800")
    with TestClient(app) as client:
        with session_scope() as s:
            s.add(WorkerState(source="demo", heartbeat=utcnow() - timedelta(minutes=25), message="Cron"))
        assert client.get("/api/status").json()["data"]["worker_online"]
        with session_scope() as s:
            s.get(WorkerState, "demo").heartbeat = utcnow() - timedelta(minutes=40)
        assert not client.get("/api/status").json()["data"]["worker_online"]


def test_once_exits_and_releases_leader_lock(postgres):
    worker.run(once=True, max_seconds=10)
    with session_scope() as s:
        assert s.get(WorkerState, "demo") is not None
    # Una sesión independiente debe poder tomar el lock tras finalizar el cron.
    from sqlalchemy import create_engine
    other = create_engine(engine.url)
    try:
        with other.connect() as connection:
            assert connection.scalar(text("SELECT pg_try_advisory_lock(67120834)"))
            connection.execute(text("SELECT pg_advisory_unlock(67120834)"))
    finally:
        other.dispose()
