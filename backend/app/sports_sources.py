"""Extract and normalize other sports from whitelisted API-Sports hosts.

Only fixture and standings payloads with confirmed coverage are persisted.
No scraping, credentials in logs, or guessed player records.
"""
import os
import httpx
from datetime import datetime, timezone
from .other_sports import SPORTS, _game_summary


class SourceUnavailable(Exception):
    pass


def api_key(sport):
    env = SPORTS[sport][0]
    return (os.getenv(env) or os.getenv("API_FOOTBALL_KEY") or "").strip()


def extract(sport, endpoint, params, transport=None):
    if sport not in SPORTS:
        raise ValueError("unknown sport")
    key = api_key(sport)
    if not key:
        raise SourceUnavailable("missing subscription credential")
    base = SPORTS[sport][1]
    try:
        with httpx.Client(timeout=14, follow_redirects=False,
                          trust_env=False, transport=transport) as client:
            response = client.get(base + "/" + endpoint, params=params,
                                  headers={"x-apisports-key": key})
            response.raise_for_status()
            body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise SourceUnavailable("sports provider request failed") from exc
    if not isinstance(body, dict) or body.get("errors"):
        raise SourceUnavailable("endpoint not covered by subscription or invalid parameters")
    rows = body.get("response")
    if not isinstance(rows, list):
        raise SourceUnavailable("invalid provider response")
    if int((body.get("paging") or {}).get("total", 1) or 1) > 1:
        raise SourceUnavailable("paged response needs a dedicated adapter")
    return rows


def normalize_games(sport, rows):
    unique = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        game = _game_summary(sport, row)
        ident = game.get("id")
        if ident is None:
            continue
        game["source"] = "api_sports"
        unique[str(ident)] = game
    return list(unique.values())


def normalize_standings(rows):
    """Do not assume standings are comparable between sports/countries."""
    data = []
    def visit(items, label=None):
        for item in items:
            if isinstance(item, list):
                visit(item, label)
            elif isinstance(item, dict):
                team = item.get("team") or {}
                if isinstance(team, dict) and team.get("id") and team.get("name"):
                    data.append({
                        "group": (item.get("group") or {}).get("name") if isinstance(item.get("group"), dict) else item.get("group") or label,
                        "stage": item.get("stage"),
                        "rank": item.get("position", item.get("rank")),
                        "team_id": team["id"], "team": team["name"],
                        "played": item.get("games", {}).get("played") if isinstance(item.get("games"), dict) else item.get("played"),
                        "won": item.get("games", {}).get("win") if isinstance(item.get("games"), dict) else item.get("won"),
                        "lost": item.get("games", {}).get("lose") if isinstance(item.get("games"), dict) else item.get("lost"),
                        "points": item.get("points"),
                        "provider": "api_sports",
                        "raw_stats": {k: v for k, v in item.items() if k not in ("team", "group")},
                    })
    visit(rows)
    return data
