"""Clausura-first navigation and real five-game form in live Argentine matches."""
from datetime import timedelta
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.db import session_scope
from app.live_form import form_symbol, recent_team_form
from app.models import utcnow
from app.ingest import save_fixtures
from test_application import fixture, league

ROOT = Path(__file__).resolve().parents[2]


def test_form_outcomes_never_guess_missing_goals():
    assert [form_symbol(a,b) for a,b in [(2,1),(1,1),(0,3),(None,2),(2,None)]] == [
        "W","D","L",None,None
    ]


def test_last_five_finished_matches_from_one_batched_db_query():
    now=utcnow()
    with session_scope() as db:
        league(db)
        raw=[]
        for idx, (score_a,score_b) in enumerate([(2,1),(0,1),(0,0),(3,1),(0,2),(1,0)],1):
            raw.append(fixture(idx,"FT",now-timedelta(days=12-idx),
                               {"home":score_a,"away":score_b}))
        raw.append(fixture(8,"NS",now-timedelta(days=1),
                           {"home":7,"away":1}))
        raw.append(fixture(9,"1H",now,
                           {"home":5,"away":0}))
        raw.append(fixture(10,"FT",now+timedelta(days=3),
                           {"home":9,"away":0}))
        save_fixtures(db,raw,[128])
    with session_scope() as db:
        rows=recent_team_form(db,"api",{1,2},now)
        # The oldest of six ended games is excluded.
        assert rows[1]==["L","D","W","L","W"]
        assert rows[2]==["W","D","L","W","L"]
        assert recent_team_form(db,"api",set(),now)=={}


def test_live_form_endpoint_only_uses_saved_matches_not_vendor(monkeypatch):
    monkeypatch.setattr(main,"settings",
                        replace(main.settings,mode="api",league_scope="all"))
    now=utcnow()
    with session_scope() as db:
        league(db)
        save_fixtures(db,[
            fixture(1,"FT",now-timedelta(days=2),{"home":2,"away":1}),
            fixture(2,"1H",now,{"home":1,"away":0}),
            fixture(3,"NS",now+timedelta(days=1)),
        ],[128])
    with TestClient(main.app) as client:
        response=client.get("/api/fixtures/live/form")
        assert response.status_code==200
        data=response.json()["data"]
        assert len(data)==1
        assert data[0]["fixture_id"]==2
        assert data[0]["home"]==["W"]
        assert data[0]["away"]==["L"]
        assert data[0]["sample_type"]=="five_finished_matches"


def test_current_clausura_is_first_not_fake_api_competition():
    page=(ROOT/"frontend/src/main.tsx").read_text()
    assert "CURRENT_CLAUSURA_2026" in page
    assert 'Torneo Clausura 2026 · Liga Profesional' in page
    assert 'id:128,label:CURRENT_CLAUSURA_2026?' in page
    assert 'LATENTE_PRIMARY_LEAGUES' in page
    assert 'argentinaLeagueName(rows[0].league)' in page
    assert 'argentinaLeagueName(l)' in page
    # Native provider league id reused; no made-up provider Clausura ID.
    assert 'id:130,label:"🏆 Copa Argentina"' in page


def test_live_graph_requires_genuine_live_market_and_age_region():
    mainview=(ROOT/"frontend/src/main.tsx").read_text()
    odds=(ROOT/"frontend/src/match-odds.tsx").read_text()
    form=(ROOT/"frontend/src/live-form.tsx").read_text()
    stylesheet=(ROOT/"frontend/src/style.css").read_text()
    api=(ROOT/"backend/app/live_form.py").read_text()
    assert '"/api/fixtures/live/form", 60000' in mainview
    assert "formByFixture.get(m.id)" in mainview
    assert "active && <LiveRecentForm" in mainview
    assert 'visible={geoCountry==="AR"&&Boolean(audience?.adult)}' in mainview
    assert "if (!visible || !entry) return null" in odds
    assert "const normalized=values.map(n=>n/total*100)" in odds
    assert "No es un pronóstico" in odds
    assert 'class="live-form-panel"' in form
    assert "form={entry.home||[]}" in form and "form={entry.away||[]}" in form
    assert ".live-form-grid" in stylesheet
    assert "grid-template-columns:1fr" in stylesheet
    assert "union_all(left, right)" in api
    assert "row_number().over" in api
    assert "client.get(" not in api
