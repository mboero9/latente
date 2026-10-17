"""The home spotlight must not hide City or other prominent live football
fixtures behind the first 300 kickoff-ordered matches."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_spotlight_candidates_are_database_only_and_unpaginated():
    source = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    block = source.split('@app.get("/api/fixtures/focus")', 1)[1].split(
        '@app.get("/api/fixtures/live/incidents")', 1)[0]
    assert "FOCUS_LEAGUE_ORDER" in source
    assert "39" in source.split("FOCUS_LEAGUE_ORDER =", 1)[1].split(")", 1)[0]
    assert "Fixture.status.in_(LIVE)" in block
    assert "Fixture.league_id.in_(settings.league_ids)" in block
    assert "Fixture.kickoff <= now + timedelta(hours=36)" in block
    assert ".order_by(priority, Fixture.kickoff.desc(), Fixture.id)" in block
    assert ".limit(160)" in block
    assert "match_payload(s, live_rows)" in block
    assert "client.get" not in block  # no API-Football call per visitor


def test_spotlight_uses_candidates_not_first_300_chronologically():
    frontend = (ROOT / "frontend/src/main.tsx").read_text(encoding="utf-8")
    assert '"/api/fixtures/focus", 15000' in frontend
    assert "focusCandidates?.data?.live || inPlay" in frontend
    assert "focusCandidates?.data?.upcoming || []" in frontend
    assert '/api/fixtures?date=${day}&live=true&limit=300' not in frontend
    assert "const selection = active.length ? active : next;" in frontend
    assert "Number.isFinite(new Date(m.kickoff).getTime())" in frontend


def test_premier_league_clubs_receive_high_editorial_priority():
    frontend = (ROOT / "frontend/src/main.tsx").read_text(encoding="utf-8")
    assert "39: 1380" in frontend
    assert "2: 1420" in frontend
    assert '"manchester city"' in frontend
    assert '"man city"' in frontend
    assert '"man. city"' in frontend
    assert 'score += 135' in frontend
    assert "if (m.stale) score -= 120" in frontend
