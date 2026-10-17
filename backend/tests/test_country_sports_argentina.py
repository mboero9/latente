"""Country-scoped FIBA, Argentina volleyball and handball coverage."""
from pathlib import Path
from fastapi.testclient import TestClient

from app import main
from app.db import session_scope
from app.models import SportSnapshot, utcnow
from app.sport_competitions import ARGENTINE_LEAGUES, build_competitions, display_country
from app.sports_scheduler import automatic_targets

ROOT=Path(__file__).resolve().parents[2]


def test_argentine_federation_leagues_always_listed_without_fake_results():
    expected={"basketball":2,"volleyball":4,"handball":4}
    for sport,n in expected.items():
        assert len(ARGENTINE_LEAGUES[sport])==n
        items=build_competitions(sport,[])
        assert len(items)==n
        assert all(row["country"]=="Argentina" for row in items)
        assert all(row["official_url"].startswith("https://") for row in items)
        assert all(row["provider_id"] is None for row in items)
        assert all(not row["has_imported_data"] for row in items)


def test_country_separation_prefers_argentina_and_preserves_verified_ids():
    catalogue=[
        {"id":10,"name":"Liga Nacional","country":"Argentina","seasons":[2025,2026]},
        {"id":11,"name":"Liga Nacional","country":"Brazil","seasons":[2026]},
        {"id":12,"name":"Liga ACB","country":"Spain","seasons":[2026]},
        {"id":13,"name":"Basketball Champions League","country":"World","seasons":[2026]},
    ]
    rows=build_competitions("basketball",catalogue,[
        {"league_id":10,"id":900}, {"league_id":12,"id":901}
    ],["13:2026"])
    argentina=[r for r in rows if r["country"]=="Argentina"]
    assert argentina[0]["provider_id"]==10
    assert argentina[0]["has_imported_data"]
    assert argentina[0]["seasons"]==[2026,2025]
    assert any(r["country"]=="Brasil" and r["provider_id"]==11 for r in rows)
    assert any(r["country"]=="España" and r["provider_id"]==12 for r in rows)
    assert any(r["country"]=="Internacional" and r["provider_id"]==13 for r in rows)
    assert rows[0]["country"]=="Argentina"
    assert display_country("ARGENTINA")=="Argentina"


def test_only_unique_exact_country_matches_receive_provider_ids():
    catalogue=[
        {"id":101,"name":"Liga Argentina Femenina","country":"Argentina","seasons":[2025,2026]},
        {"id":102,"name":"Liga Argentina Femenina","country":"Argentina","seasons":[2026]},
        {"id":103,"name":"Superliga Argentina","country":"Italy","seasons":[2026]},
    ]
    rows=build_competitions("volleyball",catalogue)
    female=next(r for r in rows if "Femenina (LAF)" in r["name"])
    assert female["provider_id"] is None
    assert not female["has_imported_data"]
    superliga=next(r for r in rows if "Superliga Argentina de Vóley" in r["name"])
    assert superliga["provider_id"] is None


def test_autosync_prefers_only_country_verified_argentina_catalogue():
    data=[
        {"id":40,"name":"Liga Nacional","country":"Brazil","seasons":[2026]},
        {"id":41,"name":"Liga Nacional","country":"Argentina","seasons":[2026]},
        {"id":42,"name":"Liga Argentina","country":"Argentina","seasons":[2026]},
        {"id":43,"name":"Euroleague","country":"Europe","seasons":[2026]},
    ]
    result=automatic_targets("basketball",data,2026)
    assert [r["league"] for r in result]==[41,42,43]
    assert all(r["league"]!=40 for r in result)
    volleyball=automatic_targets("volleyball",[
        {"id":24,"name":"Superliga Argentina","country":"Argentina","seasons":[2026]},
        {"id":25,"name":"Superlega","country":"Italy","seasons":[2026]},
    ],2026)
    assert [r["league"] for r in volleyball]==[24,25]


def test_api_country_catalogue_reads_postgres_not_vendor(monkeypatch):
    with session_scope() as db:
        row=SportSnapshot(sport="basketball",dataset="leagues",ref="catalog",
            provider="api_sports",
            data=[{"id":5001,"name":"Liga Nacional","country":"Argentina",
                   "seasons":[2026]}],
            source_count=1,updated_at=utcnow(),note="Proveedor")
        db.merge(row)
    with TestClient(main.app) as client:
        r=client.get("/api/sports/basketball/competitions")
        assert r.status_code==200
        data=r.json()["data"]
        national=next(item for item in data if "LNB" in item["name"])
        assert national["provider_id"]==5001
        assert not national["has_imported_data"]
        assert client.get("/api/sports/invalid/competitions").status_code==404


def test_frontend_scopes_results_and_tables_by_selected_country():
    page=(ROOT/"frontend/src/other-sports.tsx").read_text()
    standings=(ROOT/"frontend/src/sports-standings.tsx").read_text()
    explorer=(ROOT/"frontend/src/sport-country-explorer.tsx").read_text()
    assert "SportCountryExplorer" in page
    assert "countryForGame(game,competitions)" in page
    assert "matchesCompetition(game,competition,competitions)" in page
    assert "const results = filtered.filter" in page
    assert "for (const game of filtered)" in page
    assert "leagueSelection={multiCountry?competition" in page
    assert 'country==="all"&&leagueSelection==="all"' in standings
    assert "Argentina primero" in explorer
    assert "Fuente federativa" in explorer
    assert "has_imported_data" in explorer
    assert "grid-template-columns:minmax(0,1fr)" in (ROOT/"frontend/src/style.css").read_text()
