"""Railway cron ingests snapshots once; never per website visit.

The persisted quota is independent per sport. Empty or rejected source
responses never wipe older snapshots. Standings targets require verified
league IDs and season numbers in SPORTS_TARGETS_JSON.
"""
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select
from .db import session_scope
from .models import SportSnapshot, SportQuota, utcnow
from .ingest import upsert
from .provider import aware
from .other_sports import SPORTS
from .sports_sources import extract, normalize_games, normalize_standings, SourceUnavailable

logger = logging.getLogger("latente.multisport")
DONE_TTL = {"games": timedelta(hours=6), "leagues": timedelta(days=1), "standings": timedelta(days=1),
            "drivers": timedelta(days=1), "constructors": timedelta(days=1)}



# IDs MUST come from the provider /leagues catalogue. Never hardcode
# unrelated league IDs from other sports.
AUTO_LEAGUES = {
    "nhl": ("nhl",),
    "mlb": ("mlb",),
    "nfl": ("nfl",),
    "basketball": ("euroleague", "liga acb", "liga nacional"),
    "handball": ("bundesliga", "champions league", "liga asobal"),
    "volleyball": ("superlega", "plusliga", "champions league"),
}
COUNTRY_PREFERENCE = {
    "nhl": ("usa", "world"), "mlb": ("usa", "world"),
    "nfl": ("usa", "world"), "basketball": ("world", "europe", "argentina", "spain"),
    "handball": ("germany", "europe", "spain", "world"),
    "volleyball": ("italy", "poland", "europe", "world"),
}


def automatic_targets(sport, catalogue, year):
    """Return up to 2 verified active league-season pairs per supported sport."""
    goals = AUTO_LEAGUES.get(sport, ())
    pref = COUNTRY_PREFERENCE.get(sport, ())
    options = []
    for row in catalogue:
        if not isinstance(row, dict) or not isinstance(row.get("id"), int):
            continue
        title = str(row.get("name") or "").casefold().strip()
        country = str(row.get("country") or "").casefold().strip()
        if title not in goals:
            continue
        years = []
        for entry in row.get("seasons") or []:
            raw = entry.get("season", entry.get("year")) if isinstance(entry, dict) else entry
            try:
                parsed = int(raw)
                if 2000 <= parsed <= year + 1:
                    years.append(parsed)
            except (TypeError, ValueError):
                continue
        current = max((v for v in years if v <= year), default=None)
        if current is None:
            continue
        score = (goals.index(title), pref.index(country) if country in pref else len(pref))
        options.append((score, {"league": row["id"], "season": current, "country": row.get("country") or ""}))
    options.sort(key=lambda x: (x[0], x[1]["league"]))
    out = []
    seen = set()
    for _, candidate in options:
        if candidate["league"] in seen:
            continue
        seen.add(candidate["league"])
        out.append(candidate)
        if len(out) == (1 if sport in {"nhl", "mlb", "nfl"} else 2):
            break
    return out

def configured_targets():
    try:
        data = json.loads(os.getenv("SPORTS_TARGETS_JSON", "{}"))
    except ValueError:
        logger.warning("sports_targets_invalid_json")
        return {}
    if not isinstance(data, dict):
        return {}
    allowed = {}
    for sport, rows in data.items():
        if sport not in SPORTS or not isinstance(rows, list):
            continue
        clean = []
        for item in rows[:20]:
            if not isinstance(item, dict):
                continue
            try:
                league = "standard" if sport == "nba" else ("drivers" if sport == "f1" else int(item["league"]))
                season = int(item["season"])
            except (ValueError, KeyError, TypeError):
                continue
            if 2000 <= season <= utcnow().year + 1 and (league in ("standard", "drivers") or league > 0):
                clean.append({"league": league, "season": season,
                              "country": str(item.get("country") or "")[:40]})
        allowed[sport] = clean
    return allowed


def due_jobs(today=None):
    today = today or datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    enabled = [s.strip() for s in os.getenv(
        "SPORTS_AUTOSYNC", "nhl,mlb,nba,basketball,f1,nfl,handball,volleyball"
    ).split(",") if s.strip() in SPORTS and s.strip() != "rugby"]
    # Always include the two newly requested disciplines, even if Railway
    # still has an older SPORTS_AUTOSYNC value without them.
    enabled = list(dict.fromkeys([*enabled, "handball", "volleyball"]))
    jobs = []
    targets = configured_targets()
    # Supplement explicit targets from catalogue snapshots discovered by the
    # cron; don't guess league IDs or the start year for seasonal standings.
    with session_scope() as db:
        for sport in enabled:
            if targets.get(sport) or sport not in AUTO_LEAGUES:
                continue
            snap = db.get(SportSnapshot, (sport, "leagues", "catalog"))
            if snap and snap.data:
                targets[sport] = automatic_targets(sport, snap.data, today.year)
    # Estas ligas tienen identificadores oficiales estables. Si el usuario no
    # definió SPORTS_TARGETS_JSON, probar sus posiciones actuales una vez/día.
    # Los errores de cobertura se preservan como no disponibles.
    year = today.year
    if "nba" in enabled and not targets.get("nba"):
        targets["nba"] = [{"league": "standard", "season": year, "country": "USA"}]
    if "nfl" in enabled and not targets.get("nfl"):
        targets["nfl"] = [{"league": 1, "season": year, "country": "USA"}]
    if "f1" in enabled and not targets.get("f1"):
        targets["f1"] = [{"league": "drivers", "season": year, "country": "World"}]
    for sport in enabled:
        # Una consulta de catálogo diaria como máximo: las competiciones
        # argentinas (UAR/URBA) se identifican por sus IDs reales.
        if sport in AUTO_LEAGUES:
            jobs.append((sport, "leagues", "catalog", {}))
        # Una ventana de cobertura real, no solo ayer/hoy.
        # Dentro de 20 solicitudes diarias por deporte, recorrer jornadas
        # pasadas y futuras que el plan gratuito realmente permita consultar.
        # Para F1, /races?season=AAAA devuelve el calendario anual: basta un
        # único snapshot por temporada, no 15 consultas idénticas.
        offsets = (0,) if sport == "f1" else (0, -1, 1, -2, 2)
        for offset in offsets:
            target = today + timedelta(days=offset)
            jobs.append((sport, "games", target.isoformat(), target))
        for config in targets.get(sport, []):
            ref = f"{config['league']}:{config['season']}"
            kind = "drivers" if sport == "f1" else "standings"
            jobs.append((sport, kind, ref, config))
            if sport == "f1":
                jobs.append((sport, "constructors", f"teams:{config['season']}", config))
    return jobs


def reserve_quota(sport, cap=20):
    today = utcnow().date()
    with session_scope() as db:
        # Avoid using a mutable process-only counter: this lock works across cron runs.
        upsert_no_replace(db, sport, today)
        quota = db.scalar(select(SportQuota).where(
            SportQuota.sport == sport, SportQuota.day == today,
        ).with_for_update())
        if quota.requests >= cap:
            return False
        quota.requests += 1
    return True


def upsert_no_replace(db, sport, day):
    if db.bind.dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        from sqlalchemy.dialects.postgresql import insert
    db.execute(insert(SportQuota).values(sport=sport, day=day, requests=0)
               .on_conflict_do_nothing(index_elements=["sport", "day"]))


def persist_snapshot(sport, kind, ref, normalized, count, country=""):
    now = utcnow()
    with session_scope() as db:
        previous = db.get(SportSnapshot, (sport, kind, ref))
        if previous and previous.source_count > 0 and not normalized:
            # A transient empty response must not erase a verified nonempty one.
            return False
        upsert(db, SportSnapshot, {
            "sport": sport, "dataset": kind, "ref": ref, "provider": "api_sports",
            "data": normalized, "source_count": count, "updated_at": now,
            "note": ("País: " + country + ". " if country else "") + "Cobertura según competición y temporada.",
        })
    return True


def sync_once(max_calls=3, fetch=extract):
    """Bounded, idempotent, no retry storm. Returns structured audit summary."""
    now = utcnow()
    candidates = []
    with session_scope() as db:
        for sport, kind, ref, config in due_jobs():
            previous = db.get(SportSnapshot, (sport, kind, ref))
            offseason = {v.strip() for v in os.getenv("SPORTS_OFFSEASON", "").split(",")}
            period = timedelta(days=7) if sport in offseason else (
                timedelta(days=1) if kind == "games" and ref != now.astimezone(
                    ZoneInfo("America/Argentina/Buenos_Aires")).date().isoformat()
                else DONE_TTL[kind]
            )
            if previous and aware(previous.updated_at) + period > now:
                continue
            candidates.append((sport, kind, ref, config))
    # Repartir equitativamente los turnos entre deportes de 100 requests/día.
    # Sin esto, los primeros 3 deportes monopolizan todos los cron.
    with session_scope() as db:
        used = {q.sport: q.requests for q in db.scalars(
            select(SportQuota).where(SportQuota.day == utcnow().date())
        )}
    # Los campeonatos con partidos programados en días aislados necesitan
    # varios días. Mantener prioridad de deporte con menor consumo y día más
    # cercano, sin superar la cuota de 20 consultas por disciplina.
    candidates.sort(key=lambda item: (
        used.get(item[0], 0),
        0 if item[1] == "leagues" else 1,
        abs((item[3] - now.astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date()).days)
            if item[1] == "games" else 99,
    ))
    report = {"updated": [], "unavailable": [], "attempts": 0}
    for sport, kind, ref, config in candidates:
        if report["attempts"] >= max_calls:
            break
        if not (os.getenv(SPORTS[sport][0]) or os.getenv("API_FOOTBALL_KEY")):
            report["unavailable"].append({"sport": sport, "reason": "not configured"})
            continue
        if not reserve_quota(sport):
            continue
        report["attempts"] += 1
        endpoint = "races" if sport == "f1" and kind == "games" else (
            "rankings/drivers" if kind == "drivers" else (
                "rankings/teams" if kind == "constructors" else kind))
        if kind == "leagues":
            params = {}
        elif kind == "games":
            params = ({"season": config.year} if sport == "f1"
                      else {"date": ref})
            if sport == "nba":
                params.update({"league": "standard", "season": config.year})
        else:
            params = {"season": config["season"]}
            if kind == "standings":
                params["league"] = config["league"]
        try:
            rows = fetch(sport, endpoint, params)
            if kind == "games":
                normalized = normalize_games(sport, rows)
            elif kind == "leagues":
                normalized = [
                    {"id": row["id"], "name": row.get("name") or "",
                     "country": ((row.get("country") or {}).get("name") if isinstance(row.get("country"), dict) else row.get("country")) or "",
                     "type": row.get("type") or "",
                     "seasons": row.get("seasons") or []}
                    for row in rows if isinstance(row, dict) and isinstance(row.get("id"), int)
                ]
            elif kind == "standings":
                normalized = normalize_standings(rows, sport=sport)
            else:
                normalized = rows[:200]  # F1 pilotos/constructores, registros originales
            stored = persist_snapshot(sport, kind, ref, normalized, len(rows),
                                      config.get("country", "") if isinstance(config, dict) else "")
            if stored:
                report["updated"].append({"sport": sport, "kind": kind,
                                          "ref": ref, "rows": len(normalized)})
        except (SourceUnavailable, ValueError, TypeError):
            # Preserve last good snapshot; errors must not erase prior data.
            report["unavailable"].append({"sport": sport, "kind": kind,
                                          "reason": "provider unavailable or uncovered"})
    return report
