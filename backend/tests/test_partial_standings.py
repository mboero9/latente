from dataclasses import replace
from fastapi.testclient import TestClient
from sqlalchemy import select
from app import main
from app.ingest import save_fixtures, save_standings
from app.models import League
from app.partial_standings import partial_standings
from test_application import league, fixture, standing_group


class Game:
    def __init__(self, home, away, hg, ag, status="FT"):
        self.home_id, self.away_id = home, away
        self.home_goals, self.away_goals = hg, ag
        self.status = status


def test_partial_only_final_scores_and_sorting():
    teams = {1: {"id": 1, "name": "A"}, 2: {"id": 2, "name": "B"}, 3: {"id": 3, "name": "C"}}
    rows, count = partial_standings([
        Game(1, 2, 2, 1),
        Game(2, 3, 1, 1),
        Game(3, 1, 5, 0, "NS"),
    ], teams)
    assert count == 2
    assert [(r["team_id"], r["points"], r["played"]) for r in rows] == [
        (1, 3, 1), (3, 1, 1), (2, 1, 2),
    ]
    assert rows[0]["difference"] == 1
    assert rows[0]["description"] == "Cálculo parcial: no es la clasificación oficial"


def test_official_standings_are_always_preferred(db, monkeypatch):
    fake = replace(main.settings, mode="api", league_ids=(128,), league_scope="all")
    monkeypatch.setattr(main, "settings", fake)
    league(db)
    save_standings(db, [{"league": {"standings": [[standing_group("A", 1)]]}}], 128, 2026)
    db.commit()
    with TestClient(main.app) as client:
        response = client.get("/api/leagues/128/standings?season=2026").json()
    assert response["meta"]["provisional"] is False
    assert response["data"][0]["group"] == "A"
