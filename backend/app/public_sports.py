"""Public, cached sports reference feeds.

These are server-side, fixed-provider integrations; no user supplied URLs/keys.
They complement API-Sports snapshots when an optional subscription is absent.
Upstream services may change or restrict access; never fabricate standings.
"""
import os
import threading
import time
from datetime import datetime, timezone

import httpx

_CACHE = {}
_LOCK = threading.RLock()
F1 = "https://api.jolpi.ca/ergast/f1"
ESPN_NBA = "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings"
ESPN_US = {"nhl": "hockey/nhl", "mlb": "baseball/mlb", "nfl": "football/nfl", "wnba": "basketball/wnba"}
ESPN_CRICKET = "https://site.api.espn.com/apis/site/v2/sports/cricket"
CRICKETDATA = "https://api.cricapi.com/v1/currentMatches"


def _get(url, params=None):
    with httpx.Client(timeout=7, follow_redirects=False, trust_env=False) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        obj = response.json()
        if not isinstance(obj, dict):
            raise ValueError("Invalid sports response")
        return obj


def _cached(key, ttl, producer):
    now = time.monotonic()
    with _LOCK:
        found = _CACHE.get(key)
        if found and found[0] > now:
            return found[1]
        # Serialize updates to avoid a provider request per website visitor.
        try:
            value = producer()
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            # Keep the last verified result even during a provider outage.
            if found and found[1].get("available"):
                return {**found[1], "stale": True}
            value = {"available": False, "message": "Fuente temporalmente no disponible; no se muestran datos supuestos."}
        _CACHE[key] = (now + (ttl if value.get("available") else 300), value)
        return value


def _standing_list(path):
    data = _get(F1 + path)
    lists = (data.get("MRData") or {}).get("StandingsTable", {}).get("StandingsLists") or []
    return lists[0] if lists else {}


def formula_one(year=None):
    year = year or datetime.now(timezone.utc).year
    if year < 1950 or year > datetime.now(timezone.utc).year:
        raise ValueError("Invalid F1 season")

    def produce():
        drivers = _standing_list(f"/{year}/driverstandings.json")
        constructors = _standing_list(f"/{year}/constructorstandings.json")
        last = _get(F1 + f"/{year}/last/results.json")
        races = (last.get("MRData") or {}).get("RaceTable", {}).get("Races") or []
        last_race = None
        if races:
            race = races[0]
            finishers = (race.get("Results") or [])[:10]
            last_race = {
                "name": race.get("raceName"), "round": race.get("round"),
                "date": race.get("date"), "circuit": (race.get("Circuit") or {}).get("circuitName"),
                "podium": [
                    {"position": int(row["position"]),
                     "name": (row.get("Driver") or {}).get("givenName", "") + " " + (row.get("Driver") or {}).get("familyName", ""),
                     "team": (row.get("Constructor") or {}).get("name", ""),
                     "nationality": (row.get("Driver") or {}).get("nationality"),
                     "team_nationality": (row.get("Constructor") or {}).get("nationality")}
                    for row in finishers[:3] if row.get("position", "").isdigit()
                ],
                "results": [
                    {"position": int(row["position"]), "driver": (row.get("Driver") or {}).get("givenName", "") + " " + (row.get("Driver") or {}).get("familyName", ""),
                     "team": (row.get("Constructor") or {}).get("name", ""),
                     "nationality": (row.get("Driver") or {}).get("nationality"),
                     "team_nationality": (row.get("Constructor") or {}).get("nationality"),
                     "time": (row.get("Time") or {}).get("time") or row.get("status")}
                    for row in finishers if row.get("position", "").isdigit()
                ],
            }
        upcoming = None
        try:
            raw_next = _get(F1 + f"/{year}/next.json")
            schedule = (raw_next.get("MRData") or {}).get("RaceTable", {}).get("Races") or []
            if schedule:
                event = schedule[0]
                upcoming = {"name": event.get("raceName"), "date": event.get("date"),
                            "circuit": (event.get("Circuit") or {}).get("circuitName")}
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            pass
        if not drivers and not constructors and not last_race:
            return {"available": False, "message": "Temporada sin clasificaciones confirmadas"}
        return {
            "available": True, "season": year, "round": drivers.get("round"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "provider": "Jolpica / Ergast",
            "drivers": [{
                "rank": int(row["position"]), "name": f"{row.get('Driver', {}).get('givenName', '')} {row.get('Driver', {}).get('familyName', '')}".strip(),
                "team": ", ".join(c.get("name", "") for c in row.get("Constructors", []) if c.get("name")),
                "nationality": (row.get("Driver") or {}).get("nationality"),
                "team_nationalities": [c.get("nationality") for c in row.get("Constructors", []) if c.get("name")],
                "points": float(row["points"]), "wins": int(row.get("wins", 0)),
            } for row in drivers.get("DriverStandings", []) if row.get("position") and row.get("points")],
            "constructors": [{
                "rank": int(row["position"]), "name": row.get("Constructor", {}).get("name", ""),
                "nationality": (row.get("Constructor") or {}).get("nationality"),
                "points": float(row["points"]), "wins": int(row.get("wins", 0)),
            } for row in constructors.get("ConstructorStandings", []) if row.get("position") and row.get("points")],
            "last_race": last_race, "upcoming": upcoming,
        }
    return _cached(("f1", year), 3600, produce)


def _nba_rows(node, label="NBA"):
    """Accept ESPN conference/division nesting and legacy standings lists."""
    rows = []
    if not isinstance(node, dict):
        return rows
    group = node.get("name") or node.get("abbreviation") or label
    standings = node.get("standings") or {}
    blocks = standings if isinstance(standings, list) else [standings]
    for block in blocks:
        if not isinstance(block, dict):
            continue
        for entry in block.get("entries", []):
            if not isinstance(entry, dict):
                continue
            team = entry.get("team") or {}
            stats = {s.get("name"): s for s in entry.get("stats") or [] if isinstance(s, dict)}
            def stat(*names):
                for name in names:
                    if name in stats:
                        item = stats[name]
                        return item.get("value", item.get("displayValue"))
                return None
            rows.append({
                "id": team.get("id"), "name": team.get("displayName") or team.get("name"),
                "logo": team.get("logo") or next((x.get("href") for x in team.get("logos", []) if isinstance(x, dict) and x.get("href")), None),
                "group": group, "wins": stat("wins", "win"), "losses": stat("losses", "loss"),
                "win_pct": stat("winPercent", "winPercentage"),
                "rank": stat("playoffSeed", "rank"), "games_back": stat("gamesBehind", "gamesBack"),
                "points": stat("points", "point"), "ot_losses": stat("otLosses", "overtimeLosses"),
            })
    for child in node.get("children") or []:
        rows.extend(_nba_rows(child, group))
    return rows


def nba(season=None):
    year = datetime.now(timezone.utc).year
    season = int(season if season is not None else year)
    if season < 2010 or season > year:
        raise ValueError("Invalid NBA season")

    def produce():
        raw = _get(ESPN_NBA, {"season": season, "type": 2})
        groups = raw.get("children") or []
        rows = []
        for group in groups:
            rows.extend(_nba_rows(group))
        if not rows:
            rows = _nba_rows(raw)
        # Deduplicate possible conference/division nested representations.
        unique = {}
        for row in rows:
            if row.get("name"):
                unique[str(row.get("id") or row["name"])] = row
        entries = sorted(unique.values(), key=lambda row: (
            -(float(row["wins"]) if row["wins"] is not None else -1), row["name"]))
        return {
            "available": bool(entries), "season": season, "provider": "ESPN",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "rows": entries, "count": len(entries),
            "note": "Temporada regular; la temporada NBA se identifica por el año de inicio.",
        }
    return _cached(("nba", season), 10800, produce)


def cricket(competition="ipl"):
    if competition not in {"ipl", "icc.t20", "icc.world-cup"}:
        raise ValueError("Unknown cricket competition")

    def produce():
        # ESPN has different series coverage by competition. A missing
        # table must be reported, not replaced with a made-up ranking.
        rows = []
        try:
            data = _get(f"{ESPN_CRICKET}/{competition}/standings")
            rows = _nba_rows(data)  # ESPN grouped standings use the same envelope.
        except (httpx.HTTPError, ValueError, TypeError):
            pass
        games = []
        key = os.getenv("CRICKETDATA_API_KEY", "").strip()
        if key:
            try:
                body = _get(CRICKETDATA, {"apikey": key, "offset": 0})
                for match in (body.get("data") or [])[:30]:
                    if not isinstance(match, dict):
                        continue
                    score = match.get("score") or []
                    games.append({
                        "id": match.get("id"), "name": match.get("name"),
                        "date": match.get("date"), "status": match.get("status"),
                        "teams": match.get("teams") or [],
                        "score": score if isinstance(score, list) else [],
                        "match_type": match.get("matchType"),
                    })
            except (httpx.HTTPError, ValueError, TypeError):
                pass
        return {
            "available": bool(rows or games), "competition": competition,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "provider": "ESPN (tablas) / CricketData (partidos, si hay clave)",
            "rows": rows, "matches": games,
            "needs_key": not bool(key),
            "message": None if rows or games else "No hay tabla verificada disponible para esta competición. Los partidos requieren CRICKETDATA_API_KEY.",
        }
    return _cached(("cricket", competition, bool(os.getenv("CRICKETDATA_API_KEY"))), 3600, produce)


def us_league(sport, season=None):
    """NHL/MLB/NFL/WNBA regular season tables, including prior seasons, from ESPN."""
    if sport not in ESPN_US:
        raise ValueError("Unknown US league")
    year = datetime.now(timezone.utc).year
    season = int(season if season is not None else year)
    if season < 2015 or season > year:
        raise ValueError("Invalid sports season")

    def produce():
        raw = _get("https://site.api.espn.com/apis/v2/sports/" + ESPN_US[sport] + "/standings",
                   {"season": season, "type": 2})
        rows = []
        for group in raw.get("children") or []:
            rows.extend(_nba_rows(group))
        if not rows:
            rows = _nba_rows(raw)
        unique = {}
        for row in rows:
            if row.get("name"):
                unique[str(row.get("id") or row["name"])] = row
        entries = sorted(unique.values(), key=lambda row: (
            -(float(row["wins"]) if row["wins"] is not None else -1), row["name"]))
        return {"available": bool(entries), "season": season, "rows": entries,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "provider": "ESPN", "count": len(entries),
                "note": "Datos de temporada regular según el proveedor. La cobertura de temporadas antiguas puede variar."}
    return _cached((sport, season), 10800, produce)
