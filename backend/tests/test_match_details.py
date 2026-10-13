from dataclasses import replace

from fastapi.testclient import TestClient
from app import main, worker
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


def test_public_details_only_uses_cache(db, monkeypatch):
    fake = replace(main.settings, mode="api", league_scope="all", league_ids=(128,))
    monkeypatch.setattr(main, "settings", fake)
    league(db)
    save_fixtures(db, [fixture(status="FT", goals={"home": 1, "away": 0})], [128])
    store_details(db, 1, [
        {"time": {"elapsed": 21}, "team": {"id": 12800},
         "player": {"name": "Autor"}, "type": "Goal", "detail": "Normal Goal"}
    ], [], None)
    db.commit()
    assert db.get(FixtureDetails, ("api", 1))
    with TestClient(main.app) as client:
        response = client.get("/api/fixtures/1/details")
    assert response.status_code == 200
    assert response.json()["data"]["events"][0]["player"] == "Autor"
    assert response.json()["data"]["best_rated_player"] is None
    assert response.json()["meta"]["available"] is True
