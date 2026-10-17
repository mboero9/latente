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
