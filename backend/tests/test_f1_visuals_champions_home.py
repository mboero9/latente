"""F1 media, current season rankings, and verified historical champions."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone

from app.f1_history import (
    enrich_driver_rows, permitted_photo, _champion_rows, f1_champions,
)

ROOT=Path(__file__).resolve().parents[2]


def test_f1_photos_are_matched_by_unique_exact_surname():
    rows=[
        {"name":"Andrea Kimi Antonelli","family_name":"Antonelli","team":"Mercedes"},
        {"name":"Lewis Hamilton","family_name":"Hamilton","team":"Ferrari"},
        {"name":"Unknown Example","family_name":"Example","team":"Example"},
    ]
    media=[
        {"last_name":"Antonelli","headshot_url":"https://media.formula1.com/images/antonelli.png",
         "team_colour":"00D7B6","team_name":"Mercedes"},
        {"last_name":"Hamilton","headshot_url":"https://media.formula1.com/images/hamilton.png",
         "team_colour":"ED1131"},
    ]
    found=enrich_driver_rows(rows,media)
    assert found[0]["photo"].endswith("/antonelli.png")
    assert found[0]["team_colour"]=="#00D7B6"
    assert found[1]["photo"].endswith("/hamilton.png")
    assert "photo" not in found[2]
    assert found[0]["team"]=="Mercedes"


def test_f1_does_not_accept_wrong_or_ambiguous_portraits():
    assert permitted_photo("http://media.formula1.com/test.png") is None
    assert permitted_photo("https://impostor.formula1.com/test.png") is None
    ambiguous=enrich_driver_rows(
        [{"name":"Leo Smith","family_name":"Smith"}],
        [{"last_name":"Smith","headshot_url":"https://media.formula1.com/a.png"},
         {"last_name":"Smith","headshot_url":"https://media.formula1.com/b.png"}])
    assert "photo" not in ambiguous[0]


def test_champions_filter_unfinished_year_and_constructor_era(monkeypatch):
    import app.f1_history as history
    current=datetime.now(timezone.utc).year
    def mock_get(path,params=None):
        isdrivers="/driverstandings/" in path
        key="DriverStandings" if isdrivers else "ConstructorStandings"
        def row(year,name):
            info=({"givenName":name,"familyName":"Driver","nationality":"British"}
                  if isdrivers else {"name":name,"nationality":"British"})
            return {"season":str(year),key:[
                {"position":"1","points":"105.5","wins":"4",
                 "Driver" if isdrivers else "Constructor":info}]}
        return {"MRData":{"StandingsTable":{"StandingsLists":[
            row(1950,"First"), row(1958,"Second"), row(current-1,"Last"),
            row(current,"Unfinished")]}}}
    monkeypatch.setattr(history,"_get",mock_get)
    pilots=_champion_rows("drivers",current-1)
    clubs=_champion_rows("constructors",current-1)
    assert pilots[0]["year"]==current-1
    assert pilots[-1]["year"]==1950
    assert clubs[-1]["year"]==1958
    assert all(row["year"]<current for row in pilots+clubs)
    assert all(row["points"]==105.5 for row in pilots)


def test_backend_and_frontend_wire_real_f1_features():
    backend=(ROOT/"backend/app/public_sports.py").read_text()
    main=(ROOT/"backend/app/main.py").read_text()
    view=(ROOT/"frontend/src/reference-sports.tsx").read_text()
    home=(ROOT/"frontend/src/main.tsx").read_text()
    styles=(ROOT/"frontend/src/style.css").read_text()
    history=(ROOT/"frontend/src/f1-champions.tsx").read_text()
    media=(ROOT/"frontend/src/f1-media.tsx").read_text()
    assert 'current_driver_media(year)' in backend
    assert 'enrich_driver_rows([' in backend
    assert '@app.get("/api/f1/champions")' in main
    assert "F1Champions" in view and "F1Portrait" in view
    assert "F1TeamLogo" in view and "F1CountryFlag" in view
    assert 'href={link("/sport/f1")}' in home
    assert "f1-home-feature" in styles
    assert '"/api/f1/champions"' in history
    assert "1958" in history
    assert "2026" in media or '"mclaren"' in media
    for p in ("frontend/public/_headers","deploy/railway/nginx.conf.template",
              "deploy/nginx/nginx.conf"):
        c=(ROOT/p).read_text()
        assert "https://media.formula1.com" in c
        assert "https://commons.wikimedia.org" in c
        assert "https://flagcdn.com" in c
        assert "https://www.svgrepo.com" in c
