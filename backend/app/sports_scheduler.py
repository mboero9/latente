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
DONE_TTL = {"games": timedelta(hours=6), "standings": timedelta(days=1),
            "drivers": timedelta(days=1)}


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
                league = int(item["league"]) if sport != "nba" else "standard"
                season = int(item["season"])
            except (ValueError, KeyError, TypeError):
                continue
            if 2000 <= season <= utcnow().year + 1 and (league == "standard" or league > 0):
                clean.append({"league": league, "season": season,
                              "country": str(item.get("country") or "")[:40]})
        allowed[sport] = clean
    return allowed


def due_jobs(today=None):
    today = today or datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    enabled = [s.strip() for s in os.getenv(
        "SPORTS_AUTOSYNC", "nhl,mlb,nba,basketball,f1,nfl,afl,rugby"
    ).split(",") if s.strip() in SPORTS]
    jobs = []
    targets = configured_targets()
    for sport in enabled:
        # One date per sport and request. Archives remain unchanged.
        jobs.append((sport, "games", today.isoformat(), today))
        jobs.append((sport, "games", (today - timedelta(days=1)).isoformat(),
                     today - timedelta(days=1)))
        for config in targets.get(sport, []):
            ref = f"{config['league']}:{config['season']}"
            kind = "drivers" if sport == "f1" else "standings"
            jobs.append((sport, kind, ref, config))
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


def persist_snapshot(sport, kind, ref, normalized, count):
    now = utcnow()
    with session_scope() as db:
        upsert(db, SportSnapshot, {
            "sport": sport, "dataset": kind, "ref": ref, "provider": "api_sports",
            "data": normalized, "source_count": count, "updated_at": now,
            "note": "Dato del proveedor. Cobertura sujeta a competición/temporada.",
        })


def sync_once(max_calls=3, fetch=extract):
    """Bounded, idempotent, no retry storm. Returns structured audit summary."""
    now = utcnow()
    candidates = []
    with session_scope() as db:
        for sport, kind, ref, config in due_jobs():
            previous = db.get(SportSnapshot, (sport, kind, ref))
            if previous and aware(previous.updated_at) + DONE_TTL[kind] > now:
                continue
            candidates.append((sport, kind, ref, config))
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
            "rankings/drivers" if kind == "drivers" else kind)
        if kind == "games":
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
            elif kind == "standings":
                normalized = normalize_standings(rows)
            else:
                normalized = rows[:200]  # F1 driver ranking, source-record format
            persist_snapshot(sport, kind, ref, normalized, len(rows))
            report["updated"].append({"sport": sport, "kind": kind,
                                      "ref": ref, "rows": len(normalized)})
        except (SourceUnavailable, ValueError, TypeError):
            # Preserve last good snapshot; errors must not erase prior data.
            report["unavailable"].append({"sport": sport, "kind": kind,
                                          "reason": "provider unavailable or uncovered"})
    return report
