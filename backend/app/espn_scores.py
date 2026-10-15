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


def rugby_feed(league="urba", season=None):
    if league not in RUGBY_LEAGUES:
        raise ValueError("Competición de rugby inválida")
    year = int(season or datetime.now(timezone.utc).year)
    if year < 2018 or year > datetime.now(timezone.utc).year + 1:
        raise ValueError("Temporada de rugby inválida")
    name, league_id = RUGBY_LEAGUES[league]

    def produce():
        # ESPN rejects year-long rugby scoreboard ranges with HTTP 400.
        # Query bounded 40-day windows, then try the legacy rugby-league
        # route used by some ESPN competitions. Never scrape HTML.
        today = datetime.now(timezone.utc).date()
        windows = [
            (today - timedelta(days=35), today + timedelta(days=10)),
            (today + timedelta(days=10), today + timedelta(days=55)),
        ]
        games = []
        used_route = None
        for rugby_path in ("rugby", "rugby-league"):
            candidate = {}
            successful = False
            for first, last in windows:
                if first.year > year or last.year < year:
                    continue
                from_day = max(first, date(year, 1, 1))
                to_day = min(last, date(year, 12, 31))
                try:
                    raw = _get(f"{ESPN_SITE}/{rugby_path}/{league_id}/scoreboard", {
                        "dates": from_day.strftime("%Y%m%d") + "-" + to_day.strftime("%Y%m%d"),
                        "limit": 125,
                    })
                    successful = True
                    for match in normalize_games(raw, name):
                        if (match.get("date") or "").startswith(str(year)):
                            candidate[match["id"]] = match
                except (httpx.HTTPError, ValueError, KeyError, TypeError):
                    continue
            if candidate:
                games = sorted(candidate.values(), key=lambda match: (match["date"] or "", match["id"]))
                used_route = rugby_path
                break
            if successful:
                used_route = rugby_path
        if not games:
            # Some ESPN rugby deployments reject the 'dates' parameter
            # entirely. Try the default current scoreboard once per host;
            # this is intentionally not a claim of full-season coverage.
            for host in (ESPN_SITE, "https://site.web.api.espn.com/apis/site/v2/sports"):
                for rugby_path in ("rugby", "rugby-league"):
                    try:
                        raw = _get(f"{host}/{rugby_path}/{league_id}/scoreboard")
                        seen = {match["id"]: match for match in normalize_games(raw, name)
                                if (match.get("date") or "").startswith(str(year))}
                        if seen:
                            games = sorted(seen.values(), key=lambda match: (match["date"] or "", match["id"]))
                            break
                    except (httpx.HTTPError, ValueError, KeyError, TypeError):
                        continue
                if games:
                    break
        # The public ESPN feeds sometimes expose a standalone standings
        # endpoint and sometimes only a metadata stub. An empty response
        # must never be shown as official rankings.
        official = []
        for rugby_path in dict.fromkeys((used_route or "rugby", "rugby-league")):
            try:
                standings = _get(f"{ESPN_TABLES}/{rugby_path}/{league_id}/standings", {"season": year})
                for group in standings.get("children") or []:
                    official.extend(_nba_rows(group))
                if not official:
                    official = _nba_rows(standings)
                if official:
                    break
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                continue
        # Avoid publishing a fake official championship ranking: rugby bonus
        # points vary by tournament and cannot be inferred from scores.
        from collections import defaultdict
        by_team = defaultdict(lambda: {"pj": 0, "g": 0, "e": 0, "p": 0,
                                        "for": 0, "against": 0})
        for match in games:
            if not match["completed"] or match["home_score"] is None or match["away_score"] is None:
                continue
            for team, own, conceded in (
                (match["home"], match["home_score"], match["away_score"]),
                (match["away"], match["away_score"], match["home_score"])
            ):
                row = by_team[team]
                row["pj"] += 1
                row["for"] += own
                row["against"] += conceded
                row["g" if own > conceded else "e" if own == conceded else "p"] += 1
        statistics = [{"team": team, **stats} for team, stats in by_team.items()]
        statistics.sort(key=lambda x: (-x["g"], -(x["for"] - x["against"]), x["team"]))
        return {
            "available": bool(games or official), "league": league,
            "league_name": name, "season": year, "games": games, "official": official,
            "statistics": statistics, "provider": "ESPN",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "message": None if games or official else "No hay encuentros confirmados de esta temporada en ESPN.",
        }
    return _cached(("rugby", league, year), 1800, produce)
