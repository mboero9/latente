"""Snapshots de eventos y planteles validados; jamás inventar datos faltantes."""
from .models import FixtureDetails, utcnow
from .ingest import upsert


def normalize_events(rows):
    output = []
    for raw in rows[:250]:
        if not isinstance(raw, dict):
            continue
        player = raw.get("player") or {}
        assist = raw.get("assist") or {}
        team = raw.get("team") or {}
        elapsed = raw.get("time") or {}
        if not isinstance(team.get("id"), int):
            continue
        output.append({
            "minute": elapsed.get("elapsed") if isinstance(elapsed.get("elapsed"), int) else None,
            "extra": elapsed.get("extra") if isinstance(elapsed.get("extra"), int) else None,
            "team_id": team["id"],
            "player": str(player.get("name") or "")[:120],
            "assist": str(assist.get("name") or "")[:120] or None,
            "type": str(raw.get("type") or "")[:40],
            "detail": str(raw.get("detail") or "")[:100],
            "comments": str(raw.get("comments") or "")[:200] or None,
        })
    return output


def normalize_lineups(rows):
    output = []
    for raw in rows[:2]:
        if not isinstance(raw, dict):
            continue
        team = raw.get("team") or {}
        if not isinstance(team.get("id"), int):
            continue
        def players(key):
            result = []
            for item in (raw.get(key) or [])[:30]:
                player = item.get("player") or {}
                if player.get("id") is None or not player.get("name"):
                    continue
                result.append({
                    "id": player["id"], "name": str(player["name"])[:130],
                    "number": player.get("number"), "position": player.get("pos"),
                    "grid": player.get("grid"),
                })
            return result
        coach = raw.get("coach") or {}
        output.append({
            "team_id": team["id"],
            "formation": str(raw.get("formation") or "")[:16] or None,
            "coach": str(coach.get("name") or "")[:130] or None,
            "start": players("startXI"),
            "bench": players("substitutes"),
        })
    return output


def normalize_player_ratings(rows):
    output = []
    for team in rows[:2]:
        for entry in (team.get("players") or [])[:35]:
            player = entry.get("player") or {}
            for stats in (entry.get("statistics") or [])[:1]:
                games = stats.get("games") or {}
                try:
                    rating = float(games.get("rating"))
                except (TypeError, ValueError):
                    continue
                if not (0 <= rating <= 10) or not player.get("name") or not player.get("id"):
                    continue
                output.append({
                    "id": player["id"], "name": str(player["name"])[:130],
                    "team_id": (team.get("team") or {}).get("id"), "rating": rating,
                })
    return output


def store_details(s, fixture_id, events, lineups, player_ratings=None):
    # Null representa endpoint aún no consultado; [] representa consultado sin datos.
    old = s.get(FixtureDetails, ("api", fixture_id))
    values = {
        "source": "api", "fixture_id": fixture_id,
        "events": normalize_events(events) if events is not None else (old.events if old else []),
        "lineups": normalize_lineups(lineups) if lineups is not None else (old.lineups if old else []),
        "player_ratings": normalize_player_ratings(player_ratings) if player_ratings is not None else (old.player_ratings if old else []),
        "updated_at": utcnow(),
    }
    upsert(s, FixtureDetails, values)
