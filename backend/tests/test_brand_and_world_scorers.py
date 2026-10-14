"""Preserve the approved Latente wordmark and accurate current Messi club label."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_header_wordmark_has_no_domain_suffix():
    code = (ROOT / "frontend/src/main.tsx").read_text(encoding="utf-8")
    assert '<span class="brand-late">late</span><span class="brand-nte">nte</span><span class="brand-dot">.</span>' in code
    assert 'class="brand-tld"' not in code


def test_messi_inter_miami_badge_and_historical_goals_disclaimer():
    code = (ROOT / "frontend/src/world-scorers.tsx").read_text(encoding="utf-8")
    assert 'club: "Inter Miami CF (actual, 2026)", teamId: 9568' in code
    assert 'club: "Paris Saint-Germain (2023)"' not in code
    assert 'goals: 934' in code
    assert 'goals: 981' in code
    assert 'asOf: "12/10/2026"' in code
    assert "<HistoricalHonours/>" in code
    assert "Cristiano Ronaldo y Lionel Messi tienen corte" in code


def test_international_club_and_country_honours_scope():
    content=(ROOT/"frontend/src/historical-honours.tsx").read_text(encoding="utf-8")
    assert 'name:"Real Madrid"' in content
    assert 'confed:23,world:9' in content
    assert 'name:"Argentina"' in content
    assert 'world:3,continental:16' in content
    assert 'name:"España"' in content
    assert 'world:2,continental:4' in content
    assert 'name:"Brasil"' in content
    assert 'world:5,continental:9' in content
    assert 'region==="all"||n.region===region' in content
    assert "Quedan fuera Confederaciones, Nations League" in content
