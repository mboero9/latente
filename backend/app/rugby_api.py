"""API-Rugby ingestion and PostgreSQL read model for Latente.

Each slug resolves against the provider's actual league catalogue. No
fabricated league IDs, fixtures, standings or bonus-point calculations.
All API calls run in the cron worker, never on page views.
"""
import os
import re
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from .db import session_scope
from .models import SportSnapshot, utcnow
from .ingest import upsert
from .sports_sources import extract, SourceUnavailable
from .sports_scheduler import reserve_quota
from .provider import aware

log = logging.getLogger("latente.rugby")

# Names are used ONLY to resolve verified IDs from GET /leagues.
# URBA is called Top 12 in API-Rugby's published catalogue.
COMPETITIONS = (
    ("urba", "URBA · Top 12 (Argentina)", ("top 12", "top12", "top 14"), ("argentina",)),
    ("championship", "Rugby Championship · Los Pumas", ("rugby championship",), ("world",)),
    ("six-nations", "Seis Naciones", ("six nations",), ("europe",)),
    ("super-rugby", "Super Rugby", ("super rugby",), ("world",)),
    ("premiership", "Premiership Rugby", ("premiership rugby",), ("england",)),
    ("top-14", "Top 14 · Francia", ("top 14",), ("france",)),
    ("urc", "United Rugby Championship", ("united rugby championship",), ("world",)),
    ("champions", "European Rugby Champions Cup", ("european rugby champions cup",), ("europe",)),
    ("test-matches", "Amistosos internacionales", ("friendly international",), ("world",)),
    ("world-cup", "Mundial de Rugby", ("world cup",), ("world",)),
)
BY_SLUG = {slug: (title, names, countries) for slug, title, names, countries in COMPETITIONS}
CATALOG_TTL = timedelta(days=1)
GAMES_TTL = timedelta(hours=8)
STANDINGS_TTL = timedelta(hours=12)
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
                        "team_id": team.get("id"),
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
        return db.get(SportSnapshot, ("rugby", kind, ref))


def _write(kind, ref, rows, count, note=""):
    now = utcnow()
    with session_scope() as db:
        existing = db.get(SportSnapshot, ("rugby", kind, ref))
        if existing and existing.source_count > 0 and not rows:
            return False
        upsert(db, SportSnapshot, {
            "sport": "rugby", "dataset": kind, "ref": ref,
            "provider": "api_rugby", "data": rows, "source_count": count,
            "updated_at": now, "note": note[:250],
        })
    return True


def catalog():
    obj = _snapshot("leagues", "catalog")
    return obj.data if obj else []


def public_catalog():
    rows = catalog()
    by_slug = {r["slug"]: r for r in rows}
    return [{"slug": slug, "name": title,
             **{k: v for k, v in by_slug.get(slug, {}).items() if k != "slug"}}
            for slug, title, _, _ in COMPETITIONS]


def read_competition(slug, season=None):
    if slug not in BY_SLUG:
        raise ValueError("unknown competition")
    row = next((c for c in public_catalog() if c["slug"] == slug), {})
    title = BY_SLUG[slug][0]
    league_id = row.get("league_id")
    available = row.get("seasons") or []
    year = int(season) if season else (available[0] if available else datetime.now(timezone.utc).year)
    if year < 2000 or year > datetime.now(timezone.utc).year + 1:
        raise ValueError("year out of range")
    if not league_id:
        return {"available": False, "provider": "API-Rugby",
                "configured": key_configured(), "season": year, "seasons": available,
                "league_name": title, "games": [], "official": [],
                "message": "Catálogo de API-Rugby pendiente, torneo no identificado o no disponible en el plan."}
    ref = f"{league_id}:{year}"
    games = _snapshot("games", ref)
    table = _snapshot("standings", ref)
    return {
        "available": bool((games and games.data) or (table and table.data)),
        "configured": key_configured(), "provider": "API-Rugby",
        "league_name": title, "season": year, "seasons": available,
        "games": games.data if games else [],
        "official": table.data if table else [],
        "updated_at": max((aware(s.updated_at) for s in (games, table) if s), default=None),
        "message": None if (games or table) else "Sin datos sincronizados de API-Rugby para esta temporada. Se importan por cron.",
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
            if cleaned:
                _write(kind, ref, cleaned, len(rows), note)
                result["updated"].append(f"{kind}:{ref}")
            else:
                _write("diagnostic", error_ref, [{"message": "Sin cobertura o resultados"}], 1)
        except (SourceUnavailable, ValueError, TypeError, KeyError):
            _write("diagnostic", error_ref, [{"message": "Proveedor no disponible o plan sin cobertura"}], 1)
            result["unavailable"].append(f"{kind}:{ref}")

    call("leagues", "catalog", "leagues", {}, resolve, CATALOG_TTL,
         "Identificadores confirmados por API-Rugby; cobertura sujeta al plan.")
    if not catalog():
        return result
    now_year = datetime.now(timezone.utc).year
    # Prioritize each competition's latest available season, then games and tables.
    for comp in catalog():
        league = comp.get("league_id")
        seasons = comp.get("seasons") or []
        year = next((y for y in seasons if y <= now_year), None)
        if not league or year is None:
            continue
        ref = f"{league}:{year}"
        params = {"league": league, "season": year}
        call("games", ref, "games", params, normalize_games, GAMES_TTL, comp["name"])
        call("standings", ref, "standings", params, normalize_standings, STANDINGS_TTL, comp["name"])
        if len(result["attempted"]) >= max_calls:
            break
    return result
