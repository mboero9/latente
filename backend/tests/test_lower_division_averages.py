"""Argentine lower leagues: points-per-game != relegation averages."""
from dataclasses import dataclass
from pathlib import Path

from app.lower_division_averages import lower_division_key, performance_average


@dataclass
class LeagueInfo:
    name: str
    country: str = "Argentina"


@dataclass
class Row:
    group: str
    team_id: int
    points: int
    played: int
    won: int=0
    drawn: int=0
    lost: int=0


def test_league_detection_never_matches_foreign_and_futsal_leagues():
    assert lower_division_key("Primera Nacional","Argentina")=="nacional"
    assert lower_division_key("Primera B Metropolitana","Argentina")=="b"
    assert lower_division_key("Primera C","Argentina")=="c"
    assert lower_division_key("Primera D","Argentina")=="d"
    assert lower_division_key("Primera B Metropolitana","Chile") is None
    assert lower_division_key("Primera B Futsal","Argentina") is None


def test_per_group_ppg_uses_only_persisted_standings():
    teams={
        1:{"id":1,"name":"Almirante Brown"},
        2:{"id":2,"name":"Ferro"},
        3:{"id":3,"name":"Temperley"},
    }
    records=[
        Row("Zona A",1,24,12,7,3,2),
        Row("Zona A",2,21,12,6,3,3),
        Row("Zona B",3,19,10,6,1,3),
        Row("Zona A",999,99,10), # No verified team in DB
        Row("Zona A",3,0,0), # No games -> omit
    ]
    result=performance_average(records,teams,"nacional",2026)
    assert len(result["groups"])==2
    a=result["groups"][0]["rows"]
    assert [row["team_id"] for row in a]==[1,2]
    assert a[0]["average"]==2.0
    assert a[1]["average"]==1.75
    assert "descenso" in result["note"] and result["matches_available"]
    assert all("relegation" not in row for group in result["groups"] for row in group["rows"])


def test_invalid_or_unknown_values_never_manufacture_average():
    teams={1:{"id":1,"name":"Club A"}}
    matches=[Row("General",1,4,0),Row("General",1,-4,2),Row("General",1,20,True)]
    data=performance_average(matches,teams,"b",2026)
    assert not data["groups"]
    assert not data["matches_available"]


def test_primera_d_is_history_only():
    result=performance_average([],{},"d",2026)
    assert result["historic_only"]
    assert result["groups"]==[]
    assert not result["matches_available"]
    assert "2026" in result["note"]


def test_ascenso_tabs_api_and_responsive_table():
    root=Path(__file__).resolve().parents[2]
    ui=(root/"frontend/src/main.tsx").read_text()
    page=(root/"frontend/src/lower-league-promedios.tsx").read_text()
    backend=(root/"backend/app/main.py").read_text()
    assert 'lowerLeagueCode, LowerLeaguePromedios' in ui
    assert 'lowerLeagueCode(league) ? [["promedios", "PTS/PJ · Promedios"]]' in ui
    assert '<LowerLeaguePromedios league={league}' in ui
    assert '@app.get("/api/leagues/{league_id}/points-average")' in backend
    assert "season == year" in backend
    assert "select(Standing)" in backend
    assert 'role="region"' in page
    assert 'class="table-scroll promedios-table"' in page
    assert "No es una tabla oficial de descenso" in page
