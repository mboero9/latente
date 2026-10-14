"""League coverage regressions: MLS, assists, handball and volleyball."""
from dataclasses import replace
from fastapi.testclient import TestClient
from app import main
from app.config import settings
from app.db import session_scope
from app.ingest import save_assists
from app.models import SportSnapshot
from app.sports_scheduler import automatic_targets, due_jobs
from app.sports_sources import normalize_standings
from test_application import league


def test_mls_is_mandatory():
    assert 253 in settings.league_ids


def test_mls_assists_independent_of_goals(monkeypatch):
    monkeypatch.setattr(main, "settings", replace(main.settings, mode="api", league_scope="all"))
    fake = [{"player":{"id":100,"name":"Jugador"},
             "statistics":[{"league":{"id":128,"season":2026},
              "team":{"id":1000,"name":"Equipo"},
              "goals":{"total":8,"assists":19},
              "games":{"appearences":28}}]}]
    with session_scope() as db:
        league(db)
        assert save_assists(db, fake, 128, 2026)
        assert db.get(SportSnapshot, ("football", "assists", "128:2026"))
    with TestClient(main.app) as client:
        out=client.get("/api/leagues/128/assists?season=2026")
        assert out.status_code==200
        assert out.json()["data"][0]["assists"]==19
        assert client.get("/api/leagues/128/scorers?season=2026").status_code==200


def test_standings_include_verified_club_logos_goals():
    logo="https://media.api-sports.io/hockey/teams/25.png"
    raw=[[{"position":1,"team":{"id":25,"name":"Knights","logo":logo},
           "group":{"name":"West"},"games":{"played":10,"win":{"total":8},
           "draw":0,"lose":{"total":2}},"goals":{"for":41,"against":18},
           "points":18}]]
    rows=normalize_standings(raw,sport="nhl")
    assert rows[0]["logo"]==logo
    assert (rows[0]["won"],rows[0]["lost"],rows[0]["scored"],rows[0]["conceded"])==(8,2,41,18)


def test_catalog_season_ids_are_verified():
    catalog=[
      {"id":3,"name":"NHL","country":"USA","seasons":[2025,2026]},
      {"id":12,"name":"Bundesliga","country":"Germany","seasons":[2024,2025,2026]},
    ]
    assert automatic_targets("nhl",catalog,2026)==[{"league":3,"season":2026,"country":"USA"}]
    assert automatic_targets("handball",catalog,2026)==[{"league":12,"season":2026,"country":"Germany"}]
    assert automatic_targets("volleyball",catalog,2026)==[]
    assert automatic_targets("nhl",[{"id":3,"name":"NHL","country":"USA","seasons":[]}],2026)==[]


def test_activity_discovery_runs_with_old_autosync_env(monkeypatch):
    monkeypatch.setenv("SPORTS_AUTOSYNC", "nhl,mlb,f1")
    jobs=due_jobs()
    assert any(s=="handball" and k=="leagues" for s,k,_,_ in jobs)
    assert any(s=="volleyball" and k=="leagues" for s,k,_,_ in jobs)


def test_mls_navigation_and_assists():
    from pathlib import Path
    content=(Path(__file__).resolve().parents[2]/"frontend/src/main.tsx").read_text()
    assert '["/league/253", "🇺🇸 MLS"]' in content
    assert "function AssistsView(" in content
    assert '"assists", "Asistencias"' in content
