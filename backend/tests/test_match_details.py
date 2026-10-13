from dataclasses import replace

from fastapi.testclient import TestClient
from app import main, worker
from app.db import session_scope
from app.ingest import save_fixtures
from app.match_details import normalize_events, normalize_lineups, normalize_player_ratings, store_details
from app.models import FixtureDetails
from test_application import league, fixture


def test_normalize_real_match_event_goal_assist_and_card():
    data = normalize_events([
        {"time": {"elapsed": 55, "extra": 2}, "team": {"id": 1},
         "player": {"name": "Delantero"}, "assist": {"name": "Asistente"},
         "type": "Goal", "detail": "Normal Goal"},
        {"time": {"elapsed": 70}, "team": {"id": 2}, "player": {"name": "Defensor"},
         "type": "Card", "detail": "Red Card"},
    ])
    assert data[0]["minute"] == 55 and data[0]["extra"] == 2
    assert data[0]["assist"] == "Asistente"
    assert data[1]["detail"] == "Red Card"


def test_team_lineup_and_pitch_position():
    lineups = normalize_lineups([{
        "team": {"id": 1}, "formation": "4-3-3",
        "coach": {"name": "Director Técnico"},
        "startXI": [{"player": {"id": 10, "name": "Arquero", "number": 1, "pos": "G", "grid": "1:1"}}],
        "substitutes": [{"player": {"id": 11, "name": "Suplente", "number": 12}}],
    }])
    assert lineups[0]["formation"] == "4-3-3"
    assert lineups[0]["start"][0]["grid"] == "1:1"
    assert lineups[0]["bench"][0]["name"] == "Suplente"


def test_ratings_do_not_imply_official_mvp():
    results = normalize_player_ratings([
        {"team": {"id": 1}, "players": [{"player": {"id": 9, "name": "Jugador"},
         "statistics": [{"games": {"rating": "8.5"}}]}]}
    ])
    assert results[0]["rating"] == 8.5
    assert normalize_player_ratings([{"team": {"id": 1}, "players": [
        {"player": {"id": 2, "name": "Sin nota"}, "statistics": [{"games": {"rating": None}}]}
    ]}]) == []


def test_public_details_only_uses_cache(monkeypatch):
    fake = replace(main.settings, mode="api", league_scope="all", league_ids=(128,))
    monkeypatch.setattr(main, "settings", fake)
    with session_scope() as s:
        league(s)
        save_fixtures(s, [fixture(status="FT", goals={"home": 1, "away": 0})], [128])
        store_details(s, 1, [
            {"time": {"elapsed": 21}, "team": {"id": 1},
             "player": {"name": "Autor"}, "type": "Goal", "detail": "Normal Goal"}
        ], [], None)
    with TestClient(main.app) as client:
        response = client.get("/api/fixtures/1/details")
    assert response.status_code == 200
    assert response.json()["data"]["events"][0]["player"] == "Autor"
    assert response.json()["data"]["best_rated_player"] is None
    assert response.json()["meta"]["available"] is True


def test_pro_queues_twenty_fixture_batches_for_goal_authors(monkeypatch):
    from datetime import timedelta
    from sqlalchemy import select
    from app.models import SyncJob, utcnow
    from test_application import fixture as example
    settings = replace(worker.settings, mode="api", league_scope="all",
                       profile="live", league_ids=(128,))
    monkeypatch.setattr(worker, "settings", settings)
    with session_scope() as db:
        league(db)
        for number in range(1, 24):
            save_fixtures(db, [example(
                number, "FT", utcnow() - timedelta(days=1),
                {"home": 1, "away": 0},
            )], [128])
        worker.enqueue_hydration(db, 128, 2026)
        jobs = list(db.scalars(select(SyncJob).where(SyncJob.kind == "hydrate")))
        assert sorted(len(job.params["ids"]) for job in jobs) == [3, 20]
        params = next(job.params for job in jobs if len(job.params["ids"]) == 20)

    class Client:
        def get(self, endpoint, query):
            assert endpoint == "/fixtures"
            assert len(query["ids"].split("-")) == 20
            out = []
            for number in map(int, query["ids"].split("-")):
                row = example(number, "FT", utcnow() - timedelta(days=1),
                              {"home": 1, "away": 0})
                row["events"] = [{
                    "team": {"id": 1}, "time": {"elapsed": 22},
                    "player": {"name": f"Autor {number}"},
                    "type": "Goal", "detail": "Normal Goal",
                }]
                row["lineups"] = []
                out.append(row)
            return out

    worker.execute_job(Client(), "hydrate", params)
    with session_scope() as db:
        for number in params["ids"]:
            row = db.get(FixtureDetails, ("api", number))
            assert row and row.events[0]["player"] == f"Autor {number}"
            assert row.events_checked_at is not None


def test_event_snapshots_do_not_erase_goals_if_provider_omits_events():
    with session_scope() as db:
        league(db)
        save_fixtures(db, [fixture(status="FT", goals={"home": 1, "away": 0})], [128])
        store_details(db, 1, [{
            "team": {"id": 1}, "time": {"elapsed": 47},
            "player": {"name": "Autor verificado"},
            "type": "Goal", "detail": "Normal Goal",
        }], None)
    with session_scope() as db:
        store_details(db, 1, None, None, mark_events_checked=True)
        row = db.get(FixtureDetails, ("api", 1))
        db.expire_all()
        assert row.events[0]["player"] == "Autor verificado"
        assert row.events_checked_at is not None
