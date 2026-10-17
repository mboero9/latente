"""Regression checks: league identity, verified UAR 2026 rosters and schedule."""
from pathlib import Path

from app.rugby_clubs import (
    URBA_2026, INTERIOR_A_2026, edition_clubs, published_schedule, source_url,
)
from app.rugby_api import BY_SLUG, resolve

ROOT = Path(__file__).resolve().parents[2]


def test_argentinian_top14_and_french_top14_are_separate():
    urba = resolve([
        {"id": 21, "name": "Top 12", "country": {"name": "Argentina"}, "seasons": [{"season": 2025}]},
        {"id": 44, "name": "Top 14", "country": {"name": "France"}, "seasons": [{"season": 2026}]},
    ])
    by_slug = {row["slug"]: row for row in urba}
    assert by_slug["urba"]["league_id"] == 21
    assert by_slug["top-14"]["league_id"] == 44
    assert "Top 14" in BY_SLUG["urba"][0]


def test_urba_2026_clubs_only_for_confirmed_edition():
    clubs = edition_clubs("urba", 2026)
    assert len(clubs) == 14 == len(URBA_2026)
    assert {x["team"] for x in clubs} == set(URBA_2026)
    assert edition_clubs("urba", 2025) == []
    assert source_url("urba") == "https://urba.org.ar/fixture"


def test_uar_interior_entry_lists_are_not_official_standings():
    clubs = edition_clubs("interior-a", 2026)
    assert len(clubs) == 16 == sum(len(v) for v in INTERIOR_A_2026.values())
    assert len(edition_clubs("interior-b", 2026)) == 8
    assert edition_clubs("interior-b", 2027) == []


def test_uar_group_stage_schedule_has_no_fabricated_scores():
    fixtures = published_schedule("interior-a", 2026)
    assert len(fixtures) == 48
    assert len({(row["round"], row["home"], row["away"]) for row in fixtures}) == 48
    assert {row["round"] for row in fixtures} == set(range(1, 7))
    assert all("score" not in row and "completed" not in row for row in fixtures)
    assert published_schedule("interior-a", 2025) == []


def test_frontend_preserves_source_disclaimers():
    interface = (ROOT / "frontend/src/rugby-hub.tsx").read_text(encoding="utf-8")
    assert "published_schedule" in interface
    assert "verified_clubs" in interface
    assert "sin marcadores" in interface
    assert "Posiciones oficiales" in interface


def test_navigation_drag_does_not_open_links():
    nav = (ROOT / "frontend/src/nav-rail.tsx").read_text(encoding="utf-8")
    assert "onPointerMove" in nav
    assert "onClickCapture" in nav
    assert "blockDraggedClick" in nav
    assert 'event.pointerType !== "mouse"' in nav


def test_verified_european_and_premiership_clubs_for_2026_27():
    from app.rugby_clubs import TOP14_FR_2026_27, PREM_2026_27
    from app.rugby_clubs import CHAMPIONS_CUP_2026_27, CHALLENGE_CUP_2026_27
    assert len(edition_clubs("top-14", 2026)) == len(TOP14_FR_2026_27) == 14
    assert len(edition_clubs("premiership", 2026)) == len(PREM_2026_27) == 10
    assert len(edition_clubs("champions", 2026)) == 24
    assert len(edition_clubs("challenge-cup", 2026)) == 18
    assert set(CHAMPIONS_CUP_2026_27) == {"Pool 1", "Pool 2", "Pool 3", "Pool 4"}
    assert set(CHALLENGE_CUP_2026_27) == {"Pool 1", "Pool 2", "Pool 3"}
    assert edition_clubs("top-14", 2025) == []
    assert edition_clubs("champions", 2025) == []
    assert source_url("champions").startswith("https://www.epcrugby.com/")


def test_all_fourteen_urba_clubs_have_verified_public_urba_crests():
    from app.rugby_clubs import URBA_TOP14_OFFICIAL_LOGOS
    clubs = edition_clubs("urba", 2026)
    assert len(clubs) == 14
    assert set(URBA_TOP14_OFFICIAL_LOGOS) == set(URBA_2026)
    for club in clubs:
        assert club["logo"] == ("https://api.urba.org.ar/img/clubs/" +
                                URBA_TOP14_OFFICIAL_LOGOS[club["team"]])
        assert club["logo"].endswith(".png")


def test_additional_2026_urba_and_regional_leagues_have_official_sources(monkeypatch):
    from app.rugby_clubs import CORDOBA_TOP10_2026, LITORAL_TOP10_2026
    import app.rugby_api as rugby_api
    monkeypatch.setattr(rugby_api, "_snapshot", lambda *args: None)
    public_catalog = rugby_api.public_catalog
    slugs = {
        "urba-primera-a", "urba-primera-b", "urba-primera-c",
        "urba-segunda", "urba-tercera", "urba-desarrollo",
        "litoral-top10", "litoral-segunda", "cordoba-top10", "cordoba-super9",
        "noa-regional-a", "noa-regional-b", "tucumano-anual",
    }
    catalog = {row["slug"]: row for row in public_catalog()}
    for slug in slugs:
        assert slug in catalog
        assert 2026 in catalog[slug]["seasons"]
        assert catalog[slug]["official_url"].startswith("https://")
    assert len(edition_clubs("cordoba-top10", 2026)) == len(CORDOBA_TOP10_2026) == 10
    assert len(edition_clubs("litoral-top10", 2026)) == len(LITORAL_TOP10_2026) == 10
    assert not edition_clubs("litoral-top10", 2025)
    assert not edition_clubs("urba-primera-a", 2026)  # Don't invent club rosters


def test_cached_fixture_logo_matches_verified_club_name_only():
    from app.rugby_api import attach_club_logos
    clubs = [
        {"team": "CUBA", "group": "URBA"},
        {"team": "Belgrano Athletic", "group": "URBA"},
        {"team": "SIC", "group": "URBA"},
        {"team": "Al Ahly", "group": "Unrelated"},
    ]
    matches = [
        {"home": "CUBA", "home_logo": "https://a.espncdn.com/cuba.png",
         "away": "Belgrano AC", "away_logo": "https://a.espncdn.com/belgrano.png"},
    ]
    standings = [{"team": "SIC", "logo": "https://a.espncdn.com/sic.png"}]
    rows = {row["team"]: row for row in attach_club_logos(clubs, matches, standings)}
    assert rows["CUBA"]["logo"] == "https://a.espncdn.com/cuba.png"
    assert rows["Belgrano Athletic"]["logo"] == "https://a.espncdn.com/belgrano.png"
    assert rows["SIC"]["logo"] == "https://a.espncdn.com/sic.png"
    assert rows["Al Ahly"]["logo"] is None


def test_frontend_renders_logo_directly_and_no_fictitious_scheduled_zero_score():
    view = (ROOT / "frontend/src/rugby-hub.tsx").read_text()
    marks = (ROOT / "frontend/src/team-mark.tsx").read_text()
    assert 'logo={club.logo}' in view
    assert '"api.urba.org.ar"' in marks
    assert 'm.completed || /in progress' in view
    for file in ("frontend/public/_headers", "deploy/railway/nginx.conf.template",
                 "deploy/nginx/nginx.conf"):
        assert "https://api.urba.org.ar" in (ROOT / file).read_text()
