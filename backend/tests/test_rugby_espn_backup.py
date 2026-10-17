"""Rugby backup is cron-only, source-attributed and never invents standings."""
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app import rugby_api, main
from app.db import session_scope
from app.models import SportSnapshot


def test_espn_backup_populates_real_top14_games_and_verified_table(monkeypatch):
    # Isolate test from the editorial priority order (URBA goes first).
    monkeypatch.setattr(rugby_api, 'ESPN_PRIORITY', ('top-14', 'urba'))
    now = datetime.now(timezone.utc).year
    calls = []
    def fake(slug, season):
        calls.append((slug,season))
        return {
            "games": [{
                "id": "espn-567", "date": f"{now}-11-10T15:00:00Z",
                "home": "Toulouse", "away": "Bayonne",
                "home_logo": "https://a.espncdn.com/i/teamlogos/rugby/teams/500/123.png",
                "away_logo": None, "home_score": None, "away_score": None,
                "status": "Scheduled", "completed": False,
            }],
            "official": [{
                "id": "123", "name": "Toulouse", "group": "General",
                "logo": "https://a.espncdn.com/i/teamlogos/rugby/teams/500/123.png",
                "rank": 1, "points": 35, "wins": 8, "losses": 1,
            }]
        }
    result = rugby_api.sync_espn_once(max_leagues=1, fetch=fake)
    assert result["attempted"] == ["top-14"]
    assert calls == [("top-14", now)]
    public = rugby_api.read_competition("top-14", now)
    assert public["available"]
    assert public["games"][0]["home"] == "Toulouse"
    assert public["official"][0]["points"] == 35
    assert "ESPN" in public["provider"]
    assert now in public["seasons"]
    # Valid cached rows are read without requesting an external site on GET.
    with TestClient(main.app) as client:
        answer = client.get(f"/api/rugby/top-14?season={now}")
        assert answer.status_code == 200
        assert answer.json()["data"]["official"][0]["team"] == "Toulouse"
    # No repeated ESPN requests every cron while backup is fresh.
    second = rugby_api.sync_espn_once(max_leagues=1, fetch=fake)
    assert second["attempted"] != ["top-14"]


def test_espn_empty_or_non_table_rows_do_not_invent_league_points():
    invalid = [{"name": "Team without rank or points", "wins": 3}]
    assert rugby_api.espn_standings(invalid) == []
    assert rugby_api.espn_standings([{"name": "Test", "rank": 1,
                                     "points": 12}])[0]["points"] == 12


def test_every_sport_has_provider_logo_or_clear_fallback():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    mark = (root/"frontend/src/team-mark.tsx").read_text()
    assert "media.api-sports.io" in mark
    assert "a.espncdn.com" in mark
    assert 'title={url&&!bad?name:' in mark
    for path in ("rugby-hub", "scoreboards", "other-sports", "sports-standings", "reference-sports"):
        source=(root/f"frontend/src/{path}.tsx").read_text()
        assert 'from "./team-mark"' in source
        assert "<TeamMark" in source


def test_rugby_api_labels_espn_source_and_keeps_top14_selectable():
    from pathlib import Path
    source=(Path(__file__).resolve().parents[2]/"frontend/src/rugby-hub.tsx").read_text()
    assert 'data?.provider || "API-Rugby / ESPN"' in source
    assert 'slug:"top-14"' in source
