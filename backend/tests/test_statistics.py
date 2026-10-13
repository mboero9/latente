from dataclasses import replace
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app import main, worker
from app.db import session_scope
from app.ingest import save_statistics
from app.models import FixtureStatistics, SyncJob, utcnow
from test_application import fixture
from test_global_catalog import catalog_row


def configure(monkeypatch):
    settings = replace(worker.settings, mode="api", league_scope="all", league_ids=(128,), profile="live")
    monkeypatch.setattr(worker, "settings", settings)
    monkeypatch.setattr(main, "settings", settings)


def covered_catalog(s, supported=True):
    row = catalog_row(128)
    row["seasons"][0]["coverage"]["fixtures"] = {"statistics_fixtures": supported}
    worker.save_catalog(s, [row])


def statistics():
    return [
        {"team": {"id": 1}, "statistics": [
            {"type": "Shots on Goal", "value": 0},
            {"type": "Ball Possession", "value": "58%"},
            {"type": "expected_goals", "value": None},
        ]},
        {"team": {"id": 2}, "statistics": [{"type": "Shots on Goal", "value": 3}]},
    ]


def test_snapshot_keeps_null_zero_and_previous_data_on_empty(db, monkeypatch):
    configure(monkeypatch)
    covered_catalog(db)
    worker.sync_fixture_rows(db, [fixture(status="2H")])
    rows = statistics()
    save_statistics(db, rows + [rows[0], {"team": {"id": 999}, "statistics": rows[0]["statistics"]}], 1)
    snapshot = db.get(FixtureStatistics, ("api", 1))
    original_updated = snapshot.updated_at
    assert [r["team_id"] for r in snapshot.data] == [1, 2]
    assert [r["value"] for r in snapshot.data[0]["statistics"]] == [0, "58%", None]
    save_statistics(db, [], 1)
    db.expire_all()
    assert db.get(FixtureStatistics, ("api", 1)).updated_at == original_updated
    assert not db.get(FixtureStatistics, ("demo", 1))


def test_statistics_jobs_require_coverage_and_recent_started_match(db, monkeypatch):
    configure(monkeypatch)
    covered_catalog(db, False)
    worker.sync_fixture_rows(db, [fixture(1, "2H")])
    assert not db.get(SyncJob, "statistics:1")
    covered_catalog(db)
    worker.sync_fixture_rows(db, [
        fixture(1, "2H"), fixture(2, "FT", utcnow() - timedelta(days=3)),
        fixture(3, "NS"), fixture(4, "FT", utcnow() - timedelta(hours=3)),
    ])
    db.flush()
    assert db.get(SyncJob, "statistics:1")
    assert db.get(SyncJob, "statistics:4")
    assert not db.get(SyncJob, "statistics:2")
    assert not db.get(SyncJob, "statistics:3")
    covered_catalog(db)
    db.flush()
    assert db.get(SyncJob, "statistics:1"), "El refresco del catálogo no debe borrar el trabajo del partido"


def test_final_snapshot_retires_job_without_recreating_it(monkeypatch):
    configure(monkeypatch)
    finished = fixture(1, "FT", utcnow() - timedelta(hours=5))
    with session_scope() as s:
        covered_catalog(s)
        worker.sync_fixture_rows(s, [finished])
        s.flush()
        s.execute(delete(SyncJob).where(SyncJob.kind != "statistics"))

    class Client:
        def get(self, endpoint, params):
            assert (endpoint, params) == ("/fixtures/statistics", {"fixture": 1})
            return statistics()

    worker.tick(Client())
    with session_scope() as s:
        assert not s.get(SyncJob, "statistics:1")
        assert s.get(FixtureStatistics, ("api", 1))
        worker.sync_fixture_rows(s, [finished])
        s.flush()
        assert not s.get(SyncJob, "statistics:1")


def test_removed_coverage_does_not_spend_provider_requests(monkeypatch):
    configure(monkeypatch)
    with session_scope() as s:
        covered_catalog(s, False)
        worker.sync_fixture_rows(s, [fixture(1, "2H")])

    class Client:
        def get(self, *args):
            raise AssertionError("No debe consultar estadísticas sin cobertura")

    assert worker.execute_job(Client(), "statistics", {"fixture": 1}) is None


def test_statistics_api_is_source_scoped_and_reports_stale_data(monkeypatch):
    configure(monkeypatch)
    with session_scope() as s:
        covered_catalog(s)
        worker.sync_fixture_rows(s, [fixture(1, "2H"), fixture(2, "NS")])
        save_statistics(s, statistics(), 1)
        s.get(FixtureStatistics, ("api", 1)).updated_at = utcnow() - timedelta(hours=1)
    with TestClient(main.app) as client:
        response = client.get("/api/fixtures/1/statistics").json()
        assert response["data"][0]["team"]["name"] == "Local"
        assert response["data"][0]["statistics"][0]["value"] == 0
        assert response["meta"]["mode"] == "api"
        assert response["meta"]["coverage"] is True
        assert response["meta"]["stale"] is True
        assert response["meta"]["updated_at"]
        assert client.get("/api/fixtures/2/statistics").json()["data"] == []
        assert client.get("/api/fixtures/999/statistics").status_code == 404
        assert client.get("/api/status").json()["data"]["display_refresh_seconds"] == 5


def test_tables_make_progress_amid_continuous_statistics(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setattr(worker, "background_turn", 0)
    with session_scope() as s:
        for kind in ("statistics", "standings"):
            s.add(SyncJob(key=kind, kind=kind, params={}, next_run=utcnow() - timedelta(days=1)))
    executed = []
    monkeypatch.setattr(worker, "execute_job", lambda client, kind, params: executed.append(kind) or 0)
    for _ in range(3):
        worker.tick(None)
    assert executed == ["statistics", "statistics", "standings"]
