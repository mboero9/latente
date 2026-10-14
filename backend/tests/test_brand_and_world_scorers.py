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
    assert 'goals: 803' in code
    assert "Los goles corresponden a ese corte histórico" in code
