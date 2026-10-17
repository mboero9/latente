"""Odds module: real bookmaker attribution, implied probability and live snapshots."""
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app import main, odds, worker
from app.db import session_scope
from app.models import FixtureOdds, utcnow
from app.ingest import save_fixtures
from test_application import league, fixture


def test_odds_probability_and_provider_bookmakers_only():
    values = [{"value": "Home", "odd": "2.50"},
              {"value": "Draw", "odd": "3.00"},
              {"value": "Away", "odd": "3.20"}]
    answer = odds.outcomes(values)
    assert answer is not None
    assert answer["implied"]["home"] == 40.0
    assert answer["implied"]["draw"] == 33.3
    assert answer["implied"]["away"] == 31.2
    assert abs(sum(answer["normalized"].values())-100) < 0.2
    assert odds.outcomes([{"value":"Home","odd":0}]) is None

    pre = odds.prematch([{"update": "2026-10-14T17:00:00Z",
        "bookmakers": [
            {"name": "Bet365", "bets": [{"name": "Match Winner", "values": values}]},
            {"name": "Book without prices", "bets": [{"name": "Other bet", "values": values}]},
        ]}])
    assert len(pre) == 1
    assert pre[0]["bookmaker"] == "Bet365"
    assert not any(x["bookmaker"] == "Betano" for x in pre)


def test_live_odds_cannot_be_attributed_to_specific_bookmaker():
    values = [{"value": "Home", "odd": "1.80"},
              {"value": "Draw", "odd": "3.50"},
              {"value": "Away", "odd": "4.75"}]
    raw = {"status": {"blocked": False, "stopped": False, "finished": False},
           "update": "2026-10-14T17:00:00Z",
           "odds": [{"name": "Match Winner", "values": values}]}
    live = odds.inplay([raw])
    assert live[0]["bookmaker"] is None
    assert live[0]["implied"]["home"] == 55.6
    assert odds.inplay([{**raw, "status": {"blocked": True}}]) == []


def test_live_batch_only_active_fixtures_with_fresh_snapshots(monkeypatch):
    monkeypatch.setattr(main, "settings", replace(main.settings,
                        mode="api", league_scope="all"))
    with session_scope() as s:
        league(s)
        save_fixtures(s, [fixture(1, "1H"), fixture(2, "FT")], [128])
        odds.persist(s, 1, "live", [{
            "source": "live", "bookmaker": None,
            "prices": {"home": 2.5, "draw": 3, "away": 3.2},
            "implied": {"home": 40., "draw": 33.3, "away": 31.2},
        }])
        odds.persist(s, 2, "live", [{
            "source": "live", "bookmaker": None,
            "prices": {"home": 1.5, "draw": 4.0, "away": 6.5},
            "implied": {"home": 66.7, "draw": 25., "away": 15.4},
        }])
    with TestClient(main.app) as client:
        rows = client.get("/api/odds/live")
        assert rows.status_code == 200
        assert len(rows.json()["data"]) == 1
        assert rows.json()["data"][0]["fixture_id"] == 1
        assert rows.json()["data"][0]["implied"]["home"] == 40.

    with session_scope() as s:
        stored = s.get(FixtureOdds, ("api", 1, "live"))
        stored.updated_at = utcnow() - timedelta(minutes=17)
    with TestClient(main.app) as client:
        assert client.get("/api/odds/live").json()["data"] == []


def test_worker_alternates_live_and_prematch_odds_queries(monkeypatch):
    monkeypatch.setattr(worker, "settings", replace(worker.settings,
                          mode="api", profile="live", league_scope="all"))
    with session_scope() as s:
        league(s)
        save_fixtures(s, [fixture(1, "1H"), fixture(2, "NS",
                       datetime(2026, 10, 14, 18, 10, tzinfo=timezone.utc))], [128])
    class Spy:
        def __init__(self): self.calls = []
        def get(self, endpoint, params):
            self.calls.append((endpoint, params))
            return []
    spy = Spy()
    monkeypatch.setattr(worker, "utcnow", lambda: datetime(2026, 10, 14, 16, 10, tzinfo=timezone.utc))
    worker.capture_betting_odds(spy)
    assert spy.calls == [("/odds", {"fixture": 2})]
    spy.calls.clear()
    monkeypatch.setattr(worker, "utcnow", lambda: datetime(2026, 10, 14, 16, 20, tzinfo=timezone.utc))
    worker.capture_betting_odds(spy)
    assert spy.calls == [("/odds/live", {})]


def test_frontend_odds_are_reachable_from_live_and_fixture_detail():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    main_file = (root/"frontend/src/main.tsx").read_text(encoding="utf-8")
    odds_file = (root/"frontend/src/match-odds.tsx").read_text(encoding="utf-8")
    assert "<MatchOdds id={m.id}" in main_file
    assert "<LiveOddsMini fixtureId={m.id}" in main_file
    brand_file = (root/"frontend/src/bookmaker-brands.tsx").read_text(encoding="utf-8")
    directory = (root/"frontend/src/betting-guide.tsx").read_text(encoding="utf-8")
    assert "www.betano.bet.ar" in brand_file
    assert "caba.bplay.bet.ar" in directory
    assert "BookmakerComparison" in odds_file
    assert "payoutUplift" in odds_file
    assert "closest" not in odds_file
    assert 'country==="BR"' in directory
    assert "sin casa identificada" in odds_file
