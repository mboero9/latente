"""Contract tests for normalized public reference feeds (no network)."""
import httpx
from fastapi.testclient import TestClient

from app import public_sports, main


def test_f1_jolpica_normalization(monkeypatch):
    public_sports._CACHE.clear()
    def fake(url, params=None):
        if "driverstandings" in url:
            return {"MRData": {"StandingsTable": {"StandingsLists": [
                {"round": "17", "DriverStandings": [
                    {"position": "1", "points": "340", "wins": "8",
                     "Driver": {"givenName": "Kimi", "familyName": "Antonelli", "nationality": "Italian"},
                     "Constructors": [{"name": "Mercedes", "nationality": "German"}]}
                ]}
            ]}}}
        if "constructorstandings" in url:
            return {"MRData": {"StandingsTable": {"StandingsLists": [
                {"ConstructorStandings": [
                    {"position": "1", "points": "578", "wins": "11",
                     "Constructor": {"name": "Mercedes", "nationality": "German"}}
                ]}
            ]}}}
        return {"MRData": {"RaceTable": {"Races": [
            {"raceName": "Singapore Grand Prix", "date": "2026-10-11",
             "round": "17", "Circuit": {"circuitName": "Marina Bay"},
             "Results": [{"position": "1", "Driver": {"givenName": "Max", "familyName": "Verstappen", "nationality": "Dutch"},
                          "Constructor": {"name": "Red Bull", "nationality": "Austrian"}, "Time": {"time": "1:42:00.785"}}]}
        ]}}}
    monkeypatch.setattr(public_sports, "_get", fake)
    data = public_sports.formula_one(2026)
    assert data["drivers"][0]["points"] == 340
    assert data["constructors"][0]["name"] == "Mercedes"
    assert data["last_race"]["podium"][0]["name"] == "Max Verstappen"
    assert data["drivers"][0]["nationality"] == "Italian"
    assert data["drivers"][0]["team_nationalities"] == ["German"]
    assert data["constructors"][0]["nationality"] == "German"
    assert data["last_race"]["podium"][0]["nationality"] == "Dutch"
    assert data["last_race"]["podium"][0]["team_nationality"] == "Austrian"
    assert data["last_race"]["results"][0]["nationality"] == "Dutch"
    assert data["last_race"]["results"][0]["team_nationality"] == "Austrian"


def test_nba_standings_are_season_scoped(monkeypatch):
    public_sports._CACHE.clear()
    monkeypatch.setattr(public_sports, "_get", lambda url, params=None: {
        "children": [{"name": "Eastern Conference", "standings": {
            "entries": [{"team": {"id": "2", "displayName": "Boston Celtics"},
                         "stats": [{"name": "wins", "value": 61},
                                   {"name": "losses", "value": 21},
                                   {"name": "winPercent", "value": .744}]}]
        }}]
    })
    data = public_sports.nba(2025)
    assert data["rows"][0]["name"] == "Boston Celtics"
    assert data["rows"][0]["wins"] == 61
    assert data["season"] == 2025


def test_public_sports_has_no_guessed_results_if_provider_fails(monkeypatch):
    public_sports._CACHE.clear()
    def fail(url, params=None):
        raise httpx.ConnectError("provider unavailable")
    monkeypatch.setattr(public_sports, "_get", fail)
    assert not public_sports.formula_one(2026)["available"]
    assert not public_sports.cricket("ipl")["available"]


def test_reference_routes_validate_enums(monkeypatch):
    monkeypatch.setattr(main, "meta", lambda *a, **k: {"mode": "api"})
    with TestClient(main.app) as client:
        assert client.get("/api/reference/unknown").status_code == 404
        assert client.get("/api/reference/cricket?competition=not-allowed").status_code == 422
        assert client.get("/api/reference/nba?season=1900").status_code == 422
