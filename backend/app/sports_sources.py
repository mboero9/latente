"""Extract and normalize other sports from whitelisted API-Sports hosts.

Only fixture and standings payloads with confirmed coverage are persisted.
No scraping, credentials in logs, or guessed player records.
"""
import os
import httpx
from datetime import datetime, timezone
from .other_sports import SPORTS, _game_summary, _trusted_logo as _trusted_team_logo


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


def normalize_standings(rows, sport=None):
    """Normalize provider standings while keeping actual club crests and scores."""
    def count(v):
        if isinstance(v, dict):
            v = v.get("total", v.get("all"))
        if isinstance(v, bool):
            return None
        try:
            return int(v) if v is not None else None
        except (ValueError, TypeError):
            return None
    data = []
    def visit(items, label=None):
        for item in items or []:
            if isinstance(item, list):
                visit(item, label)
            elif isinstance(item, dict):
                team = item.get("team") or {}
                if isinstance(team, dict) and team.get("id") and team.get("name"):
                    if sport == "nba":
                        conference = item.get("conference") or {}
                        division = item.get("division") or {}
                        games = item.get("win") or {}
                        defeats = item.get("loss") or {}
                        rank = conference.get("rank") or division.get("rank")
                        data.append({
                            "group": str(conference.get("name") or division.get("name") or "NBA"),
                            "stage": item.get("stage"), "rank": rank,
                            "team_id": team["id"], "team": team["name"],
                            "played": (games.get("total") or 0) + (defeats.get("total") or 0),
                            "won": games.get("total"), "lost": defeats.get("total"),
                            "points": None, "provider": "api_sports", "logo": _trusted_team_logo(team.get("logo")),
                            "raw_stats": item,
                        })
                        continue
                    games = item.get("games") or {}
                    if not isinstance(games, dict):
                        games = {}
                    scores = item.get("goals") or item.get("scores") or {}
                    if not isinstance(scores, dict):
                        scores = {}
                    data.append({
                        "drawn": count(games.get("draw", item.get("drawn"))),
                        "scored": count(scores.get("for")),
                        "conceded": count(scores.get("against")), 
                        "group": (item.get("group") or {}).get("name") if isinstance(item.get("group"), dict) else item.get("group") or label,
                        "stage": item.get("stage"),
                        "rank": item.get("position", item.get("rank")),
                        "team_id": team["id"], "team": team["name"],
                        "played": count(games.get("played", item.get("played"))),
                        "won": count(games.get("win", item.get("won"))),
                        "lost": count(games.get("lose", item.get("lost"))),
                        "points": item.get("points"),
                        "provider": "api_sports",
                        "logo": _trusted_team_logo(team.get("logo")),
                        "raw_stats": {k: v for k, v in item.items() if k not in ("team", "group")},
                    })
    visit(rows)
    return data
