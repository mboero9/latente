"""Bounded, server-cached ESPN scoreboards for Latente.
Only whitelisted leagues and provider hosts are called. ESPN's public feeds
are undocumented; missing coverage is reported, never fabricated.
"""
from datetime import date, datetime, timedelta, timezone
import httpx

from .public_sports import _cached, _get, _nba_rows

ESPN_SITE = "https://site.api.espn.com/apis/site/v2/sports"
ESPN_TABLES = "https://site.api.espn.com/apis/v2/sports"
US_SPORTS = {
    "nba": "basketball/nba", "wnba": "basketball/wnba",
    "mlb": "baseball/mlb", "nhl": "hockey/nhl", "nfl": "football/nfl",
}
# IDs confirmed on ESPN's rugby calendar, not conjectural API-Sports IDs.
RUGBY_LEAGUES = {
    "urba": ("URBA Top 14 · Argentina", "289279"),
    "championship": ("Rugby Championship · Los Pumas", "244293"),
    "six-nations": ("Seis Naciones", "180659"),
    "super-rugby": ("Super Rugby Pacific", "242041"),
    "premiership": ("Premiership Rugby", "267979"),
    "top-14": ("Top 14 · Francia", "270559"),
    "urc": ("United Rugby Championship", "270557"),
    "champions": ("Champions Cup", "271937"),
    "test-matches": ("Partidos internacionales", "289234"),
    "world-cup": ("Mundial de Rugby", "164205"),
    # Competition IDs appear in ESPN game/result URLs; these IDs are not
    # provider IDs for API-Sports. Keep sources rigorously separated.
    "mlr": ("Major League Rugby", "289262"),
    "challenge-cup": ("European Rugby Challenge Cup", "272073"),
}

def _number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value) if str(value).strip() != "" else None
    except (ValueError, TypeError):
        return None


def normalize_games(data, league):
    matches = []
    for event in data.get("events") or []:
        if not isinstance(event, dict):
            continue
        contest = (event.get("competitions") or [{}])[0]
        competitors = contest.get("competitors") or []
        def side(which):
            return next((t for t in competitors if t.get("homeAway") == which), {})
        home, away = side("home"), side("away")
        if not home or not away:
            continue
        status = (contest.get("status") or event.get("status") or {}).get("type") or {}
        start = event.get("date") or contest.get("date")
        matches.append({
            "id": str(event.get("id") or ""), "league": league,
            "date": start, "home": (home.get("team") or {}).get("displayName") or "Local",
            "away": (away.get("team") or {}).get("displayName") or "Visitante",
            "home_logo": (home.get("team") or {}).get("logo") or next((x.get("href") for x in (home.get("team") or {}).get("logos", []) if isinstance(x, dict) and x.get("href")), None),
            "away_logo": (away.get("team") or {}).get("logo") or next((x.get("href") for x in (away.get("team") or {}).get("logos", []) if isinstance(x, dict) and x.get("href")), None),
            "home_score": _number(home.get("score")), "away_score": _number(away.get("score")),
            "status": status.get("description") or status.get("name") or "No informado",
            "completed": bool(status.get("completed")), "state": status.get("state") or "",
        })
    return sorted(matches, key=lambda item: (item["date"] or "", item["id"]))


def us_scoreboard(sport, day=None):
    if sport not in US_SPORTS:
        raise ValueError("Unrecognized sports league")
    date_key = day or datetime.now(timezone.utc).date().isoformat()
    requested = date.fromisoformat(date_key)
    if abs((requested - datetime.now(timezone.utc).date()).days) > 366:
        raise ValueError("Scoreboard outside supported date range")
    def produce():
        url = f"{ESPN_SITE}/{US_SPORTS[sport]}/scoreboard"
        # One request covers nearby results and the next games.
        first, last = requested - timedelta(days=7), requested + timedelta(days=7)
        query = {"dates": first.strftime("%Y%m%d") + "-" + last.strftime("%Y%m%d"), "limit": 250}
        raw = _get(url, query)
        games = normalize_games(raw, sport.upper())
        return {"available": bool(games), "games": games, "sport": sport,
                "from": first.isoformat(), "to": last.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "provider": "ESPN", "message": None if games else "ESPN no informa partidos para estas fechas."}
    return _cached(("scoreboard", sport, date_key), 600, produce)


def season_windows(year, days=28):
    """Bounded ESPN scoreboard slices across the entire calendar season.

    ESPN rejects overly broad rugby date ranges. Small 28-day windows let
    RugbyHub display verified March games in October, not just this week.
    These calls run in scheduled ingestion, NEVER in request handlers.
    """
    cursor = date(year, 1, 1)
    end = date(year, 12, 31)
    while cursor <= end:
        last = min(cursor + timedelta(days=days - 1), end)
        yield cursor, last
        cursor = last + timedelta(days=1)


def rugby_feed(league="urba", season=None):
    if league not in RUGBY_LEAGUES:
        raise ValueError("Competición de rugby inválida")
    year = int(season or datetime.now(timezone.utc).year)
    if year < 2018 or year > datetime.now(timezone.utc).year + 1:
        raise ValueError("Temporada de rugby inválida")
    name, league_id = RUGBY_LEAGUES[league]

    def produce():
        games = {}
        used_route = None
        windows = list(season_windows(year))
        # Try the regular rugby feed first for the FULL calendar year.
        # If none has coverage, use just three distributed probes with the
        # legacy rugby-league path; avoid doubling requests indiscriminately.
        for rugby_path, scans in (
            ("rugby", windows),
            ("rugby-league", [windows[2], windows[len(windows)//2], windows[-3]]),
        ):
            any_success = False
            for first, last in scans:
                try:
                    raw = _get(f"{ESPN_SITE}/{rugby_path}/{league_id}/scoreboard", {
                        "dates": first.strftime("%Y%m%d") + "-" + last.strftime("%Y%m%d"),
                        "limit": 250,
                    })
                    any_success = True
                    for game in normalize_games(raw, name):
                        if (game.get("date") or "").startswith(str(year)) and game.get("id"):
                            prev = games.get(game["id"])
                            if prev is None or (game["completed"] and not prev["completed"]):
                                games[game["id"]] = game
                except (httpx.HTTPError, ValueError, KeyError, TypeError):
                    # Unsupported league/period: missing is not a fake score.
                    continue
            if games:
                used_route = rugby_path
                break
            if any_success:
                used_route = rugby_path

        # Some ESPN leagues ignore 'dates'; try one default scoreboard as a
        # final, bounded discovery query if the date ranges contained no games.
        if not games:
            for path in dict.fromkeys((used_route or "rugby", "rugby-league")):
                try:
                    raw = _get(f"{ESPN_SITE}/{path}/{league_id}/scoreboard", {"limit": 250})
                    for game in normalize_games(raw, name):
                        if (game.get("date") or "").startswith(str(year)) and game.get("id"):
                            games[game["id"]] = game
                    if games:
                        used_route = path
                        break
                except (httpx.HTTPError, ValueError, KeyError, TypeError):
                    continue

        # Only standings actually provided by ESPN; rugby points and bonus
        # can NOT be computed faithfully from ordinary rugby results.
        official = []
        for rugby_path in dict.fromkeys((used_route or "rugby", "rugby", "rugby-league")):
            try:
                table = _get(f"{ESPN_TABLES}/{rugby_path}/{league_id}/standings",
                             {"season": year})
                official = _nba_rows(table)
                if official:
                    break
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                continue
        ordered = sorted(games.values(), key=lambda row: (row.get("date") or "", row["id"]))
        from collections import defaultdict
        by_team = defaultdict(lambda: {"pj": 0, "g": 0, "e": 0, "p": 0,
                                        "for": 0, "against": 0})
        for game in ordered:
            if not game["completed"] or game["home_score"] is None or game["away_score"] is None:
                continue
            for team, own, conceded in (
                (game["home"], game["home_score"], game["away_score"]),
                (game["away"], game["away_score"], game["home_score"]),
            ):
                stats = by_team[team]
                stats["pj"] += 1
                stats["for"] += own
                stats["against"] += conceded
                stats["g" if own > conceded else "e" if own == conceded else "p"] += 1
        stats = [{"team": team, **data} for team, data in by_team.items()]
        stats.sort(key=lambda v: (-v["g"], -(v["for"]-v["against"]), v["team"]))
        return {
            "available": bool(ordered or official), "league": league,
            "league_name": name, "season": year, "games": ordered,
            "official": official, "statistics": stats, "provider": "ESPN",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "message": (None if ordered or official else
                        "ESPN no ofrece datos estructurados verificables de esta liga y temporada."),
        }
    return _cached(("rugby_season_full", league, year), 21600, produce)
