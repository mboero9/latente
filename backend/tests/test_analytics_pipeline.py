from datetime import date, timedelta
from dataclasses import replace

from fastapi.testclient import TestClient
from app import main
from app.analytics import safe_div, summarize
from app.db import session_scope
from app.ingest import save_fixtures
from app.models import League, SportSnapshot, SportQuota, utcnow
from app.sports_sources import normalize_standings, normalize_games
from app.sports_scheduler import persist_snapshot, reserve_quota, sync_once
from test_application import fixture, league


def test_safely_calculates_only_final_scores():
    class Row:
        def __init__(self, status, home_goals, away_goals):
            self.status = status
            self.home_goals = home_goals
            self.away_goals = away_goals
            self.home_id = 1
            self.away_id = 2
    data = summarize([
        Row("FT", 3, 1), Row("FT", 2, 2),
        Row("NS", None, None), Row("AWD", 6, 0),
    ], {1: "Home", 2: "Away"}, season=2026)
    assert data["finished_matches_available"] == 2
    team = next(x for x in data["teams"] if x["team_id"] == 1)
    assert team["scored"] == 5 and team["conceded"] == 3
    assert team["goals_for_per_game"] == 2.5
    assert team["points_per_game_estimated"] == 2.0
    assert team["matches_complete_vs_standings"] is False
    assert safe_div(2, 0) is None


def test_real_football_analytics_endpoint(monkeypatch):
    monkeypatch.setattr(main, "settings", replace(
        main.settings, mode="api", league_scope="all", league_ids=(128,)))
    with session_scope() as db:
        league(db)
        save_fixtures(db, [
            fixture(1201, "FT", utcnow() - timedelta(days=1),
                    {"home": 2, "away": 1}),
        ], None)
    with TestClient(main.app) as client:
        response = client.get("/api/leagues/128/analytics?season=2026").json()
        assert response["data"]["finished_matches_available"] == 1
        assert response["data"]["teams"][0]["goals_for_per_game"] is not None
        archive = client.get("/api/leagues/128/analytics/history").json()
        assert archive["data"]["seasons"][0]["champion"] is None


def test_multisport_standings_groups_and_snapshots(monkeypatch):
    records = [[{
        "team": {"id": 12, "name": "Club A"}, "position": 1,
        "games": {"played": 10, "win": 8, "lose": 2}, "points": 16,
        "group": {"name": "Conference A"}
    }]]
    normalized = normalize_standings(records)
    assert normalized[0]["team_id"] == 12
    assert normalized[0]["played"] == 10
    assert normalized[0]["group"] == "Conference A"
    persist_snapshot("nhl", "standings", "57:2026", normalized, 1)
    monkeypatch.setattr(main, "settings", replace(main.settings, mode="api"))
    with TestClient(main.app) as client:
        result = client.get("/api/sports/nhl/dataset?kind=standings&ref=57:2026").json()
        assert result["data"][0]["team"] == "Club A"
        listings = client.get("/api/sports/nhl/datasets").json()
        assert listings["data"][0]["ref"] == "57:2026"


def test_quota_cannot_be_reset_by_multiple_worker_runs():
    for _ in range(3):
        assert reserve_quota("nba", cap=3)
    assert not reserve_quota("nba", cap=3)
    with session_scope() as db:
        assert db.get(SportQuota, ("nba", utcnow().date())).requests == 3


def test_provider_failure_keeps_last_snapshot(monkeypatch):
    from app import sports_scheduler as sc
    yesterday = utcnow().date() - timedelta(days=1)
    persist_snapshot("nhl", "games", yesterday.isoformat(),
                     [{"id": 7, "home": "Team A"}], 1)
    # A stale snapshot must never be deleted because of a provider error.
    monkeypatch.setattr(sc, "due_jobs",
                        lambda: [("nhl", "games", yesterday.isoformat(), yesterday)])
    monkeypatch.setattr(sc, "reserve_quota", lambda sport: True)
    monkeypatch.setattr(sc, "api_key", lambda sport: "fake", raising=False)
    monkeypatch.setenv("API_FOOTBALL_KEY", "fake")
    def rejected(*args, **kwargs):
        from app.sports_sources import SourceUnavailable
        raise SourceUnavailable("not available")
    outcome = sync_once(max_calls=1, fetch=rejected)
    with session_scope() as db:
        assert db.get(SportSnapshot, ("nhl", "games", yesterday.isoformat())).data[0]["id"] == 7
    assert outcome["updated"] == []
