from dataclasses import replace
from datetime import timedelta

from fastapi.testclient import TestClient

from app import main, worker
from app.db import session_scope
from app.ingest import save_fixtures, save_scorers
from app.match_details import store_details
from app.models import utcnow
from app.scorer_fallback import partial_scorers
from test_application import league, fixture


def _goal(name, detail="Normal Goal", minute=12):
    return {"team": {"id": 1}, "player": {"name": name},
            "time": {"elapsed": minute}, "type": "Goal", "detail": detail}


def test_provisional_scorers_only_use_real_non_own_goals():
    with session_scope() as db:
        league(db)
        save_fixtures(db, [
            fixture(1, "FT", utcnow() - timedelta(days=1), {"home": 3, "away": 1}),
            fixture(2, "FT", utcnow() - timedelta(days=2), {"home": 1, "away": 0}),
        ], [128])
        store_details(db, 1, [_goal("Autor"), _goal("Autor", "Penalty"),
                              _goal("Otro", "Own Goal")], None)
        store_details(db, 2, [_goal("Autor")], None)
    with session_scope() as db:
        results, scanned = partial_scorers(db, "api", 128, 2026, main.public)
    assert scanned == 2
    assert len(results) == 1
    assert results[0]["name"] == "Autor"
    assert results[0]["goals"] == 3
    assert results[0]["penalties"] == 1
    assert results[0]["player_id"] < 0


def test_scorers_api_marks_derived_list_as_provisional(monkeypatch):
    monkeypatch.setattr(main, "settings", replace(main.settings,
                        mode="api", league_scope="all", league_ids=(128,)))
    with session_scope() as db:
        league(db)
        save_fixtures(db, [fixture(3, "FT", utcnow() - timedelta(days=1),
                                   {"home": 1, "away": 0})], [128])
        store_details(db, 3, [_goal("Jugador", minute=22)], None)
    with TestClient(main.app) as client:
        result = client.get("/api/leagues/128/scorers?season=2026").json()
    assert result["meta"]["provisional"] is True
    assert result["meta"]["matches_used"] == 1
    assert result["data"][0]["name"] == "Jugador"
