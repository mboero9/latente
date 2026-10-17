"""API-Rugby ingestion and PostgreSQL read model for Latente.

Each slug resolves against the provider's actual league catalogue. No
fabricated league IDs, fixtures, standings or bonus-point calculations.
All API calls run in the cron worker, never on page views.
"""
import os
import re
import logging
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from .db import session_scope
from .models import SportSnapshot, utcnow
from .ingest import upsert
from .sports_sources import extract, SourceUnavailable
from .sports_scheduler import reserve_quota
from .provider import aware
from .rugby_clubs import edition_clubs, published_schedule, source_url

log = logging.getLogger("latente.rugby")

# Names are used ONLY to resolve verified IDs from GET /leagues.
# API-Sports still calls the historic competition Top 12 in its catalogue.
# Argentina URBA 2026 fields 14 clubs; keep France separate.
COMPETITIONS = (
    ("urba", "URBA · Top 14 (Argentina, 2026)", ("top 12", "top12", "top 14"), ("argentina",)),
    ("interior-a", "UAR · Torneo del Interior A", ("torneo del interior a",), ("argentina",)),
    ("interior-b", "UAR · Torneo del Interior B", ("torneo del interior b",), ("argentina",)),
    # These competitions exist in the 2026 official calendars. A public
    # fixture page does NOT imply an authorized JSON feed or full standings.
    ("urba-primera-a", "URBA · Primera A", ("primera a", "primera division a"), ("argentina",)),
    ("urba-primera-b", "URBA · Primera B", ("primera b", "primera division b"), ("argentina",)),
    ("urba-primera-c", "URBA · Primera C", ("primera c", "primera division c"), ("argentina",)),
    ("urba-segunda", "URBA · Segunda División", ("segunda division",), ("argentina",)),
    ("urba-tercera", "URBA · Tercera División", ("tercera division",), ("argentina",)),
    ("urba-desarrollo", "URBA · Desarrollo", ("desarrollo",), ("argentina",)),
    ("litoral-top10", "Torneo Regional del Litoral · Top 10", ("torneo regional del litoral",), ("argentina",)),
    ("litoral-segunda", "Torneo Regional del Litoral · Segunda", ("trl segunda",), ("argentina",)),
    ("cordoba-top10", "Unión Cordobesa · Top 10 A", ("top 10 a",), ("argentina",)),
    ("cordoba-super9", "Unión Cordobesa · Súper 9 B", ("super 9 b",), ("argentina",)),
    ("noa-regional-a", "Regional del NOA · Torneo A", ("regional del noa a",), ("argentina",)),
    ("noa-regional-b", "Regional del NOA · Torneo B", ("regional del noa b",), ("argentina",)),
    ("tucumano-anual", "Torneo Anual Tucumano", ("anual tucumano",), ("argentina",)),
    ("championship", "Rugby Championship · Los Pumas", ("rugby championship",), ("world",)),
    ("six-nations", "Seis Naciones", ("six nations",), ("europe",)),
    ("super-rugby", "Super Rugby", ("super rugby",), ("world",)),
    ("premiership", "Premiership Rugby", ("premiership rugby",), ("england",)),
    ("top-14", "Top 14 · Francia", ("top 14",), ("france",)),
    ("urc", "United Rugby Championship", ("united rugby championship",), ("world",)),
    ("champions", "European Rugby Champions Cup", ("european rugby champions cup",), ("europe",)),
    ("test-matches", "Amistosos internacionales", ("friendly international",), ("world",)),
    ("world-cup", "Mundial de Rugby", ("world cup",), ("world",)),
    ("npc-nz", "National Provincial Championship · Nueva Zelanda", ("national provincial championship",), ("new zealand",)),
    ("currie-cup", "Currie Cup · Sudáfrica", ("currie cup",), ("south africa",)),
    ("pro-d2", "Pro D2 · Francia", ("pro d2",), ("france",)),
    ("challenge-cup", "European Challenge Cup", ("challenge cup",), ("europe",)),
    ("europe-championship", "Rugby Europe Championship", ("rugby europe championship",), ("europe",)),
    ("europe-trophy", "Rugby Europe Trophy", ("rugby europe trophy",), ("europe",)),
    ("europe-conference", "Rugby Europe Conference", ("rugby europe conference",), ("europe",)),
    ("europe-super-cup", "Europe Super Cup", ("europe super cup",), ("europe",)),
    ("top10-italia", "Top10 · Italia", ("top10",), ("italy",)),
    ("nations-championship", "Nations Championship", ("nations championship",), ("international",)),
    ("pacific-nations", "Pacific Nations Cup", ("pacific nations cup",), ("international",)),
    ("autumn-series", "Autumn Nations Series", ("autumn nations series",), ("international",)),
    ("premiership-cup", "Premiership Rugby Cup", ("premiership rugby cup",), ("england",)),
    ("premiership-women", "Premiership Women's Rugby", ("premiership women's rugby",), ("england",)),
    ("six-nations-women", "Six Nations femenino", ("women's six nations",), ("europe",)),
    ("super-rugby-aupiki", "Super Rugby Aupiki", ("super rugby aupiki",), ("new zealand",)),
    ("mlr", "Major League Rugby · EE. UU.", ("major league rugby",), ("usa",)),
    ("world-u20", "Mundial de Rugby Sub-20", ("world rugby u20 championship",), ("international",)),
    ("world-cup-women", "Mundial femenino de Rugby", ("women's world cup",), ("international",)),
    ("farah-palmer", "Farah Palmer Cup · Nueva Zelanda", ("farah palmer cup",), ("new zealand",)),
    ("super-w", "Super W · Australia", ("super w women",), ("australia",)),
    ("lions-tour", "Gira British & Irish Lions", ("lions tour",), ("international",)),
    ("nations-cup", "Nations Cup", ("nations cup",), ("international",)),
    ("wxv1", "WXV 1 femenino", ("wxv 1",), ("international",)),
)
BY_SLUG = {slug: (title, names, countries) for slug, title, names, countries in COMPETITIONS}
CATALOG_TTL = timedelta(days=1)
GAMES_TTL = timedelta(hours=6)
STANDINGS_TTL = timedelta(hours=24)
FAIL_TTL = timedelta(hours=6)


def key_configured():
    return bool((os.getenv("RUGBY_API_KEY") or os.getenv("API_FOOTBALL_KEY") or "").strip())


def _clean(value):
    return re.sub(r"\s+", " ", str(value or "").casefold().replace("-", " ")).strip()


def seasons_for(league):
    seasons = league.get("seasons") or []
    found = set()
    for season in seasons:
        value = season.get("season", season.get("year")) if isinstance(season, dict) else season
        try:
            year = int(value)
            if 2000 <= year <= datetime.now(timezone.utc).year + 1:
                found.add(year)
        except (ValueError, TypeError):
            pass
    return sorted(found, reverse=True)


def resolve(rows):
    """Exact competition and geography, not ambiguous partial name matching."""
    out = []
    for slug, title, aliases, countries in COMPETITIONS:
        chosen = None
        for entry in rows:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), int):
                continue
            country = entry.get("country")
            if isinstance(country, dict):
                country = country.get("name")
            if _clean(entry.get("name")) in aliases and _clean(country) in countries:
                chosen = entry
                break
        if chosen is not None:
            out.append({
                "slug": slug, "name": title, "league_name": chosen["name"],
                "league_id": chosen["id"],
                "country": (chosen.get("country") or {}).get("name", "") if isinstance(chosen.get("country"), dict) else chosen.get("country", ""),
                "seasons": seasons_for(chosen),
            })
        else:
            out.append({"slug": slug, "name": title, "league_name": None,
                        "league_id": None, "country": None, "seasons": []})
    return out


def _num(value):
    if isinstance(value, dict):
        value = value.get("total", value.get("value"))
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None


def normalize_games(rows):
    result = []
    seen = set()
    for g in rows:
        if not isinstance(g, dict) or g.get("id") is None or str(g["id"]) in seen:
            continue
        teams = g.get("teams") or {}
        if not isinstance(teams, dict):
            continue
        h, a = teams.get("home") or {}, teams.get("away") or {}
        if not isinstance(h, dict) or not isinstance(a, dict) or not h.get("name") or not a.get("name"):
            continue
        seen.add(str(g["id"]))
        scores = g.get("scores") or {}
        status = g.get("status") or {}
        short = str(status.get("short") or "") if isinstance(status, dict) else ""
        label = str(status.get("long") or short) if isinstance(status, dict) else str(status)
        def score(side):
            v = scores.get(side) if isinstance(scores, dict) else None
            return _num(v.get("total")) if isinstance(v, dict) else _num(v)
        date_value = g.get("date") or ""
        if isinstance(date_value, dict):
            date_value = date_value.get("start") or ""
        completed = short.upper() in {"FT", "AET", "PEN", "FINAL"} or label.casefold() in {
            "finished", "game finished", "match finished", "after extra time",
            "full time", "final", "ended", "completed"}
        result.append({
            "id": str(g["id"]), "date": str(date_value),
            "home": str(h["name"]), "away": str(a["name"]),
            "home_logo": h.get("logo"), "away_logo": a.get("logo"),
            "home_score": score("home"), "away_score": score("away"),
            "status": label, "completed": completed,
        })
    return sorted(result, key=lambda g: (g["date"], g["id"]))


def normalize_standings(rows):
    """Standings retain official position/points; no invented rugby rules."""
    parsed = []
    def visit(items, group=""):
        if not isinstance(items, list):
            return
        for item in items:
            if isinstance(item, list):
                visit(item, group)
            elif isinstance(item, dict):
                team = item.get("team") or {}
                if isinstance(team, dict) and team.get("name"):
                    record = item.get("games") or {}
                    if not isinstance(record, dict):
                        record = {}
                    group_obj = item.get("group")
                    grouping = group_obj.get("name") if isinstance(group_obj, dict) else group_obj
                    parsed.append({
                        "team": str(team["name"]),
                        "team_id": team.get("id"), "logo": team.get("logo"),
                        "rank": _num(item.get("position", item.get("rank"))),
                        "group": str(grouping or group or "General"),
                        "played": _num(record.get("played", item.get("played"))),
                        "won": _num(record.get("win", item.get("won"))),
                        "drawn": _num(record.get("draw", item.get("drawn"))),
                        "lost": _num(record.get("lose", item.get("lost"))),
                        "points": _num(item.get("points")),
                        "for": _num(item.get("for")),
                        "against": _num(item.get("against")),
                    })
                elif "standings" in item:
                    visit(item["standings"], str(item.get("group") or group))
    visit(rows)
    return sorted(parsed, key=lambda r: (r["group"], r["rank"] if r["rank"] is not None else 999, r["team"]))


def _snapshot(kind, ref):
    with session_scope() as db:
        row = db.get(SportSnapshot, ("rugby", kind, ref))
        # Eager immutable data before session_scope expires ORM attributes.
        return SimpleNamespace(data=row.data, source_count=row.source_count,
                               updated_at=row.updated_at) if row else None


def _write(kind, ref, rows, count, note=""):
    now = utcnow()
    with session_scope() as db:
        existing = db.get(SportSnapshot, ("rugby", kind, ref))
        if existing and existing.source_count > 0 and not rows:
            return False
        upsert(db, SportSnapshot, {
            "sport": "rugby", "dataset": kind, "ref": ref,
            "provider": ("rugbyapi.com" if kind.startswith("rugbyapi_") else
                         "thesportsdb" if kind.startswith("thesportsdb_") else
                         "espn" if kind.startswith("espn_") else "api_rugby"),
            "data": rows, "source_count": count,
            "updated_at": now, "note": note[:250],
        })
    return True


def catalog():
    obj = _snapshot("leagues", "curated-2026")
    return obj.data if obj else []


def public_catalog():
    by_slug = {row["slug"]: row for row in catalog()
               if isinstance(row,dict) and row.get("slug") in BY_SLUG}
    external=_snapshot("rugbyapi_cats","current")
    discovered=external.data if external else []
    by_com={row["slug"]:row for row in discovered
            if isinstance(row,dict) and row.get("slug")}
    seasons_snapshot=_snapshot("rugbyapi_seasons","current")
    seasons=seasons_snapshot.data if seasons_snapshot else []
    seasons_by_slug={}
    for item in seasons:
        if isinstance(item,dict) and item.get("slug") and isinstance(item.get("year"),int):
            seasons_by_slug.setdefault(item["slug"],set()).add(item["year"])
    result=[]
    for slug,title,_,_ in COMPETITIONS:
        from_api=by_slug.get(slug,{})
        mapped=by_com.get(slug,{})
        result.append({
            "slug":slug,"name":title,
            **{k:v for k,v in from_api.items() if k not in ("name","slug","seasons")},
            "rugbyapi_id":mapped.get("competition_id"),
            "region":mapped.get("region") or mapped.get("country"),
            "source_coverage":bool(mapped),
            "official_url":source_url(slug),
            "seasons":sorted(set(from_api.get("seasons") or []).union(seasons_by_slug.get(slug,set())).union({2026} if slug in {
                "urba", "interior-a", "interior-b", "urba-primera-a",
                "urba-primera-b", "urba-primera-c", "urba-segunda",
                "urba-tercera", "urba-desarrollo", "litoral-top10",
                "litoral-segunda", "cordoba-top10", "cordoba-super9",
                "noa-regional-a", "noa-regional-b", "tucumano-anual",
            } else set()),reverse=True)
        })
    for row in discovered:
        if not isinstance(row,dict) or not row.get("slug") or row["slug"] in BY_SLUG:
            continue
        # Explicitly excluded domestic rugby coverage by request.
        origin = str(row.get("region") or row.get("country") or "").casefold()
        if any(place in origin for place in ("japan", "japón", "chile", "uruguay")):
            continue
        result.append({
            "slug":row["slug"],"name":row["name"],
            "rugbyapi_id":row.get("competition_id"),
            "region":row.get("region") or row.get("country"),
            "source_coverage":True,
            "seasons":sorted(seasons_by_slug.get(row["slug"],set()),reverse=True)
        })
    return result


# Explicit variants appearing in ESPN / API-Sports fixture feeds. Exact
# normalized matching avoids attaching the crest of a different club.
CLUB_FIXTURE_ALIASES = {
    "belgrano athletic": ("belgrano ac", "belgrano athletic club"),
    "la plata rugby club": ("la plata", "la plata rc"),
    "buenos aires cricket & rugby club": ("b a c r c", "bacrc", "buenos aires c rc"),
    "atletico del rosario": ("atletico del rosario",),
    "hindu": ("hindu club",),
    "cuba": ("cuba",),
    "sic": ("sic",),
    "regatas bella vista": ("regatas bella vista",),
    "jockey club de villa maria": ("jockey villa maria",),
}


def _club_key(name):
    import unicodedata
    folded = "".join(c for c in unicodedata.normalize("NFKD", str(name or "").casefold())
                     if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", folded).strip()


def attach_club_logos(clubs, games, official):
    """Attach only official/published or provider-verified logos.
    Prefer a federation logo embedded in the 2026 edition list; otherwise
    find a cached match/official table exact alias. No vendor calls.
    """
    logos = {}
    for match in games:
        for side in ("home", "away"):
            name, url = match.get(side), match.get(f"{side}_logo")
            if name and isinstance(url, str) and url.startswith("https://"):
                logos[_club_key(name)] = url
    for row in official:
        name, url = row.get("team"), row.get("logo")
        if name and isinstance(url, str) and url.startswith("https://"):
            logos[_club_key(name)] = url
    updated = []
    for club in clubs:
        item = dict(club)
        if not item.get("logo"):
            key = _club_key(item["team"])
            variants = (key,) + CLUB_FIXTURE_ALIASES.get(key, ())
            item["logo"] = next((logos[variant] for variant in variants
                                  if variant in logos), None)
        updated.append(item)
    return updated


def read_competition(slug, season=None):
    row = next((c for c in public_catalog() if c["slug"] == slug), None)
    if row is None:
        raise ValueError("unknown competition")
    title = row["name"]
    league_id = row.get("league_id")
    available = row.get("seasons") or []
    current_year = datetime.now(timezone.utc).year
    year = int(season) if season else next((y for y in available if y <= current_year), current_year)
    if year < 2000 or year > datetime.now(timezone.utc).year + 1:
        raise ValueError("year out of range")
    ref = f"{league_id}:{year}" if league_id else None
    primary_games = _snapshot("games", ref) if ref else None
    primary_table = _snapshot("standings", ref) if ref else None
    # ESPN is a secondary source, loaded only by the scheduled ingest job.
    # Each dataset falls back independently: official tables are NEVER
    # reverse-engineered from match scores (rugby bonus points vary).
    backup_games = _snapshot("espn_games", f"{slug}:{year}")
    backup_table = _snapshot("espn_standings", f"{slug}:{year}")
    sportsdb_games = _snapshot("thesportsdb_games", f"{slug}:{year}")
    rugbyapi_games = _snapshot("rugbyapi_games", f"{slug}:{year}")
    rugbyapi_table = _snapshot("rugbyapi_tables", f"{slug}:{year}")
    backup_stats = _snapshot("espn_statistics", f"{slug}:{year}")
    game_source = (rugbyapi_games if rugbyapi_games and rugbyapi_games.data else
                   primary_games if primary_games and primary_games.data else
                   backup_games if backup_games and backup_games.data else sportsdb_games)
    table_source = (rugbyapi_table if rugbyapi_table and rugbyapi_table.data else
                    primary_table if primary_table and primary_table.data else backup_table)
    # Independent providers may publish only part of the calendar. Merge real
    # matches by teams and date, with fresh completed results taking precedence.
    by_game = {}
    for source in (sportsdb_games, backup_games, primary_games, rugbyapi_games):
        for game in (source.data or []) if source else []:
            if not isinstance(game,dict) or not game.get("home") or not game.get("away"):
                continue
            identity = (_clean(game["home"]),_clean(game["away"]),str(game.get("date") or "")[:10])
            previous = by_game.get(identity)
            if previous and previous.get("completed") and not game.get("completed"):
                continue
            by_game[identity] = game
    games = sorted(by_game.values(), key=lambda g: (g.get("date") or "", g.get("id") or ""))
    official = table_source.data if table_source else []
    clubs = edition_clubs(slug, year)
    clubs = attach_club_logos(clubs, games, official)
    sources = [src for src, row in (
        ("rugbyAPI.com", rugbyapi_games if rugbyapi_games and rugbyapi_games.data else None),
        ("rugbyAPI.com", rugbyapi_table if rugbyapi_table and rugbyapi_table.data else None),
        ("API-Rugby", primary_games if game_source == primary_games and primary_games and primary_games.data else None),
        ("API-Rugby", primary_table if table_source == primary_table and primary_table and primary_table.data else None),
        ("ESPN", backup_games if game_source == backup_games and backup_games and backup_games.data else None),
        ("TheSportsDB", sportsdb_games if game_source == sportsdb_games and sportsdb_games and sportsdb_games.data else None),
        ("ESPN", backup_table if table_source == backup_table and backup_table and backup_table.data else None),
    ) if row is not None]
    provider = " + ".join(dict.fromkeys(sources)) if sources else "API-Rugby / ESPN / rugbyAPI.com"
    return {
        "available": bool(games or official),
        "configured": key_configured() or bool(os.getenv("RUGBYAPI_COM_KEY")),
        "provider": provider, "league_name": title,
        "season": year, "seasons": sorted(set([*available, *([year] if games or official else [])]), reverse=True),
        "games": games, "official": official,
        "verified_clubs": clubs,
        "published_schedule": published_schedule(slug, year),
        "schedule_verified_results": False,
        "clubs_source_url": source_url(slug),
        "clubs_note": ("Clubes de la edición 2026 confirmados en la publicación de la organización; "
                       "los escudos provienen de su sitio o de imágenes verificadas del proveedor. "
                       "Este listado no equivale a una tabla de posiciones."
                        if clubs else None),
        "statistics": backup_stats.data if backup_stats else [],
        "updated_at": max((aware(row.updated_at) for row in (game_source, table_source, backup_stats) if row), default=None),
        "message": None if games or official else
            "Sin partidos o clasificaciones verificadas en las fuentes disponibles para esta temporada. Consultá el calendario de la organización.",
    }


def _fresh(snapshot, ttl):
    return bool(snapshot and aware(snapshot.updated_at) + ttl > utcnow())


def sync_once(max_calls=3, fetch=None):
    """Single-iteration bounded cron work; keep all requests in Railway worker."""
    fetch = fetch or (lambda endpoint, params: extract("rugby", endpoint, params))
    result = {"attempted": [], "updated": [], "unavailable": []}
    if not key_configured():
        result["unavailable"].append("Falta RUGBY_API_KEY o API_FOOTBALL_KEY")
        return result

    def call(kind, ref, endpoint, params, normalize, ttl, note=""):
        if len(result["attempted"]) >= max_calls or _fresh(_snapshot(kind, ref), ttl):
            return
        error_ref = f"{kind}:{ref}"
        if _fresh(_snapshot("diagnostic", error_ref), FAIL_TTL):
            return
        if not reserve_quota("rugby", cap=60):
            result["unavailable"].append("Cuota diaria conservadora alcanzada")
            return
        result["attempted"].append(f"{kind}:{ref}")
        try:
            rows = fetch(endpoint, params)
            cleaned = normalize(rows)
            if cleaned and (kind != "leagues" or any(r.get("league_id") for r in cleaned)):
                _write(kind, ref, cleaned, len(rows), note)
                result["updated"].append(f"{kind}:{ref}")
            else:
                _write("diagnostic", error_ref, [{"message": "Sin cobertura o resultados"}], 1)
        except (SourceUnavailable, ValueError, TypeError, KeyError):
            _write("diagnostic", error_ref, [{"message": "Proveedor no disponible o plan sin cobertura"}], 1)
            result["unavailable"].append(f"{kind}:{ref}")

    call("leagues", "curated-2026", "leagues", {}, resolve, CATALOG_TTL,
         "Identificadores confirmados por API-Rugby; cobertura sujeta al plan.")
    if not catalog():
        return result
    now_year = datetime.now(timezone.utc).year
    # Prioritize each competition's latest available season, then games and tables.
    for comp in catalog():
        league = comp.get("league_id")
        seasons = comp.get("seasons") or []
        year = next((y for y in seasons if y <= now_year), now_year)
        if not league:
            continue
        ref = f"{league}:{year}"
        params = {"league": league, "season": year}
        call("games", ref, "games", params, normalize_games, GAMES_TTL, comp["name"])
        call("standings", ref, "standings", params, normalize_standings, STANDINGS_TTL, comp["name"])
        if len(result["attempted"]) >= max_calls:
            break
    return result


# Independent, documented fallback from the existing ESPN rugby provider adapter.
# ESPN's public feeds are unofficial/undocumented and may stop working; snapshots
# have source labels and stay empty rather than supplying imaginary league points.
ESPN_REFRESH = timedelta(hours=8)
ESPN_RETRY = timedelta(hours=6)
ESPN_PRIORITY = ("top-14", "urba", "championship", "premiership",
                 "six-nations", "urc", "super-rugby", "champions",
                 "test-matches", "world-cup")


def espn_standings(rows):
    """Adapt verified ESPN ranking data to RugbyHub without losing provenance."""
    parsed = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or not row.get("name"):
            continue
        points = _num(row.get("points"))
        rank = _num(row.get("rank"))
        if points is None and rank is None:
            # Records with neither rank nor league points are team stats,
            # not an official table. Do not pass them off as standings.
            continue
        parsed.append({
            "team": row["name"], "team_id": row.get("id"),
            "logo": row.get("logo"), "group": row.get("group") or "General",
            "rank": rank or i + 1, "played": None,
            "won": _num(row.get("wins")), "lost": _num(row.get("losses")),
            "drawn": None, "points": points,
            "for": None, "against": None,
        })
    return parsed


def sync_espn_once(max_leagues=1, fetch=None):
    """Scheduled ESPN fallback. No visitor-initiated ESPN calls.

    Rotates through leagues with old/absent snapshots, attempts each source
    once per 6h, and retains prior data on provider failure.
    """
    from .espn_scores import rugby_feed
    fetch = fetch or rugby_feed
    report = {"attempted": [], "updated": [], "unavailable": []}
    current = datetime.now(timezone.utc).year
    candidates = []
    for slug in ESPN_PRIORITY:
        ref = f"{slug}:{current}"
        games = _snapshot("espn_games", ref)
        table = _snapshot("espn_standings", ref)
        diag = _snapshot("espn_diagnostic_v3", ref)
        if _fresh(diag, ESPN_RETRY):
            continue
        if _fresh(games, ESPN_REFRESH) and _fresh(table, STANDINGS_TTL):
            continue
        # Work on least recently tried competitions before retrying coverage.
        oldest = min((aware(v.updated_at) for v in (games, table, diag) if v),
                     default=datetime(2000, 1, 1, tzinfo=timezone.utc))
        candidates.append((oldest, ESPN_PRIORITY.index(slug), slug))
    for _, _, slug in sorted(candidates)[:max_leagues]:
        ref = f"{slug}:{current}"
        report["attempted"].append(slug)
        try:
            result = fetch(slug, current)
            games = result.get("games") or []
            official = espn_standings(result.get("official") or [])
            # ESPN's already-derived match-only stats can be shown separately,
            # never with official ranks or rugby competition/bonus points.
            partial = [v for v in (result.get("statistics") or [])
                       if isinstance(v, dict) and v.get("team") and
                       isinstance(v.get("pj"), int) and v["pj"] > 0]
            if games:
                _write("espn_games", ref, games, len(games), "ESPN: partidos y fixture, cobertura parcial")
                report["updated"].append(f"games:{slug}")
            if official:
                _write("espn_standings", ref, official, len(official),
                       "ESPN: clasificación publicada por proveedor, sin calcular bonus")
                report["updated"].append(f"standings:{slug}")
            if partial:
                _write("espn_statistics", ref, partial, len(partial),
                       "Estadísticas parciales solo de encuentros verificados ESPN")
                report["updated"].append(f"statistics:{slug}")
            if not games and not official and not partial:
                report["unavailable"].append(slug)
            # Record last attempt to throttle empty and restricted sources.
            _write("espn_diagnostic_v3", ref, [{"attempted": True}], 1)
        except (ValueError, TypeError, KeyError, ImportError, OSError):
            _write("espn_diagnostic_v3", ref, [{"attempted": True}], 1)
            report["unavailable"].append(slug)
    return report


def sync_sportsdb_once(max_leagues=2, fetch=None):
    """Backfill rugby calendar from TheSportsDB; no league standings fabricated.

    Service runs periodically and stores confirmed published events only. Free
    TheSportsDB API returns a limited number of events per queried season.
    """
    from .thesportsdb_rugby import LEAGUES, fetch as fetch_sportsdb
    fetch = fetch or fetch_sportsdb
    year=datetime.now(timezone.utc).year
    options=[]
    for slug in LEAGUES:
        ref=f"{slug}:{year}"
        current=_snapshot("thesportsdb_games",ref)
        diagnostics=_snapshot("tsdb_diagnostic",ref)
        if _fresh(current,timedelta(hours=12)) or _fresh(diagnostics,timedelta(hours=3)):
            continue
        last=min((aware(s.updated_at) for s in (current,diagnostics) if s),
                 default=datetime(2000,1,1,tzinfo=timezone.utc))
        options.append((last,list(LEAGUES).index(slug),slug))
    result={"attempted":[],"updated":[],"unavailable":[]}
    for _,_,slug in sorted(options)[:max_leagues]:
        ref=f"{slug}:{year}"
        result["attempted"].append(slug)
        try:
            events=fetch(slug,year)
            if events:
                _write("thesportsdb_games",ref,events,len(events),
                       "TheSportsDB free; fixture coverage is limited")
                result["updated"].append(slug)
            else:
                result["unavailable"].append(slug)
        except (ValueError,TypeError,KeyError,OSError):
            result["unavailable"].append(slug)
        _write("tsdb_diagnostic",ref,[{"attempted":True}],1)
    return result
