"""TheSportsDB has public Rugby Union fixtures but free coverage is limited."""
from datetime import datetime,timezone
from app import thesportsdb_rugby, rugby_api
from app.db import session_scope
from app.models import SportSnapshot

def events(year):
    return [
      {"idEvent":"123","strHomeTeam":"Toulouse","strAwayTeam":"Clermont",
       "dateEvent":f"{year}-10-18","strTime":"18:00:00",
       "strHomeTeamBadge":"https://www.thesportsdb.com/images/media/team/badge/a.png",
       "strAwayTeamBadge":None,"intHomeScore":None,"intAwayScore":None,
       "strStatus":"NS"},
      {"idEvent":"124","strHomeTeam":"Bayonne","strAwayTeam":"Stade Français",
       "dateEvent":f"{year}-10-04","strTime":"20:00:00",
       "intHomeScore":"20","intAwayScore":"14","strStatus":"FT"},
      {"idEvent":"125","strHomeTeam":"Match Outside Year","strAwayTeam":"Invalid",
       "dateEvent":f"{year-1}-12-04"}
    ]

def test_top14_current_year_calendar_from_verified_league_identifier():
    year=datetime.now(timezone.utc).year
    queried=[]
    def get(params):
        queried.append(params)
        return {"events":events(year)}
    normalized=thesportsdb_rugby.fetch("top-14",year,get=get)
    assert queried==[{"id":4430,"s":f"{year-1}-{year}"},
                     {"id":4430,"s":f"{year}-{year+1}"}]
    assert len(normalized)==2
    assert normalized[0]["completed"] is True
    assert normalized[1]["completed"] is False
    assert normalized[1]["home_logo"].startswith("https://www.thesportsdb.com/")
    assert normalized[1]["id"]=="tsdb-123"

def test_the_sportsdb_rejects_outside_logo_domain_and_bad_events():
    year=datetime.now(timezone.utc).year
    data=events(year)[:1]
    data[0]["strHomeTeamBadge"]="http://untrusted.example/badge.png"
    rows=thesportsdb_rugby.normalize(data,year)
    assert rows[0]["home_logo"] is None

def test_sportsdb_cron_saves_fixture_without_creating_fake_official_table():
    year=datetime.now(timezone.utc).year
    def mocked(slug,year):
        return thesportsdb_rugby.normalize(events(year),year)
    audit=rugby_api.sync_sportsdb_once(max_leagues=1,fetch=mocked)
    assert audit["attempted"]==["top-14"]
    assert audit["updated"]==["top-14"]
    with session_scope() as s:
        record=s.get(SportSnapshot,("rugby","thesportsdb_games",f"top-14:{year}"))
        assert record.provider=="thesportsdb"
        assert record.source_count==2
    data=rugby_api.read_competition("top-14",year)
    assert data["available"]
    assert "TheSportsDB" in data["provider"]
    assert len(data["games"])==2
    assert data["official"]==[]
