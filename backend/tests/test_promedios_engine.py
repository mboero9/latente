"""Argentina 2026 averages: exact arithmetic, coverage, API-only reads."""
from types import SimpleNamespace
from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from app import main
from app.promedios import compute_promedios, regular_phase
from app.promedios_reference import parse_reference
from app.ingest import save_fixtures, upsert
from app.models import SportSnapshot, utcnow
from test_application import fixture, league

TEAMS = {1: {"id": 1, "name": "A"}, 2: {"id": 2, "name": "B"},
         3: {"id": 3, "name": "C"}}


def game(ident, year, home, away, hg, ag, round_name="Apertura - 1",
         status="FT", league_id=128):
    return SimpleNamespace(id=ident, league_id=league_id, season=year,
                           home_id=home, away_id=away, home_goals=hg,
                           away_goals=ag, round=round_name, status=status)


def test_regular_phase_excludes_playoff_rounds_and_unknowns():
    for label in ("Regular Season - 1", "Apertura - 16",
                  "Clausura - 4", "Primera Fase - 12",
                  "1st Phase - 3", "Fase de Zonas - 4"):
        assert regular_phase(label), label
    for label in ("Round of 16", "Quarter-finals", "Semi-finals", "Final",
                  "Apertura - Playoffs - Round of 16",
                  "Clausura - Final", None, "Unknown Round"):
        assert not regular_phase(label), label


def test_average_2024_2025_2026_excludes_non_regular_other_leagues_and_duplicates():
    rows = [
        game(1,2024,1,2,2,1,"Regular Season - 1"),
        game(2,2025,2,3,1,1,"Clausura - 12"),
        game(3,2026,1,2,0,0,"Apertura - 8"),
        game(4,2026,1,3,1,0,"Clausura - Quarter-finals"),
        game(5,2026,2,1,3,0,"Apertura - 9","NS"),
        game(6,2026,2,1,5,0,"Apertura - 9",league_id=130),
        game(3,2026,1,2,0,0,"Apertura - 8"),
    ]
    data=compute_promedios(rows,TEAMS,{1,2,3})
    ids={r["team_id"]:r for r in data["rows"]}
    assert data["matches_used"]==3
    assert data["matches_by_season"]=={"2024":1,"2025":1,"2026":1}
    assert (ids[1]["points"],ids[1]["played"],ids[1]["average"])==(4,2,2)
    assert (ids[2]["points"],ids[2]["played"])==(2,3)
    assert ids[3]["points"]==1
    assert ids[3]["seasons"]["2024"]["points"] is None
    assert ids[3]["missing_seasons"] == [2024, 2026]
    assert not any(r["verified"] for r in data["rows"])
    assert data["provisional"]


def test_official_baseline_validates_only_when_points_and_matches_equal():
    rows=[game(1,2024,1,2,2,0,"Regular Season - 1"),
          game(2,2026,1,2,1,1,"Clausura - 1")]
    reference=[{"team_id":1,"points":4,"played":2},
               {"team_id":2,"points":2,"played":2}]
    data=compute_promedios(rows,TEAMS,{1,2},reference)
    assert data["verified_count"]==1
    by_id={r["team_id"]:r for r in data["rows"]}
    assert by_id[1]["verified"] is True
    assert by_id[2]["difference"]=={"points":-1,"played":0}
    assert by_id[2]["verified"] is False
    assert data["provisional"]


def test_never_infer_zero_points_for_promoted_team_or_relegation():
    data=compute_promedios([game(1,2026,3,1,0,0)],TEAMS,{3})
    row=data["rows"][0]
    assert row["points"]==1 and row["played"]==1
    assert row["seasons"]["2024"]["points"] is None
    assert row["seasons"]["2025"]["points"] is None
    assert row["missing_seasons"]==[2024,2025]
    assert "relegated" not in row and "descenso" not in row


def test_reference_csv_json_validation_requires_official_url_and_no_duplicate_ids():
    sample={"season":2026,"source_url":
            "https://www.ligaprofesional.ar/torneo-clausura-mercado-libre-2026/",
            "captured_at":"2026-10-17T19:00:00-03:00",
            "rows":[{"team_id":1,"points":17,"played":12}]}
    records,when,url=parse_reference(sample)
    assert records==[{"team_id":1,"points":17,"played":12}]
    with pytest.raises(ValueError):
        parse_reference({**sample,"source_url":"https://fake-lpf.com/pro"})
    with pytest.raises(ValueError):
        parse_reference({**sample,"rows":sample["rows"]*2})
    with pytest.raises(ValueError):
        parse_reference({**sample,"rows":[{"team_id":1,"points":40,"played":12}]})


def test_api_promedios_queries_persisted_fixtures_only(db,monkeypatch):
    fake=replace(main.settings, mode="api", league_ids=(128,), league_scope="all")
    monkeypatch.setattr(main,"settings",fake)
    league(db)
    year2024=fixture(id=122,status="FT",goals={"home":2,"away":0})
    year2024["league"]["season"]=2024
    year2024["league"]["round"]="Regular Season - 1"
    year2024["fixture"]["date"]="2024-09-01T20:00:00+00:00"
    year2024["league"]["id"]=128
    year2024["league"]["round"]="Regular Season - 1"
    year2026=fixture(id=126,status="FT",goals={"home":0,"away":0})
    year2026["league"]["round"]="Apertura - 1"
    save_fixtures(db,[year2024,year2026],[128])
    db.commit()
    with TestClient(main.app) as client:
        response=client.get("/api/leagues/128/promedios?season=2026")
        assert response.status_code==200, response.text
        obj=response.json()
    assert obj["data"]["matches_used"]==2
    assert obj["data"]["provisional"] is True
    assert obj["meta"]["provider"]=="API-Football"
    assert obj["data"]["reference_count"]==0


def test_promedios_page_is_connected_and_mobile_scroll_safe():
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    view=(root/"frontend/src/argentina-promedios.tsx").read_text(encoding="utf-8")
    css=(root/"frontend/src/style.css").read_text(encoding="utf-8")
    assert "/api/leagues/128/promedios?season=2026" in view
    assert "no oficial" in view and "no determina descensos" in view
    assert "promedios-table" in view and 'role="region"' in view
    assert ".promedios-table table" in css
    assert "overflow-x:auto" in css
    assert "liga" in view.lower()
