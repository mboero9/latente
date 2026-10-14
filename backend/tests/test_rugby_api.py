"""API-Rugby safety and integration contracts. No real provider quota used."""
from app import rugby_api, main
from app.db import session_scope
from app.models import SportSnapshot
from fastapi.testclient import TestClient


def leagues():
    return [
        {"id": 67, "name": "Top 12", "country": {"name": "Argentina"}, "seasons": [2024, 2025, 2026]},
        {"id": 90, "name": "Rugby Championship", "country": {"name": "World"},
         "seasons": [{"season": 2025}, {"season": 2026, "current": True}]},
        {"id": 91, "name": "Six Nations", "country": {"name": "Europe"}, "seasons": [2026]},
        {"id": 92, "name": "Top 14", "country": {"name": "France"}, "seasons": [2026]},
        {"id": 93, "name": "Top 14", "country": {"name": "Italy"}, "seasons": [2026]},
    ]


def sample_games():
    return [
        {"id": 5, "date": "2026-09-21T18:00:00+00:00",
         "teams": {"home": {"id": 3, "name": "Los Pumas"},
                   "away": {"id": 6, "name": "South Africa"}},
         "scores": {"home": {"total": 28}, "away": {"total": 24}},
         "status": {"short": "FT", "long": "Game Finished"}},
        {"id": 6, "date": "2026-11-21T18:00:00+00:00",
         "teams": {"home": {"id": 3, "name": "Los Pumas"},
                   "away": {"id": 8, "name": "Australia"}},
         "scores": {"home": None, "away": None},
         "status": {"short": "NS", "long": "Not Started"}},
    ]


def sample_table():
    return [[
        {"position": 1, "team": {"id": 3, "name": "Los Pumas"}, "group": "General",
         "games": {"played": 6, "win": 4, "draw": 0, "lose": 2}, "points": 18},
    ]]


def test_api_rugby_matches_actual_name_and_country():
    catalog = rugby_api.resolve(leagues())
    assert next(x for x in catalog if x["slug"] == "urba")["league_id"] == 67
    assert next(x for x in catalog if x["slug"] == "championship")["league_id"] == 90
    assert next(x for x in catalog if x["slug"] == "top-14")["league_id"] == 92
    assert next(x for x in catalog if x["slug"] == "premiership")["league_id"] is None
    assert catalog[0]["seasons"] == [2026, 2025, 2024]


def test_game_and_standings_normalization():
    games = rugby_api.normalize_games(sample_games())
    assert games[0]["completed"] is True
    assert games[0]["home_score"] == 28
    assert games[1]["completed"] is False
    assert games[1]["home_score"] is None
    official = rugby_api.normalize_standings(sample_table())
    assert official[0]["points"] == 18
    assert official[0]["team"] == "Los Pumas"


def test_rugby_cron_only_fetches_verified_ids_and_persists(monkeypatch):
    monkeypatch.setattr(rugby_api, "key_configured", lambda: True)
    monkeypatch.setattr(rugby_api, "reserve_quota", lambda *args, **kwargs: True)
    queries = []

    def fake(endpoint, params):
        queries.append((endpoint, dict(params)))
        if endpoint == "leagues":
            return leagues()
        if endpoint == "games":
            assert params["league"] == 67
            return sample_games()
        if endpoint == "standings":
            assert params["league"] == 67
            return sample_table()
        raise AssertionError(endpoint)

    report = rugby_api.sync_once(max_calls=3, fetch=fake)
    assert len(report["attempted"]) == 3
    assert [q[0] for q in queries] == ["leagues", "games", "standings"]
    catalog = rugby_api.public_catalog()
    assert catalog[0]["league_id"] == 67
    stored = rugby_api.read_competition("urba", 2026)
    assert stored["available"] is True
    assert stored["official"][0]["points"] == 18
    assert stored["games"][0]["home_score"] == 28

    # Repeat runs reuse persisted data, not API requests per site visitor.
    assert rugby_api.sync_once(max_calls=3, fetch=fake)["attempted"] == []


def test_rugby_http_uses_database_snapshots_without_provider_calls(monkeypatch):
    monkeypatch.setattr(rugby_api, "key_configured", lambda: True)
    monkeypatch.setattr(rugby_api, "reserve_quota", lambda *args, **kwargs: True)
    def fail(*args):
        raise AssertionError("No third-party HTTP from visitor route")
    with TestClient(main.app) as client:
        assert client.get("/api/rugby/urba").status_code == 200
        assert client.get("/api/rugby/catalog").status_code == 200
        assert client.get("/api/rugby/nonexistent").status_code == 422


def test_api_rugby_does_not_invent_standings_when_missing(monkeypatch):
    monkeypatch.setattr(rugby_api, "key_configured", lambda: True)
    monkeypatch.setattr(rugby_api, "reserve_quota", lambda *args, **kwargs: True)
    calls = []
    def fake(endpoint, params):
        calls.append(endpoint)
        return leagues() if endpoint == "leagues" else []
    rugby_api.sync_once(max_calls=3, fetch=fake)
    actual = rugby_api.read_competition("urba", 2026)
    assert not actual["available"]
    assert actual["official"] == []
    assert actual["games"] == []
