from dataclasses import replace
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app import main, worker
from app.config import Settings
from app.db import session_scope
from app.ingest import save_fixtures
from app.models import Fixture, League, SyncJob, utcnow


def catalog_row(league_id, country="Argentina", current=True):
    return {
        "league": {"id": league_id, "name": f"Liga {league_id}", "type": "League"},
        "country": {"name": country},
        "seasons": [{"year": 2026, "current": current, "coverage": {
            "standings": True, "top_scorers": False,
        }}],
    }


def match(status="2H"):
    return {
        "fixture": {"id": 500, "date": "2026-10-12T19:00:00+00:00",
                    "status": {"short": status, "elapsed": 75}, "venue": {}},
        "league": {"id": 999, "season": 2026},
        "teams": {"home": {"id": 1, "name": "Local"}, "away": {"id": 2, "name": "Visitante"}},
        "goals": {"home": 2, "away": 1},
    }


def all_settings(monkeypatch):
    settings = replace(worker.settings, mode="api", league_scope="all", league_ids=(128,), profile="live")
    monkeypatch.setattr(worker, "settings", settings)
    monkeypatch.setattr(main, "settings", settings)


def test_auto_activation_requires_nonempty_key(monkeypatch):
    monkeypatch.setenv("DATA_MODE", "auto")
    monkeypatch.delenv("API_FOOTBALL_KEY", raising=False)
    assert Settings().mode == "demo"
    monkeypatch.setenv("API_FOOTBALL_KEY", "test-placeholder")
    assert Settings().mode == "api"
    monkeypatch.setenv("DATA_MODE", "api")
    monkeypatch.delenv("API_FOOTBALL_KEY")
    assert Settings().mode == "api"


def test_global_catalog_coverage_and_bounded_fixture_jobs(db, monkeypatch):
    all_settings(monkeypatch)
    worker.save_catalog(db, [catalog_row(128), catalog_row(999, "Spain"), catalog_row(1000, "England", False)])
    db.flush()
    assert db.get(League, ("api", 999))
    assert db.get(League, ("api", 1000))
    assert not db.get(SyncJob, "standings:999:2026")
    assert not db.get(SyncJob, "standings:1000:2026")
    assert not db.get(SyncJob, "scorers:999:2026")
    assert not db.get(SyncJob, "fixtures:999:2026")
    assert db.get(SyncJob, "fixtures:128:2026")
    assert len(list(db.scalars(select(SyncJob).where(SyncJob.kind == "day")))) == 10


def test_free_plan_preserves_catalog_but_bounds_background_jobs(db, monkeypatch):
    all_settings(monkeypatch)
    free_settings = replace(worker.settings, profile="free")
    monkeypatch.setattr(worker, "settings", free_settings)
    monkeypatch.setattr(main, "settings", free_settings)
    worker.save_catalog(db, [catalog_row(128), catalog_row(999, "Spain")])
    db.flush()
    assert db.get(League, ("api", 999))
    assert not db.get(SyncJob, "fixtures:128:2026")
    assert not db.get(SyncJob, "standings:999:2026")
    assert len(list(db.scalars(select(SyncJob).where(SyncJob.kind == "day")))) == 3


def test_global_api_exposes_unlisted_leagues_and_separates_demo(monkeypatch):
    all_settings(monkeypatch)
    with session_scope() as s:
        worker.save_catalog(s, [catalog_row(999, "Spain"), catalog_row(888)])
        save_fixtures(s, [match()], None)
    with TestClient(main.app) as client:
        leagues = client.get("/api/leagues").json()["data"]
        assert [league["id"] for league in leagues] == [888, 999]
        fixtures = client.get("/api/fixtures?date=2026-10-12").json()
        assert [row["id"] for row in fixtures["data"]] == [500]
        # Una fecha distinta no oculta el marcador en el filtro En vivo.
        live = client.get("/api/fixtures?date=2026-10-13&live=true").json()
        assert [row["id"] for row in live["data"]] == [500]
        assert fixtures["meta"]["mode"] == "api"
        assert client.get("/api/leagues/999/standings").status_code == 200
        assert client.get("/api/status").json()["data"]["league_scope"] == "all"


def test_global_live_and_date_are_single_queries(monkeypatch):
    all_settings(monkeypatch)
    monkeypatch.setattr(worker, "utcnow", lambda: datetime(2026, 10, 13, 2, 0, tzinfo=timezone.utc))
    with session_scope() as s:
        worker.save_catalog(s, [catalog_row(999)])
    calls = []

    class Client:
        def get(self, endpoint, params):
            calls.append((endpoint, params))
            return [match()]

    worker.execute_job(Client(), "live", {})
    worker.execute_job(Client(), "day", {"offset": 0})
    assert calls == [
        ("/fixtures", {"live": "all"}),
        ("/fixtures", {"date": "2026-10-12", "timezone": "America/Argentina/Buenos_Aires"}),
    ]


def test_disappeared_live_match_is_reconciled_to_final(monkeypatch):
    all_settings(monkeypatch)
    now = datetime(2026, 10, 12, 21, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(worker, "utcnow", lambda: now)
    with session_scope() as s:
        worker.save_catalog(s, [catalog_row(999)])
        save_fixtures(s, [match()], None)
        s.get(Fixture, ("api", 500)).updated_at = now - timedelta(hours=2)

    class Client:
        def get(self, endpoint, params):
            assert params == {"ids": "500"}
            return [match("FT")]

    worker.execute_job(Client(), "settle", {})
    with session_scope() as s:
        assert s.get(Fixture, ("api", 500)).status == "FT"
        assert not worker.live_ids(s, now)


def test_live_not_starved_by_initial_thousands_of_tables(monkeypatch):
    all_settings(monkeypatch)
    with session_scope() as s:
        s.add(SyncJob(key="table", kind="standings", params={}, next_run=utcnow() - timedelta(days=3)))
        s.add(SyncJob(key="live", kind="live", params={}, next_run=utcnow() - timedelta(seconds=1)))
    executed = []
    monkeypatch.setattr(worker, "execute_job", lambda client, kind, params: executed.append(kind) or 60)
    for _ in range(3):
        worker.tick(None)
    assert "live" in executed
    assert "standings" in executed


def test_undetermined_participants_do_not_abort_daily_snapshot(db, monkeypatch):
    all_settings(monkeypatch)
    worker.save_catalog(db, [catalog_row(999)])
    unknown = match()
    unknown["fixture"]["id"] = 501
    unknown["teams"]["away"]["id"] = None
    save_fixtures(db, [unknown, match()], None)
    assert not db.get(Fixture, ("api", 501))
    assert db.get(Fixture, ("api", 500))


def test_pro_recovery_ids_fit_database_source_column():
    from app.models import WorkerState
    import inspect
    import re

    limit = WorkerState.__table__.c.source.type.length
    source = inspect.getsource(worker.run)
    keys = re.findall(r'WorkerState\(source=["\']([^"\']+)["\']', source)
    keys += re.findall(r's\.get\(WorkerState, ["\']([^"\']+)["\']', source)
    assert keys
    assert all(len(key) <= limit for key in keys), (keys, limit)
