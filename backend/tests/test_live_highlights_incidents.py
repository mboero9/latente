"""Live highlights expose verified incidents only, never inferred cards/goals."""
from pathlib import Path

from app.live_incidents import compact_live_incidents

ROOT = Path(__file__).resolve().parents[2]


def test_compact_events_exclude_invalid_or_unconfirmed_goals():
    records = [
        {"type": "Goal", "detail": "Normal Goal", "team_id": 11,
         "minute": 14, "extra": None, "player": "Jugador A"},
        {"type": "Goal", "detail": "Missed Penalty", "team_id": 11,
         "minute": 17, "player": "Jugador B"},
        {"type": "Var", "detail": "Goal cancelled", "team_id": 12,
         "minute": 20, "player": "Jugador C"},
        {"type": "Card", "detail": "Yellow Card", "team_id": 12,
         "minute": 25, "player": "Jugador D"},
        {"type": "Card", "detail": "Second Yellow card", "team_id": 11,
         "minute": 30, "player": "Jugador E"},
        {"type": "Card", "detail": "Red Card", "team_id": 12,
         "minute": 47, "extra": 3, "player": "Jugador F"},
        {"type": "Goal", "detail": "Own Goal", "team_id": 12,
         "minute": 49, "player": "Jugador G"},
        {"type": "Subst", "detail": "Substitution", "team_id": 11},
        {"type": "Goal", "detail": "Disallowed goal", "team_id": 11,
         "minute": 50, "player": "Jugador H"},
        {"type": "Goal", "detail": "Normal Goal", "team_id": "bad"},
    ]
    data = compact_live_incidents(records)
    assert [row["kind"] for row in data] == ["goal", "yellow", "red", "red", "goal"]
    assert data[0]["minute"] == 14
    assert data[3]["extra"] == 3
    assert data[4]["own_goal"] is True
    assert data[4]["penalty"] is False


def test_empty_event_snapshot_is_not_fabricated():
    assert compact_live_incidents([]) == []
    assert compact_live_incidents(None) == []
    assert compact_live_incidents([{"type": "Card", "detail": "Unknown Card", "team_id": 2}]) == []


def test_compact_read_endpoint_uses_postgres_only():
    main = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    method = main.split('@app.get("/api/fixtures/live/incidents")', 1)[1].split(
        '@app.get(', 1)[0]
    assert "select(FixtureDetails, Fixture)" in method
    assert "Fixture.status.in_(LIVE)" in method
    assert "limit(300)" in method
    assert "client.get(" not in method
    assert "settings.accepts_league" not in method  # server-side scope check below
    assert "Fixture.league_id.in_(settings.league_ids)" in method


def test_live_view_prioritizes_clubs_and_shows_event_strip():
    view = (ROOT / "frontend/src/main.tsx").read_text(encoding="utf-8")
    strip = (ROOT / "frontend/src/live-incidents.tsx").read_text(encoding="utf-8")
    assert "Destacados en vivo" in view
    assert "focusPriority(b) - focusPriority(a)" in view
    assert "highlightedIds = new Set" in view
    assert "live ? 300 : 150" in view
    assert '"/api/fixtures/live/incidents", 15000' in view
    assert "LiveIncidentStrip" in view
    assert "⚽" in strip and "🟨" in strip and "🟥" in strip
    assert "Incidencias pendientes del proveedor" in strip
