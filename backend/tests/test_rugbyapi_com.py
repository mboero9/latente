"""rugbyAPI.com world coverage and quota behavior without real API credentials."""
from datetime import datetime, timezone
from pathlib import Path
from app import rugbyapi_com, rugby_api

ROOT=Path(__file__).resolve().parents[2]


def test_verified_competitions_and_explicit_country_exclusions():
    rows=[
        {"id":"cp_3HY2BK5","name":"Autumn Nations Series","region":"International","seasons":3},
        {"id":"cp_2FFF9Z7","name":"Currie Cup","region":"South Africa","seasons":16},
        {"id":"cp_0JH8S46","name":"Major League Rugby","region":"USA","seasons":8},
    ]
    items=rugbyapi_com.catalogue(rows)
    assert {x["slug"] for x in items}=={"autumn-series","currie-cup","mlr"}
    assert all(x["competition_id"].startswith("cp_") for x in items)
    assert all(c[0] not in {"japan","chile","uruguay"} for c in rugby_api.COMPETITIONS)
    with __import__("app.db",fromlist=["session_scope"]).session_scope() as db:
        pass
    assert "npc-nz" in rugby_api.BY_SLUG
    assert "urba" in rugby_api.BY_SLUG
    assert "europe-championship" in rugby_api.BY_SLUG


def test_match_and_season_mapping_uses_provider_ids():
    sample=[{"id":"mt_13YSBTS","competition":{"id":"cp_2FFF9Z7"},
             "_latente_slug":"currie-cup","season":{"id":"ss_1VSX6S8"},
             "kickoff_utc":"2026-10-15T17:00:00Z","status":"finished",
             "home":{"name":"Pumas","score":28},"away":{"name":"Bulls","score":17}}]
    matches,seasons=rugbyapi_com.match_rows(sample)
    assert len(matches)==1
    assert matches[("currie-cup",2026,"mt_13YSBTS")]["home_score"]==28
    assert seasons[("currie-cup",2026)]=="ss_1VSX6S8"


def test_standings_retains_real_bonus_points():
    rows=[{"team":{"name":"Stormers","id":"tm_123"},"pos":1,"p":12,
           "w":9,"d":1,"l":2,"pts":48,"bp":8,"pd":95,"pf":320,"pa":225}]
    parsed=rugbyapi_com.tables(rows)
    assert parsed[0]["points"]==48
    assert parsed[0]["bonus"]==8
    assert parsed[0]["difference"]==95
    assert parsed[0]["played"]==12
    assert rugbyapi_com.tables([{"team":{"name":"Team"},"pos":1}])==[]


def test_no_key_results_in_no_remote_calls(monkeypatch):
    monkeypatch.delenv("RUGBYAPI_COM_KEY",raising=False)
    invoked=[]
    result=rugbyapi_com.sync_once(fetch=lambda *a:invoked.append(a))
    assert not invoked
    assert "RUGBYAPI_COM_KEY not configured" in result["unavailable"]


def test_home_country_override_and_argentina_independent_card():
    home=(ROOT/"frontend/src/rugby-home-tables.tsx").read_text()
    main=(ROOT/"frontend/src/main.tsx").read_text()
    assert '<MiniRugbyTable slug="urba" title="Argentina · URBA Top 12"/>' in home
    assert 'slug:"currie-cup"' in home
    assert 'slug:"npc-nz"' in home
    assert '<RugbyHomeTables/>' in main
    assert 'País sugerido por idioma o zona horaria' in home
    assert 'slug:"japan"' not in home
    assert 'slug:"chile"' not in home
    assert 'slug:"uruguay"' not in home
